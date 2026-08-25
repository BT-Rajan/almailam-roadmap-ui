import type {
  ClientAddressType,
  ClientCommunicationPreference,
  ClientConsentType,
  ClientContactType,
  ClientIdentificationType,
  ClientType,
} from '@/types/Client'

export interface ClientWizardIndividualProfile {
  fullLegalName: string
  preferredName: string
  nationality: string
  dateOfBirth: string
  countryOfResidence: string
}

export interface ClientWizardOrganisationProfile {
  legalName: string
  tradeName: string
  organisationType: string
  registrationNumber: string
  tradeLicenceNumber: string
  taxIdentificationNumber: string
  countryOfRegistration: string
  dateOfIncorporation: string
  website: string
}

export interface ClientWizardContactDraft {
  name: string
  contactType: ClientContactType
  mobile: string
  email: string
  isAuthorisedRepresentative: boolean
}

export interface ClientWizardAddressDraft {
  addressType: ClientAddressType
  country: string
  state: string
  city: string
  area: string
  street: string
  building: string
}

export interface ClientWizardIdentificationDraft {
  documentType: ClientIdentificationType
  documentNumber: string
  issueDate: string
  expiryDate: string
  issuingCountry: string
}

export interface ClientWizardForm {
  clientType: ClientType
  companyName: string
  contactPerson: string
  mobile: string
  email: string
  city: string
  individualProfile: ClientWizardIndividualProfile
  organisationProfile: ClientWizardOrganisationProfile
  contacts: ClientWizardContactDraft[]
  address: ClientWizardAddressDraft
  identification: ClientWizardIdentificationDraft
  identificationFile: File | null
  consents: Record<ClientConsentType, boolean>
  communicationPreference: ClientCommunicationPreference
  /** "" means unassigned -- optional, can be set later via Edit Client too. */
  accountManagerId: string
}

export function createEmptyClientWizardForm(): ClientWizardForm {
  return {
    clientType: 'Individual',
    companyName: '',
    contactPerson: '',
    mobile: '',
    email: '',
    city: '',
    individualProfile: {
      fullLegalName: '',
      preferredName: '',
      // Almailam only onboards Kuwait-based clients -- defaulted rather
      // than left blank so the wizard doesn't ask for it, but the field
      // itself stays (the backend still records it, and Country of
      // Residence isn't shown in the UI at all anymore, see
      // ClientBasicInfoStep.vue).
      nationality: 'Kuwait',
      dateOfBirth: '',
      countryOfResidence: 'Kuwait',
    },
    organisationProfile: {
      legalName: '',
      tradeName: '',
      organisationType: '',
      registrationNumber: '',
      tradeLicenceNumber: '',
      taxIdentificationNumber: '',
      countryOfRegistration: '',
      dateOfIncorporation: '',
      website: '',
    },
    contacts: [{ name: '', contactType: 'Primary Contact', mobile: '', email: '', isAuthorisedRepresentative: true }],
    address: {
      addressType: 'Registered',
      country: 'Kuwait',
      state: '',
      city: '',
      area: '',
      street: '',
      building: '',
    },
    identification: {
      documentType: 'Civil ID',
      documentNumber: '',
      issueDate: '',
      expiryDate: '',
      issuingCountry: 'Kuwait',
    },
    identificationFile: null,
    consents: {
      'Process Personal Information': false,
      'Electronic Communication': false,
      'Process Documents': false,
    },
    communicationPreference: {
      preferredLanguage: 'English',
      preferredChannel: 'Email',
      emailConsent: false,
      whatsappConsent: false,
      smsConsent: false,
    },
    accountManagerId: '',
  }
}
