export type ServiceCatalogBranch = 'Design' | 'Supervision'

export interface ServiceCatalogActivity {
  id: string
  name: string
  fixedCost: number
}

// branch determines billing behavior (see backend migration 0059): Design
// services are one-time fees; the single Supervision service's activities
// are monthly recurring fees, day-prorated for partial calendar months.
export interface ServiceCatalogItem {
  id: string
  name: string
  branch: ServiceCatalogBranch
  activities: ServiceCatalogActivity[]
}

// A single leaf pick made in ServicePickerDialog -- one activity, under one
// service, with the price it was selected at. Kept flat (rather than
// nested service -> activities) because every consumer (line items, quote
// prefill, contract scope) wants to iterate picks, not re-walk a tree.
// Design branch only -- see SelectedSupervisionActivity (Project.ts) for
// the Supervision equivalent, which also carries its own start/end dates.
export type SelectedActivityStatus = 'Not Started' | 'In Progress' | 'Complete' | 'Cancelled'

export interface SelectedServiceActivity {
  serviceId: string
  serviceName: string
  activityId: string
  activityName: string
  fixedCost: number
  // Present once this pick has actually been persisted to a project
  // (ProjectOut.selectedActivities) -- absent while it's still just a
  // fresh selection in ServicePickerDialog before the project is
  // created. id is this row's own identity (not activityId, the
  // catalog's display id) -- what Task.selectedActivityId and the
  // close/reopen actions operate on.
  id?: string
  status?: SelectedActivityStatus
  closedAt?: string
}

// An admin-configured "this Design activity must be Complete before
// this Supervision activity is eligible" rule -- see
// project_service._recompute_supervision_eligibility. Same shape as
// PermitPrerequisite (types/PermitCatalog.ts).
export interface SupervisionPrerequisite {
  id: string
  designActivityId: string
  designActivityName: string
  serviceName: string
}
