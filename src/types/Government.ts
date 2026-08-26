export type AuthorityCategory = 'Municipality' | 'Fire Department' | 'Electricity' | 'Water' | 'Environment' | 'Internal'

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
  | 'Agreement'
  | 'Legal Undertaking'

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
  // The fillable body of the form/undertaking, written with {{token}}
  // merge fields (see governmentFormHelpers.renderGovernmentFormTemplate).
  // Empty for forms that are only a scanned/attached sample (previewUrl).
  template?: string
  // Service Catalog service names this form applies to -- matched against
  // Project.service (a comma-joined summary of the project's picked
  // services) to decide which forms to surface under a project's
  // Documents > Government section.
  serviceTags: string[]
}
