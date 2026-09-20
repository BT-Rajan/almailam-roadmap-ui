export interface PermitCatalogItem {
  id: string
  name: string
  fixedCost: number
  // Application setup: the authority and form this permit type's
  // applications use. Both null until an administrator configures it
  // (Administration > Permit Catalog). requiredDocuments is only the
  // override -- null means the form's own checklist applies.
  authorityId: string | null
  formId: string | null
  requiredDocuments: string[] | null
}

export interface PermitApplicationSetupInput {
  authorityId: string | null
  formId: string | null
  requiredDocuments: string[] | null
}

// An admin-configured "this Design activity must be Complete before
// the permit is eligible" rule -- see project_service.
// _recompute_permit_eligibility.
export interface PermitPrerequisite {
  id: string
  designActivityId: string
  designActivityName: string
  serviceName: string
}
