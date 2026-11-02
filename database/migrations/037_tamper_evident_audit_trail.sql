-- Extend the existing organization-scoped audit_events table with a serialized SHA-256 chain.
-- pgcrypto is used for SHA-256; privileged database operators remain outside the threat
-- model unless hashes are periodically anchored outside this database.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER TABLE audit_events
    ADD COLUMN IF NOT EXISTS chain_scope TEXT,
    ADD COLUMN IF NOT EXISTS chain_sequence BIGINT,
    ADD COLUMN IF NOT EXISTS previous_hash TEXT,
    ADD COLUMN IF NOT EXISTS event_hash TEXT;

CREATE TABLE IF NOT EXISTS audit_chain_heads (
    chain_scope TEXT PRIMARY KEY,
    last_sequence BIGINT NOT NULL DEFAULT 0 CHECK (last_sequence >= 0),
    last_hash TEXT NOT NULL CHECK (length(last_hash) = 64),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE OR REPLACE FUNCTION audit_event_sha256(
    p_id UUID,
    p_actor_user_id UUID,
    p_organization_id UUID,
    p_action TEXT,
    p_entity_type TEXT,
    p_entity_id UUID,
    p_event_metadata JSONB,
    p_occurred_at TIMESTAMPTZ,
    p_chain_scope TEXT,
    p_chain_sequence BIGINT,
    p_previous_hash TEXT
) RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
AS $$
    SELECT encode(
        digest(
            convert_to(
                jsonb_build_object(
                    'id', p_id,
                    'actor_user_id', p_actor_user_id,
                    'organization_id', p_organization_id,
                    'action', p_action,
                    'entity_type', p_entity_type,
                    'entity_id', p_entity_id,
                    'event_metadata', COALESCE(p_event_metadata, '{}'::jsonb),
                    'occurred_at', to_char(p_occurred_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
                    'chain_scope', p_chain_scope,
                    'chain_sequence', p_chain_sequence,
                    'previous_hash', p_previous_hash
                )::text,
                'UTF8'
            ),
            'sha256'
        ),
        'hex'
    )
$$;

-- Backfill the pre-existing audit history deterministically before installing the
-- append-only trigger. Historical events are therefore part of the verifiable chain.
DO $$
DECLARE
    v_scope TEXT;
    v_previous_hash TEXT;
    v_sequence BIGINT;
    v_event RECORD;
    v_hash TEXT;
BEGIN
    FOR v_scope IN
        SELECT DISTINCT COALESCE(organization_id::TEXT, 'global')
        FROM audit_events
        ORDER BY 1
    LOOP
        v_previous_hash := repeat('0', 64);
        v_sequence := 0;

        FOR v_event IN
            SELECT id, actor_user_id, organization_id, action, entity_type,
                   entity_id, event_metadata, occurred_at
            FROM audit_events
            WHERE COALESCE(organization_id::TEXT, 'global') = v_scope
            ORDER BY occurred_at, id
        LOOP
            v_sequence := v_sequence + 1;
            v_hash := audit_event_sha256(
                v_event.id, v_event.actor_user_id, v_event.organization_id,
                v_event.action, v_event.entity_type, v_event.entity_id,
                v_event.event_metadata, v_event.occurred_at, v_scope,
                v_sequence, v_previous_hash
            );

            UPDATE audit_events
            SET chain_scope = v_scope,
                chain_sequence = v_sequence,
                previous_hash = v_previous_hash,
                event_hash = v_hash
            WHERE id = v_event.id;

            v_previous_hash := v_hash;
        END LOOP;

        INSERT INTO audit_chain_heads (chain_scope, last_sequence, last_hash)
        VALUES (v_scope, v_sequence, v_previous_hash)
        ON CONFLICT (chain_scope) DO UPDATE
        SET last_sequence = EXCLUDED.last_sequence,
            last_hash = EXCLUDED.last_hash,
            updated_at = clock_timestamp();
    END LOOP;
END
$$;

ALTER TABLE audit_events
    ALTER COLUMN chain_scope SET NOT NULL,
    ALTER COLUMN chain_sequence SET NOT NULL,
    ALTER COLUMN previous_hash SET NOT NULL,
    ALTER COLUMN event_hash SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_audit_events_chain_position
    ON audit_events (chain_scope, chain_sequence);
CREATE INDEX IF NOT EXISTS idx_audit_events_org_chain
    ON audit_events (organization_id, chain_sequence DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_org_action
    ON audit_events (organization_id, action, chain_sequence DESC);

CREATE OR REPLACE FUNCTION append_audit_event_to_chain()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_sequence BIGINT;
    v_previous_hash TEXT;
BEGIN
    NEW.chain_scope := COALESCE(NEW.organization_id::TEXT, 'global');

    -- Serialize writers per organization so concurrent requests cannot fork a chain.
    PERFORM pg_advisory_xact_lock(hashtextextended(NEW.chain_scope, 731904221067));

    INSERT INTO audit_chain_heads (chain_scope, last_sequence, last_hash)
    VALUES (NEW.chain_scope, 0, repeat('0', 64))
    ON CONFLICT (chain_scope) DO NOTHING;

    SELECT last_sequence, last_hash
    INTO v_sequence, v_previous_hash
    FROM audit_chain_heads
    WHERE chain_scope = NEW.chain_scope
    FOR UPDATE;

    NEW.chain_sequence := v_sequence + 1;
    NEW.previous_hash := v_previous_hash;
    NEW.event_hash := audit_event_sha256(
        NEW.id, NEW.actor_user_id, NEW.organization_id, NEW.action,
        NEW.entity_type, NEW.entity_id, NEW.event_metadata, NEW.occurred_at,
        NEW.chain_scope, NEW.chain_sequence, NEW.previous_hash
    );

    UPDATE audit_chain_heads
    SET last_sequence = NEW.chain_sequence,
        last_hash = NEW.event_hash,
        updated_at = clock_timestamp()
    WHERE chain_scope = NEW.chain_scope;

    RETURN NEW;
END
$$;

CREATE TRIGGER trg_audit_events_chain_insert
BEFORE INSERT ON audit_events
FOR EACH ROW
EXECUTE FUNCTION append_audit_event_to_chain();

CREATE OR REPLACE FUNCTION prevent_audit_event_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'audit_events is append-only; UPDATE and DELETE are prohibited';
END
$$;

CREATE TRIGGER trg_audit_events_immutable
BEFORE UPDATE OR DELETE ON audit_events
FOR EACH ROW
EXECUTE FUNCTION prevent_audit_event_mutation();
