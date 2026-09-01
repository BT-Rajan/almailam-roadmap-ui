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
export interface SelectedServiceActivity {
  serviceId: string
  serviceName: string
  activityId: string
  activityName: string
  fixedCost: number
}
