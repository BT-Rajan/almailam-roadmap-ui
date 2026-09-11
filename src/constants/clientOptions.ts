import type { ClientDocumentCategory, ClientIdentificationType, ClientType } from '@/types/Client'
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

const CLIENT_IDENTIFICATION_TYPE_OPTIONS: SelectOption[] = [
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
const CLIENT_IDENTIFICATION_TYPE_OPTIONS_BY_CLIENT_TYPE: Record<ClientType, SelectOption[]> = {
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
