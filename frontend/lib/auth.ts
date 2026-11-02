export const ACTIVE_ORGANIZATION_STORAGE_KEY = "toolkit.activeOrganizationId";

export function getPreferredOrganizationId(): string | undefined {
  if (typeof window === "undefined") return undefined;
  return window.localStorage.getItem(ACTIVE_ORGANIZATION_STORAGE_KEY) || undefined;
}

export function setPreferredOrganizationId(organizationId: string | null | undefined): void {
  if (typeof window === "undefined") return;
  if (organizationId) {
    window.localStorage.setItem(ACTIVE_ORGANIZATION_STORAGE_KEY, organizationId);
  } else {
    window.localStorage.removeItem(ACTIVE_ORGANIZATION_STORAGE_KEY);
  }
}
