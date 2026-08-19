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
