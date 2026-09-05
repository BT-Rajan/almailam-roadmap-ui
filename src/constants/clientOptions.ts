import type {
  ClientDocumentCategory,
  ClientIdentificationType,
  ClientOnboardingRequirement,
  ClientOnboardingState,
  ClientType,
} from '@/types/Client'
import type { SelectOption } from '@/types/Ui'

export const CLIENT_TYPE_OPTIONS: SelectOption[] = [
  { label: 'Individual', value: 'Individual', labelKey: 'clientOptions.type.individual' },
  { label: 'Company', value: 'Company', labelKey: 'clientOptions.type.company' },
  { label: 'Organisation', value: 'Organisation', labelKey: 'clientOptions.type.organisation' },
  { label: 'Government Entity', value: 'Government Entity', labelKey: 'clientOptions.type.governmentEntity' },
  { label: 'Other', value: 'Other', labelKey: 'clientOptions.type.other' },
]

export const CLIENT_CONTACT_TYPE_OPTIONS: SelectOption[] = [
  { label: 'Primary Contact', value: 'Primary Contact', labelKey: 'clientOptions.contactType.primary' },
  { label: 'Billing Contact', value: 'Billing Contact', labelKey: 'clientOptions.contactType.billing' },
  { label: 'Legal Contact', value: 'Legal Contact', labelKey: 'clientOptions.contactType.legal' },
  {
    label: 'Authorised Representative',
    value: 'Authorised Representative',
    labelKey: 'clientOptions.contactType.authorisedRepresentative',
  },
  { label: 'Technical Contact', value: 'Technical Contact', labelKey: 'clientOptions.contactType.technical' },
  { label: 'Other', value: 'Other', labelKey: 'clientOptions.contactType.other' },
]

export const CLIENT_IDENTIFICATION_TYPE_OPTIONS: SelectOption[] = [
  { label: 'Civil ID', value: 'Civil ID', labelKey: 'clientOptions.identificationType.civilId' },
  { label: 'Passport', value: 'Passport', labelKey: 'clientOptions.identificationType.passport' },
  { label: 'Trade Licence', value: 'Trade Licence', labelKey: 'clientOptions.identificationType.tradeLicence' },
  { label: 'Other', value: 'Other', labelKey: 'clientOptions.identificationType.other' },
]

// Individuals identify with a personal document; every entity-type client
// (Company/Organisation/Government Entity) identifies with its trade
// licence instead -- Civil ID/Passport don't apply to an entity. 'Other'
// was previously offered identically to every client type regardless of
// this distinction, which is what let the wizard default an entity client
// to 'Civil ID' (see createEmptyClientWizardForm in types/ClientWizard.ts).
export const CLIENT_IDENTIFICATION_TYPE_OPTIONS_BY_CLIENT_TYPE: Record<ClientType, SelectOption[]> = {
  Individual: CLIENT_IDENTIFICATION_TYPE_OPTIONS.filter((option) => option.value !== 'Trade Licence'),
  Company: CLIENT_IDENTIFICATION_TYPE_OPTIONS.filter((option) => option.value === 'Trade Licence' || option.value === 'Other'),
  Organisation: CLIENT_IDENTIFICATION_TYPE_OPTIONS.filter((option) => option.value === 'Trade Licence' || option.value === 'Other'),
  'Government Entity': CLIENT_IDENTIFICATION_TYPE_OPTIONS.filter((option) => option.value === 'Trade Licence' || option.value === 'Other'),
  // Unknown/mixed entity shape -- offer everything rather than guess.
  Other: CLIENT_IDENTIFICATION_TYPE_OPTIONS,
}

export function getIdentificationTypeOptionsForClientType(clientType: ClientType): SelectOption[] {
  return CLIENT_IDENTIFICATION_TYPE_OPTIONS_BY_CLIENT_TYPE[clientType] ?? CLIENT_IDENTIFICATION_TYPE_OPTIONS
}

export function getDefaultIdentificationTypeForClientType(clientType: ClientType): ClientIdentificationType {
  const [firstOption] = getIdentificationTypeOptionsForClientType(clientType)
  return (firstOption?.value as ClientIdentificationType | undefined) ?? 'Other'
}

// Maps the identification document a client onboards with to the client
// document *category* it should be filed under once uploaded. Previously
// NewClientWizardPage.vue hardcoded every onboarding upload to 'Identity
// Document' regardless of what was actually selected here -- so an
// entity client uploading its Trade Licence during onboarding was filed
// under the wrong category and never satisfied the "Trade licence"
// onboarding requirement in CLIENT_ONBOARDING_REQUIREMENTS below (which
// checks specifically for category === 'Trade Licence').
export function getDocumentCategoryForIdentificationType(documentType: ClientIdentificationType): ClientDocumentCategory {
  switch (documentType) {
    case 'Civil ID':
      return 'Identity Document'
    case 'Passport':
      return 'Passport'
    case 'Trade Licence':
      return 'Trade Licence'
    default:
      return 'Other'
  }
}

export const CLIENT_DOCUMENT_CATEGORY_OPTIONS: SelectOption[] = [
  { label: 'Identity Document', value: 'Identity Document', labelKey: 'clientOptions.documentCategory.identityDocument' },
  { label: 'Passport', value: 'Passport', labelKey: 'clientOptions.documentCategory.passport' },
  { label: 'Trade Licence', value: 'Trade Licence', labelKey: 'clientOptions.documentCategory.tradeLicence' },
  {
    label: 'Registration Document',
    value: 'Registration Document',
    labelKey: 'clientOptions.documentCategory.registrationDocument',
  },
  {
    label: 'Authorisation Document',
    value: 'Authorisation Document',
    labelKey: 'clientOptions.documentCategory.authorisationDocument',
  },
  { label: 'Other', value: 'Other', labelKey: 'clientOptions.documentCategory.other' },
]

export const CLIENT_VERIFICATION_RESULT_OPTIONS: SelectOption[] = [
  { label: 'Verified', value: 'Verified', labelKey: 'clientOptions.verificationResult.verified' },
  { label: 'Rejected', value: 'Rejected', labelKey: 'clientOptions.verificationResult.rejected' },
  { label: 'Pending', value: 'Pending', labelKey: 'clientOptions.verificationResult.pending' },
]

export const CLIENT_ADDRESS_TYPE_OPTIONS: SelectOption[] = [
  { label: 'Registered', value: 'Registered', labelKey: 'clientOptions.addressType.registered' },
  { label: 'Operating', value: 'Operating', labelKey: 'clientOptions.addressType.operating' },
  { label: 'Residential', value: 'Residential', labelKey: 'clientOptions.addressType.residential' },
  { label: 'Mailing', value: 'Mailing', labelKey: 'clientOptions.addressType.mailing' },
]

export const CLIENT_STATUS_OPTIONS: SelectOption[] = [
  { label: 'All Statuses', value: 'All', labelKey: 'clientOptions.status.all' },
  { label: 'Active', value: 'Active', labelKey: 'clientOptions.status.active' },
  { label: 'Inactive', value: 'Inactive', labelKey: 'clientOptions.status.inactive' },
]

export const CLIENT_ONBOARDING_STATE_OPTIONS: SelectOption[] = [
  { label: 'All Onboarding States', value: 'All', labelKey: 'clientOptions.onboardingState.all' },
  { label: 'Information Required', value: 'Information Required', labelKey: 'clientOptions.onboardingState.informationRequired' },
  { label: 'Documents Required', value: 'Documents Required', labelKey: 'clientOptions.onboardingState.documentsRequired' },
  { label: 'Under Review', value: 'Under Review', labelKey: 'clientOptions.onboardingState.underReview' },
  { label: 'Ready', value: 'Ready', labelKey: 'clientOptions.onboardingState.ready' },
  { label: 'Rejected', value: 'Rejected', labelKey: 'clientOptions.onboardingState.rejected' },
  { label: 'Suspended', value: 'Suspended', labelKey: 'clientOptions.onboardingState.suspended' },
]

// Mirrors backend/app/core/status_transitions.py CLIENT_ONBOARDING_ALLOWED_TRANSITIONS
// exactly -- keep the two in sync. The backend is the sole source of
// enforcement (it re-validates every transition server-side); this copy
// only drives which options the UI offers, so a mismatch fails safe (the
// backend rejects it) rather than open.
export const CLIENT_ONBOARDING_ALLOWED_TRANSITIONS: Record<ClientOnboardingState, ClientOnboardingState[]> = {
  'Information Required': ['Documents Required'],
  'Documents Required': ['Under Review'],
  'Under Review': ['Ready', 'Rejected', 'Documents Required'],
  Ready: ['Suspended'],
  Suspended: ['Under Review', 'Rejected'],
  Rejected: ['Information Required'],
}

// Mirrors backend/app/core/status_transitions.py CLIENT_ONBOARDING_STATUSES_REQUIRING_REASON.
export const CLIENT_ONBOARDING_STATES_REQUIRING_REASON: ClientOnboardingState[] = ['Rejected', 'Suspended']

const INDIVIDUAL_REQUIREMENTS: ClientOnboardingRequirement[] = [
  {
    label: 'Full legal name',
    labelKey: 'clientOptions.onboardingRequirement.fullLegalName',
    category: 'Information',
    required: true,
    isSatisfied: (ctx) => Boolean(ctx.client.individualProfile?.fullLegalName?.trim()),
  },
  {
    label: 'Mobile number',
    labelKey: 'clientOptions.onboardingRequirement.mobileNumber',
    category: 'Information',
    required: true,
    isSatisfied: (ctx) => Boolean(ctx.client.mobile?.trim()),
  },
  {
    label: 'Identification document',
    labelKey: 'clientOptions.onboardingRequirement.identificationDocument',
    category: 'Document',
    required: true,
    isSatisfied: (ctx) => ctx.documents.length > 0,
  },
  {
    label: 'Address on file',
    labelKey: 'clientOptions.onboardingRequirement.addressOnFile',
    category: 'Information',
    required: false,
    isSatisfied: (ctx) => ctx.addresses.length > 0,
  },
  {
    label: 'Identification recorded',
    labelKey: 'clientOptions.onboardingRequirement.identificationRecorded',
    category: 'Identification',
    required: true,
    isSatisfied: (ctx) => ctx.identifications.length > 0,
  },
]

const ORGANISATION_REQUIREMENTS: ClientOnboardingRequirement[] = [
  {
    label: 'Legal name',
    labelKey: 'clientOptions.onboardingRequirement.legalName',
    category: 'Information',
    required: true,
    isSatisfied: (ctx) => Boolean(ctx.client.organisationProfile?.legalName?.trim()),
  },
  {
    label: 'Registration number',
    labelKey: 'clientOptions.onboardingRequirement.registrationNumber',
    category: 'Information',
    required: true,
    isSatisfied: (ctx) => Boolean(ctx.client.organisationProfile?.registrationNumber?.trim()),
  },
  {
    label: 'Trade licence',
    labelKey: 'clientOptions.onboardingRequirement.tradeLicence',
    category: 'Document',
    required: true,
    isSatisfied: (ctx) => ctx.documents.some((d) => d.category === 'Trade Licence'),
  },
  {
    label: 'Authorised representative',
    labelKey: 'clientOptions.onboardingRequirement.authorisedRepresentative',
    category: 'Information',
    required: true,
    isSatisfied: (ctx) => ctx.contacts.some((c) => c.isAuthorisedRepresentative),
  },
  {
    label: 'Additional supporting document',
    labelKey: 'clientOptions.onboardingRequirement.additionalSupportingDocument',
    category: 'Document',
    required: false,
    isSatisfied: (ctx) => ctx.documents.length > 1,
  },
  {
    label: 'Identification recorded',
    labelKey: 'clientOptions.onboardingRequirement.identificationRecorded',
    category: 'Identification',
    required: true,
    isSatisfied: (ctx) => ctx.identifications.length > 0,
  },
]

export const CLIENT_ONBOARDING_REQUIREMENTS: Record<ClientType, ClientOnboardingRequirement[]> = {
  Individual: INDIVIDUAL_REQUIREMENTS,
  Company: ORGANISATION_REQUIREMENTS,
  Organisation: ORGANISATION_REQUIREMENTS,
  'Government Entity': ORGANISATION_REQUIREMENTS,
  Other: INDIVIDUAL_REQUIREMENTS,
}
