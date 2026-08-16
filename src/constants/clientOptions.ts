import type { ClientConsentType, ClientOnboardingRequirement, ClientOnboardingState, ClientType } from '@/types/Client'
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

// Flat SelectOption shape for the workspace's "Record Consent" dialog --
// CLIENT_CONSENT_TYPE_OPTIONS above carries the richer wizard-specific
// {description, mandatory} shape.
export const CLIENT_CONSENT_TYPE_SELECT_OPTIONS: SelectOption[] = CLIENT_CONSENT_TYPE_OPTIONS.map((c) => ({
  label: c.type,
  value: c.type,
}))

export const CLIENT_VERIFICATION_RESULT_OPTIONS: SelectOption[] = [
  { label: 'Verified', value: 'Verified' },
  { label: 'Rejected', value: 'Rejected' },
  { label: 'Pending', value: 'Pending' },
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

// Mirrors backend/app/core/status_transitions.py CLIENT_ONBOARDING_ALLOWED_TRANSITIONS
// exactly -- keep the two in sync. The backend is the sole source of
// enforcement (it re-validates every transition server-side); this copy
// only drives which options the UI offers, so a mismatch fails safe (the
// backend rejects it) rather than open.
export const CLIENT_ONBOARDING_ALLOWED_TRANSITIONS: Record<ClientOnboardingState, ClientOnboardingState[]> = {
  'Information Required': ['Documents Required'],
  'Documents Required': ['Verification Required'],
  'Verification Required': ['Under Review'],
  'Under Review': ['Ready', 'Rejected', 'Documents Required'],
  Ready: ['Suspended'],
  Suspended: ['Under Review', 'Rejected'],
  Rejected: ['Information Required'],
}

// Mirrors backend/app/core/status_transitions.py CLIENT_ONBOARDING_STATUSES_REQUIRING_REASON.
export const CLIENT_ONBOARDING_STATES_REQUIRING_REASON: ClientOnboardingState[] = ['Rejected', 'Suspended']

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
