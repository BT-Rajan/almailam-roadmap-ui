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

export type GovernmentFormFieldType = 'text' | 'select' | 'radio'

// Describes one {{token}} in a form's template as a dropdown or radio
// group instead of the plain text box it'd default to -- see
// ProjectFormEntryDialog.vue. `options` only matters for 'select'/
// 'radio'.
export interface GovernmentFormField {
  token: string
  label: string
  type: GovernmentFormFieldType
  options: string[]
}

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
  // Which template tokens are dropdowns/radio groups instead of plain
  // text -- a token used in the template but not listed here just
  // falls back to a plain text field.
  fields: GovernmentFormField[]
  // The uploaded reference copy of the real government form (e.g. the
  // blank official PDF), if any -- just its filename; the file itself
  // is fetched via governmentFormService.downloadSampleFile.
  sampleFileName: string | null
}

// One government form, filled in and saved for one project --
// Approvals & Permits' own record, organized by the form's authority
// there. See ProjectFormEntryDialog.vue for how it's created/edited.
export type ProjectFormEntryStatus =
  | 'Draft'
  | 'Submitted'
  | 'Under Review'
  | 'Comments Received'
  | 'Approved'
  | 'Rejected'
  | 'Withdrawn'

export interface ProjectFormEntry {
  id: string
  formId: string
  formCode: string
  formTitle: string
  authorityId: string
  authorityName: string
  fieldValues: Record<string, string>
  status: ProjectFormEntryStatus
  // The generated PDF's document id -- always set once this entry
  // exists; Download/Print/View are only ever offered because of that.
  documentId: string | null
  createdAt: string
  createdBy: string | null
}
