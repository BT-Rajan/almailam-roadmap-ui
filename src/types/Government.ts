export type AuthorityCategory = 'Municipality' | 'Fire Department' | 'Electricity' | 'Water' | 'Environment'

export interface GovernmentAuthority {
  id: string
  name: string
  category: AuthorityCategory
  website: string
  description: string
}

export type GovernmentFormCategory =
  | 'Building Permit'
  | 'Occupancy Certificate'
  | 'Fire Safety Approval'
  | 'Utility Connection'
  | 'Environmental Clearance'
  | 'Business License'

export type GovernmentFormLanguage = 'English' | 'Arabic' | 'English / Arabic'

export type GovernmentFormViewMode = 'grid' | 'table'

export type GovernmentFormStatus = 'Active' | 'Archived'

export interface GovernmentForm {
  id: string
  authorityId: string
  formCode: string
  title: string
  version: string
  language: GovernmentFormLanguage
  category: GovernmentFormCategory
  description: string
  requiredDocuments: string[]
  lastUpdated: string
  previewUrl?: string
  status: GovernmentFormStatus
}
