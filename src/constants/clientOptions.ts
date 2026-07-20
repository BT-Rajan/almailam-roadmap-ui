import type { ClientConsentType, ClientOnboardingRequirement, ClientType } from '@/types/Client'
import type { SelectOption } from '@/types/Ui'

export const CLIENT_TYPE_OPTIONS: SelectOption[] = [
  { label: 'Individual', value: 'Individual' },
  { label: 'Company', value: 'Company' },
  { label: 'Organisation', value: 'Organisation' },
  { label: 'Government Entity', value: 'Government Entity' },
  { label: 'Other', value: 'Other' },
]

export const CLIENT_CONTACT_TYPE_OPTIONS: SelectOption[] = [
  { label: 'Primary Contact', value: 'Primary Contact' },
  { label: 'Billing Contact', value: 'Billing Contact' },
  { label: 'Legal Contact', value: 'Legal Contact' },
  { label: 'Authorised Representative', value: 'Authorised Representative' },
  { label: 'Technical Contact', value: 'Technical Contact' },
  { label: 'Other', value: 'Other' },
]

export const CLIENT_IDENTIFICATION_TYPE_OPTIONS: SelectOption[] = [
  { label: 'Emirates ID', value: 'Emirates ID' },
  { label: 'Passport', value: 'Passport' },
  { label: 'Trade Licence', value: 'Trade Licence' },
  { label: 'Other', value: 'Other' },
]

export const CLIENT_DOCUMENT_CATEGORY_OPTIONS: SelectOption[] = [
  { label: 'Identity Document', value: 'Identity Document' },
  { label: 'Passport', value: 'Passport' },
  { label: 'Trade Licence', value: 'Trade Licence' },
  { label: 'Registration Document', value: 'Registration Document' },
  { label: 'Authorisation Document', value: 'Authorisation Document' },
  { label: 'Other', value: 'Other' },
]

export const CLIENT_CONSENT_TYPE_OPTIONS: { type: ClientConsentType; description: string; mandatory: boolean }[] = [
  {
    type: 'Process Personal Information',
    description: 'Allow Almailam Engineering Consultants to collect and process personal or business information.',
    mandatory: true,
  },
  {
    type: 'Electronic Communication',
    description: 'Allow communication by email, WhatsApp and SMS regarding onboarding and service updates.',
    mandatory: false,
  },
  {
    type: 'Receive Notifications',
    description: 'Allow notifications about document expiry, verification status and project milestones.',
    mandatory: false,
  },
  {
    type: 'Process Documents',
    description: 'Allow uploaded identity and registration documents to be stored and processed.',
    mandatory: false,
  },
]

export const CLIENT_ADDRESS_TYPE_OPTIONS: SelectOption[] = [
  { label: 'Registered', value: 'Registered' },
  { label: 'Operating', value: 'Operating' },
  { label: 'Residential', value: 'Residential' },
  { label: 'Mailing', value: 'Mailing' },
]

export const CLIENT_STATUS_OPTIONS: SelectOption[] = [
  { label: 'All Statuses', value: 'All' },
  { label: 'Active', value: 'Active' },
  { label: 'Inactive', value: 'Inactive' },
]

export const CLIENT_ONBOARDING_STATE_OPTIONS: SelectOption[] = [
  { label: 'All Onboarding States', value: 'All' },
  { label: 'Information Required', value: 'Information Required' },
  { label: 'Documents Required', value: 'Documents Required' },
  { label: 'Verification Required', value: 'Verification Required' },
  { label: 'Under Review', value: 'Under Review' },
  { label: 'Ready', value: 'Ready' },
  { label: 'Rejected', value: 'Rejected' },
  { label: 'Suspended', value: 'Suspended' },
]

const INDIVIDUAL_REQUIREMENTS: ClientOnboardingRequirement[] = [
  { label: 'Full legal name', category: 'Information', required: true },
  { label: 'Mobile number', category: 'Information', required: true },
  { label: 'Identification document', category: 'Document', required: true },
  { label: 'Address on file', category: 'Information', required: false },
]

const ORGANISATION_REQUIREMENTS: ClientOnboardingRequirement[] = [
  { label: 'Legal name', category: 'Information', required: true },
  { label: 'Registration number', category: 'Information', required: true },
  { label: 'Trade licence', category: 'Document', required: true },
  { label: 'Authorised representative', category: 'Information', required: true },
  { label: 'Additional supporting document', category: 'Document', required: false },
]

export const CLIENT_ONBOARDING_REQUIREMENTS: Record<ClientType, ClientOnboardingRequirement[]> = {
  Individual: INDIVIDUAL_REQUIREMENTS,
  Company: ORGANISATION_REQUIREMENTS,
  Organisation: ORGANISATION_REQUIREMENTS,
  'Government Entity': ORGANISATION_REQUIREMENTS,
  Other: INDIVIDUAL_REQUIREMENTS,
}

export const CLIENT_PERMISSIONS = {
  VIEW: 'client.view',
  CREATE: 'client.create',
  EDIT: 'client.edit',
  DELETE: 'client.delete',
  MERGE: 'client.merge',
  VERIFY: 'client.verify',
  VIEW_SENSITIVE: 'client.view_sensitive',
  MANAGE_DOCUMENTS: 'client.manage_documents',
  MANAGE_CONSENT: 'client.manage_consent',
  EXPORT: 'client.export',
} as const
