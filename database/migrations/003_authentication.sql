-- Authentication and organization membership foundation.
ALTER TABLE user_profiles
    ADD COLUMN IF NOT EXISTS email TEXT,
    ADD COLUMN IF NOT EXISTS password_hash TEXT,
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_profiles_email_lower
    ON user_profiles (lower(email))
    WHERE email IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_user_profiles_org_role
    ON user_profiles (organization_id, role);

COMMENT ON COLUMN user_profiles.password_hash IS
    'Argon2id password hash only; never store plaintext passwords or provider secrets.';
