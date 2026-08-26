import type { SelectOption } from '@/types/Ui'

export const AUTHORITY_CATEGORY_OPTIONS: SelectOption[] = [
  { label: 'Municipality', value: 'Municipality' },
  { label: 'Fire Department', value: 'Fire Department' },
  { label: 'Electricity', value: 'Electricity' },
  { label: 'Water', value: 'Water' },
  { label: 'Environment', value: 'Environment' },
  { label: 'Internal', value: 'Internal' },
]

export const FORM_CATEGORY_OPTIONS: SelectOption[] = [
  { label: 'Building Permit', value: 'Building Permit' },
  { label: 'Occupancy Certificate', value: 'Occupancy Certificate' },
  { label: 'Fire Safety Approval', value: 'Fire Safety Approval' },
  { label: 'Utility Connection', value: 'Utility Connection' },
  { label: 'Environmental Clearance', value: 'Environmental Clearance' },
  { label: 'Business License', value: 'Business License' },
  { label: 'Agreement', value: 'Agreement' },
  { label: 'Legal Undertaking', value: 'Legal Undertaking' },
]

export const FORM_STATUS_FILTER_OPTIONS: SelectOption[] = [
  { label: 'All Statuses', value: 'All' },
  { label: 'Active', value: 'Active' },
  { label: 'Archived (disabled)', value: 'Archived' },
]

export const FORM_LANGUAGE_OPTIONS: SelectOption[] = [
  { label: 'English', value: 'English' },
  { label: 'Arabic', value: 'Arabic' },
  { label: 'English / Arabic', value: 'English / Arabic' },
]
