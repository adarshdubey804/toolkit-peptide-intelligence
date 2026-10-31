-- Attribute certification submissions so facility-scoped claims can be independently reviewed.
ALTER TABLE vendor_certifications
    ADD COLUMN IF NOT EXISTS submitted_by UUID REFERENCES user_profiles(id);

CREATE INDEX IF NOT EXISTS idx_vendor_certifications_submitter
    ON vendor_certifications(submitted_by, verification_status);
