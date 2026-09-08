export interface PermitCatalogItem {
  id: string
  name: string
  fixedCost: number
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
