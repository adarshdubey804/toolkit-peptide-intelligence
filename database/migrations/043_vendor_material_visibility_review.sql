-- Allow an independent reviewer to assign the offering's publication scope.
-- Scientific evidence fields remain immutable; visibility is a controlled moderation field.
CREATE OR REPLACE FUNCTION prevent_batch_evidence_mutation()
RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION '% is retained as provenance; create a superseding or corrective record instead', TG_TABLE_NAME;
    END IF;
    IF (to_jsonb(NEW) - ARRAY['review_status','reviewed_by','reviewed_at','visibility_scope'])
       IS DISTINCT FROM
       (to_jsonb(OLD) - ARRAY['review_status','reviewed_by','reviewed_at','visibility_scope']) THEN
        RAISE EXCEPTION '% evidence fields are immutable; create a superseding record instead', TG_TABLE_NAME;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
