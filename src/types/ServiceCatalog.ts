export interface ServiceCatalogActivity {
  id: string
  name: string
  fixedCost: number
}

export interface ServiceCatalogItem {
  id: string
  name: string
  activities: ServiceCatalogActivity[]
}

// A single leaf pick made in ServicePickerDialog -- one activity, under one
// service, with the price it was selected at. Kept flat (rather than
// nested service -> activities) because every consumer (line items, quote
// prefill, contract scope) wants to iterate picks, not re-walk a tree.
export interface SelectedServiceActivity {
  serviceId: string
  serviceName: string
  activityId: string
  activityName: string
  fixedCost: number
}
