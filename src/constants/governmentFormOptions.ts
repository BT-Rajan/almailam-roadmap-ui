import type { SelectOption } from '@/types/Ui'

export const AUTHORITY_CATEGORY_OPTIONS: SelectOption[] = [
  { label: 'Municipality', value: 'Municipality', labelKey: 'governmentFormOptions.authorityCategory.municipality' },
  { label: 'Fire Department', value: 'Fire Department', labelKey: 'governmentFormOptions.authorityCategory.fireDepartment' },
  { label: 'Electricity', value: 'Electricity', labelKey: 'governmentFormOptions.authorityCategory.electricity' },
  { label: 'Water', value: 'Water', labelKey: 'governmentFormOptions.authorityCategory.water' },
  { label: 'Environment', value: 'Environment', labelKey: 'governmentFormOptions.authorityCategory.environment' },
  { label: 'Internal', value: 'Internal', labelKey: 'governmentFormOptions.authorityCategory.internal' },
]

export const FORM_CATEGORY_OPTIONS: SelectOption[] = [
  { label: 'Building Permit', value: 'Building Permit', labelKey: 'governmentFormOptions.formCategory.buildingPermit' },
  { label: 'Occupancy Certificate', value: 'Occupancy Certificate', labelKey: 'governmentFormOptions.formCategory.occupancyCertificate' },
  { label: 'Fire Safety Approval', value: 'Fire Safety Approval', labelKey: 'governmentFormOptions.formCategory.fireSafetyApproval' },
  { label: 'Utility Connection', value: 'Utility Connection', labelKey: 'governmentFormOptions.formCategory.utilityConnection' },
  {
    label: 'Environmental Clearance',
    value: 'Environmental Clearance',
    labelKey: 'governmentFormOptions.formCategory.environmentalClearance',
  },
  { label: 'Business License', value: 'Business License', labelKey: 'governmentFormOptions.formCategory.businessLicense' },
  { label: 'Agreement', value: 'Agreement', labelKey: 'governmentFormOptions.formCategory.agreement' },
  { label: 'Legal Undertaking', value: 'Legal Undertaking', labelKey: 'governmentFormOptions.formCategory.legalUndertaking' },
]

export const FORM_STATUS_FILTER_OPTIONS: SelectOption[] = [
  { label: 'All Statuses', value: 'All', labelKey: 'governmentFormOptions.statusFilter.all' },
  { label: 'Active', value: 'Active', labelKey: 'governmentFormOptions.statusFilter.active' },
  { label: 'Archived (disabled)', value: 'Archived', labelKey: 'governmentFormOptions.statusFilter.archived' },
]

export const FORM_LANGUAGE_OPTIONS: SelectOption[] = [
  { label: 'English', value: 'English', labelKey: 'governmentFormOptions.language.english' },
  { label: 'Arabic', value: 'Arabic', labelKey: 'governmentFormOptions.language.arabic' },
  { label: 'English / Arabic', value: 'English / Arabic', labelKey: 'governmentFormOptions.language.englishArabic' },
]
