-- Organization membership and role-based workspace access.
CREATE TABLE IF NOT EXISTS organization_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'researcher'
        CHECK (role IN ('organization_admin','curator','reviewer','researcher','viewer')),
    membership_status TEXT NOT NULL DEFAULT 'active'
        CHECK (membership_status IN ('active','suspended')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organization_id, user_id)
);

INSERT INTO organization_memberships (organization_id, user_id, role)
SELECT organization_id, id,
       CASE WHEN role IN ('organization_admin','curator','reviewer','researcher','viewer')
            THEN role ELSE 'researcher' END
FROM user_profiles
WHERE organization_id IS NOT NULL
ON CONFLICT (organization_id, user_id) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_org_memberships_user_status
    ON organization_memberships (user_id, membership_status);
CREATE INDEX IF NOT EXISTS idx_org_memberships_org_role
    ON organization_memberships (organization_id, role, membership_status);

CREATE TABLE IF NOT EXISTS research_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    visibility TEXT NOT NULL DEFAULT 'organization'
        CHECK (visibility IN ('organization','private')),
    created_by UUID NOT NULL REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS project_memberships (
    project_id UUID NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    project_role TEXT NOT NULL DEFAULT 'contributor'
        CHECK (project_role IN ('owner','editor','contributor','viewer')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (project_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_research_projects_org
    ON research_projects (organization_id, updated_at DESC);

COMMENT ON TABLE organization_memberships IS
    'Tenant membership and authorization source of truth. User profile organization_id is legacy compatibility only.';
COMMENT ON TABLE research_projects IS
    'Organization-scoped research workspaces; access is enforced by the API.';
