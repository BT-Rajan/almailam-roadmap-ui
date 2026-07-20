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
  hasIdentificationDocument: boolean
  hasUploadedFile: boolean
  consents: Record<ClientConsentType, boolean>
  communicationPreference: ClientCommunicationPreference
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
      nationality: '',
      dateOfBirth: '',
      countryOfResidence: '',
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
      country: 'United Arab Emirates',
      state: '',
      city: '',
      area: '',
      street: '',
      building: '',
    },
    identification: {
      documentType: 'Emirates ID',
      documentNumber: '',
      issueDate: '',
      expiryDate: '',
      issuingCountry: 'United Arab Emirates',
    },
    hasIdentificationDocument: false,
    hasUploadedFile: false,
    consents: {
      'Process Personal Information': false,
      'Electronic Communication': false,
      'Receive Notifications': false,
      'Process Documents': false,
    },
    communicationPreference: {
      preferredLanguage: 'English',
      preferredChannel: 'Email',
      emailConsent: false,
      whatsappConsent: false,
      smsConsent: false,
    },
  }
}
