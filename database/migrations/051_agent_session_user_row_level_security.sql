-- Make AI agent sessions private to both the authenticated user and their organization.
ALTER TABLE agent_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_sessions FORCE ROW LEVEL SECURITY;
CREATE POLICY agent_sessions_select_scope ON agent_sessions FOR SELECT
USING (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
);
CREATE POLICY agent_sessions_insert_scope ON agent_sessions FOR INSERT
WITH CHECK (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
);
CREATE POLICY agent_sessions_update_scope ON agent_sessions FOR UPDATE
USING (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
)
WITH CHECK (
    organization_id = NULLIF(current_setting('app.organization_id', true), '')::uuid
    AND user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
);

ALTER TABLE agent_session_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_session_messages FORCE ROW LEVEL SECURITY;
CREATE POLICY agent_session_messages_select_scope ON agent_session_messages FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM agent_sessions session
        WHERE session.id=agent_session_messages.session_id
          AND session.organization_id=NULLIF(current_setting('app.organization_id', true), '')::uuid
          AND session.user_id=NULLIF(current_setting('app.user_id', true), '')::uuid
    )
);
CREATE POLICY agent_session_messages_insert_scope ON agent_session_messages FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM agent_sessions session
        WHERE session.id=agent_session_messages.session_id
          AND session.organization_id=NULLIF(current_setting('app.organization_id', true), '')::uuid
          AND session.user_id=NULLIF(current_setting('app.user_id', true), '')::uuid
    )
);

CREATE OR REPLACE FUNCTION prevent_agent_session_message_mutation()
RETURNS trigger AS $agent_session_message_immutable$
BEGIN
    RAISE EXCEPTION 'Agent session messages are append-only; create a new message instead';
END;
$agent_session_message_immutable$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS agent_session_messages_append_only ON agent_session_messages;
CREATE TRIGGER agent_session_messages_append_only
    BEFORE UPDATE OR DELETE ON agent_session_messages
    FOR EACH ROW EXECUTE FUNCTION prevent_agent_session_message_mutation();

COMMENT ON POLICY agent_sessions_select_scope ON agent_sessions IS
    'Agent sessions are private to the authenticated user inside their active organization.';
COMMENT ON POLICY agent_session_messages_select_scope ON agent_session_messages IS
    'Message history inherits both organization and user scope from its parent session.';
