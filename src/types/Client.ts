export type ClientStatus = 'Active' | 'Inactive'

export type ClientType = 'Individual' | 'Company' | 'Organisation' | 'Government Entity' | 'Other'

export type ClientOnboardingState =
  | 'Information Required'
  | 'Documents Required'
  | 'Verification Required'
  | 'Under Review'
  | 'Ready'
  | 'Rejected'
  | 'Suspended'

export type ClientContactType =
  | 'Primary Contact'
  | 'Billing Contact'
  | 'Legal Contact'
  | 'Authorised Representative'
  | 'Technical Contact'
  | 'Other'

export type ClientAddressType = 'Registered' | 'Operating' | 'Residential' | 'Mailing'

export type ClientIdentificationType = 'Emirates ID' | 'Passport' | 'Trade Licence' | 'Other'

export type ClientDocumentCategory =
  | 'Identity Document'
  | 'Passport'
  | 'Trade Licence'
  | 'Registration Document'
  | 'Authorisation Document'
  | 'Other'

export type ClientVerificationResult = 'Pending' | 'Verified' | 'Rejected'

export type ClientConsentType =
  | 'Process Personal Information'
  | 'Electronic Communication'
  | 'Receive Notifications'
  | 'Process Documents'

export type ClientPreferredChannel = 'Email' | 'WhatsApp' | 'SMS' | 'Phone'

export interface ClientIndividualProfile {
  fullLegalName: string
  preferredName?: string
  nationality: string
  dateOfBirth: string
  countryOfResidence: string
}

export interface ClientOrganisationProfile {
  legalName: string
  tradeName?: string
  organisationType: string
  registrationNumber: string
  tradeLicenceNumber?: string
  taxIdentificationNumber?: string
  countryOfRegistration: string
  dateOfIncorporation: string
  website?: string
}

export interface ClientCommunicationPreference {
  preferredLanguage: string
  preferredChannel: ClientPreferredChannel
  emailConsent: boolean
  whatsappConsent: boolean
  smsConsent: boolean
}

export interface Client {
  id: string
  code: string
  clientType: ClientType
  companyName: string
  contactPerson: string
  mobile: string
  email: string
  city: string
  status: ClientStatus
  onboardingState: ClientOnboardingState
  createdDate: string
  individualProfile?: ClientIndividualProfile
  organisationProfile?: ClientOrganisationProfile
  communicationPreference: ClientCommunicationPreference
}

export interface ClientContact {
  id: string
  clientId: string
  name: string
  contactType: ClientContactType
  mobile: string
  email: string
  isAuthorisedRepresentative: boolean
}

export interface ClientAddress {
  id: string
  clientId: string
  addressType: ClientAddressType
  country: string
  state: string
  city: string
  area?: string
  street?: string
  building?: string
}

export interface ClientIdentification {
  id: string
  clientId: string
  documentType: ClientIdentificationType
  documentNumber: string
  issueDate: string
  expiryDate: string
  issuingCountry: string
}

export interface ClientDocument {
  id: string
  clientId: string
  category: ClientDocumentCategory
  title: string
  issueDate?: string
  expiryDate?: string
  issuingAuthority?: string
  version: number
  verificationStatus: ClientVerificationResult
  uploadedBy: string
  uploadDate: string
}

export interface ClientOnboardingRequirement {
  label: string
  category: 'Information' | 'Document'
  required: boolean
}

export interface ClientVerification {
  id: string
  clientId: string
  item: string
  result: ClientVerificationResult
  verifiedBy: string
  verifiedDate: string
  notes?: string
}

export interface ClientConsent {
  id: string
  clientId: string
  consentType: ClientConsentType
  version: string
  granted: boolean
  dateTime: string
  method: string
  recordedBy: string
}

export interface ClientAuditEvent {
  id: string
  clientId: string
  action: string
  user: string
  timestamp: string
  previousValue?: string
  newValue?: string
  reason?: string
}

export type ClientViewMode = 'grid' | 'table'

export type ClientWorkspaceTabKey = 'overview' | 'contacts' | 'documents' | 'verification' | 'consent' | 'projects' | 'activity'

export interface ClientWorkspaceTab {
  key: ClientWorkspaceTabKey
  label: string
}

export interface ClientDuplicateMatch {
  client: Client
  matchedOn: string[]
}
