import type { ClientWizardAddressDraft, ClientWizardContactDraft, ClientWizardForm, ClientWizardIdentificationDraft } from '@/types/ClientWizard'
import { validators } from '@/utils/validators'

export type FieldErrors = Record<string, string>

/** Today's date as YYYY-MM-DD, for DatePicker's `max` prop and past-date checks. */
export function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}

// Digits, spaces, +, -, (, ) only, with at least 7 actual digits -- kept
// deliberately in sync with backend/app/schemas/client.py's
// _phone_validator (not the shared validators.phone(), which requires 10+
// digits and would reject valid 7-8 digit local Gulf landline/mobile
// numbers that the backend actually accepts).
const PHONE_PATTERN = /^[\d\s\-\+\(\)]+$/

function isValidPhone(value: string): boolean {
  const digits = value.replace(/\D/g, '')
  return PHONE_PATTERN.test(value) && digits.length >= 7
}

// Mirrors backend/app/schemas/client.py's _website_validator regex exactly
// -- permissive enough to accept "example.com" as well as a full URL,
// since website fields here are typed in freely rather than pasted.
const WEBSITE_PATTERN = /^(https?:\/\/)?([\w-]+\.)+[a-zA-Z]{2,}(\/\S*)?$/

function isFutureDate(value: string): boolean {
  if (!value) return false
  return value > todayIso()
}

/**
 * Step 0 (Client Type / basic info). Mirrors the required + format rules
 * the backend enforces (app/schemas/client.py's ClientCreate,
 * IndividualProfileIn, OrganisationProfileIn) so the wizard can't be
 * walked to the end with a payload the API will reject.
 */
export function validateBasicInfo(form: ClientWizardForm): FieldErrors {
  const errors: FieldErrors = {}

  if (!form.mobile.trim()) errors.mobile = 'Mobile number is required'
  else if (!isValidPhone(form.mobile)) errors.mobile = 'Enter a valid phone number (at least 7 digits)'

  if (!form.email.trim()) errors.email = 'Email address is required'
  else if (validators.email()(form.email) !== true) errors.email = 'Enter a valid email address'

  if (!form.city.trim()) errors.city = 'City is required'

  if (form.clientType === 'Individual') {
    const p = form.individualProfile
    if (!p.fullLegalName.trim()) errors.fullLegalName = 'Full legal name is required'
    if (!p.nationality.trim()) errors.nationality = 'Nationality is required'
    if (!p.countryOfResidence.trim()) errors.countryOfResidence = 'Country of residence is required'
    if (!p.dateOfBirth.trim()) errors.dateOfBirth = 'Date of birth is required'
    else if (isFutureDate(p.dateOfBirth)) errors.dateOfBirth = 'Date of birth cannot be in the future'
  } else {
    const p = form.organisationProfile
    if (!p.legalName.trim()) errors.legalName = 'Legal name is required'
    if (!p.organisationType.trim()) errors.organisationType = 'Organisation type is required'
    if (!p.registrationNumber.trim()) errors.registrationNumber = 'Registration number is required'
    if (!p.countryOfRegistration.trim()) errors.countryOfRegistration = 'Country of registration is required'
    if (!p.dateOfIncorporation.trim()) errors.dateOfIncorporation = 'Date of incorporation is required'
    else if (isFutureDate(p.dateOfIncorporation)) errors.dateOfIncorporation = 'Date of incorporation cannot be in the future'
    if (p.website.trim() && !WEBSITE_PATTERN.test(p.website.trim())) errors.website = 'Enter a valid website address'
  }

  return errors
}

export interface ContactsValidationResult {
  /** One error object per contact row, indices matching form.contacts. */
  rowErrors: FieldErrors[]
  /** Cross-row errors (duplicates) that don't belong to a single field. */
  formError?: string
}

/**
 * Step 1's contacts. Contacts are optional as a whole -- a fully blank
 * row is simply skipped -- but a partially-filled row (matching the
 * backend's all-or-nothing ClientContactCreate) must be completed
 * properly, and no two contacts on the same client may share a mobile
 * number or email (also enforced server-side in client_service.create_contact).
 */
export function validateContacts(contacts: ClientWizardContactDraft[]): ContactsValidationResult {
  const rowErrors: FieldErrors[] = contacts.map((contact) => {
    const touched = contact.name.trim() || contact.mobile.trim() || contact.email.trim()
    if (!touched) return {}

    const errors: FieldErrors = {}
    if (!contact.name.trim()) errors.name = 'Name is required'
    if (!contact.mobile.trim()) errors.mobile = 'Mobile number is required'
    else if (!isValidPhone(contact.mobile)) errors.mobile = 'Enter a valid phone number'
    if (!contact.email.trim()) errors.email = 'Email address is required'
    else if (validators.email()(contact.email) !== true) errors.email = 'Enter a valid email address'
    return errors
  })

  const activeContacts = contacts
    .map((contact, index) => ({ contact, index }))
    .filter(({ contact }) => contact.name.trim() || contact.mobile.trim() || contact.email.trim())

  const seenMobiles = new Map<string, number>()
  const seenEmails = new Map<string, number>()
  let formError: string | undefined

  for (const { contact, index } of activeContacts) {
    const mobileKey = contact.mobile.replace(/\D/g, '')
    const emailKey = contact.email.trim().toLowerCase()

    if (mobileKey && seenMobiles.has(mobileKey)) {
      formError = 'Two contacts have the same mobile number. Each contact must be unique.'
      rowErrors[index].mobile = rowErrors[index].mobile || 'Duplicate mobile number'
    } else if (mobileKey) {
      seenMobiles.set(mobileKey, index)
    }

    if (emailKey && seenEmails.has(emailKey)) {
      formError = 'Two contacts have the same email address. Each contact must be unique.'
      rowErrors[index].email = rowErrors[index].email || 'Duplicate email address'
    } else if (emailKey) {
      seenEmails.set(emailKey, index)
    }
  }

  return { rowErrors, formError }
}

/**
 * Step 1's address. The address section as a whole is optional (it's
 * only submitted if a city was entered -- see NewClientWizardPage.vue),
 * but state/governorate is required by the backend (ClientAddressCreate)
 * whenever an address is submitted, same as country and city.
 */
export function validateAddress(address: ClientWizardAddressDraft): FieldErrors {
  const errors: FieldErrors = {}
  const touched = address.city.trim().length > 0
  if (!touched) return errors

  if (!address.country.trim()) errors.country = 'Country is required'
  if (!address.state.trim()) errors.state = 'Governorate / State is required'
  if (!address.city.trim()) errors.city = 'City is required'
  return errors
}

/**
 * Step 2's identification. Optional as a whole, but once a document
 * number is entered, issue/expiry dates are required (the backend's
 * ClientIdentificationCreate has no defaults for either) and must be in
 * a sane order.
 */
export function validateIdentification(identification: ClientWizardIdentificationDraft): FieldErrors {
  const errors: FieldErrors = {}
  const touched = identification.documentNumber.trim().length > 0
  if (!touched) return errors

  if (!identification.issueDate) errors.issueDate = 'Issue date is required'
  else if (isFutureDate(identification.issueDate)) errors.issueDate = 'Issue date cannot be in the future'

  if (!identification.expiryDate) errors.expiryDate = 'Expiry date is required'
  else if (identification.issueDate && identification.expiryDate <= identification.issueDate) {
    errors.expiryDate = 'Expiry date must be after the issue date'
  }

  if (!identification.issuingCountry.trim()) errors.issuingCountry = 'Issuing country is required'

  return errors
}

export function hasErrors(errors: FieldErrors): boolean {
  return Object.keys(errors).length > 0
}

/**
 * Form shape for ClientEditDialog.vue -- editing an existing client's
 * contact details and, depending on clientType, exactly one of the two
 * profile blocks (matches backend/app/schemas/client.py's ClientUpdate,
 * which rejects setting the profile that doesn't match the client's type).
 */
export interface ClientEditForm {
  contactPerson: string
  mobile: string
  email: string
  city: string
  individualProfile: {
    fullLegalName: string
    preferredName: string
    nationality: string
    dateOfBirth: string
    countryOfResidence: string
  }
  organisationProfile: {
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
}

/**
 * Validates the edit dialog's contact-details fields plus whichever
 * profile block applies to this client's type -- same required/format
 * rules as onboarding (validateBasicInfo above), reapplied here since an
 * edit can just as easily introduce an invalid value as the original
 * onboarding could.
 */
export function validateClientEditForm(form: ClientEditForm, clientType: 'Individual' | string): FieldErrors {
  const errors: FieldErrors = {}

  if (!form.contactPerson.trim()) errors.contactPerson = 'Contact person is required'
  if (!form.mobile.trim()) errors.mobile = 'Mobile number is required'
  else if (!isValidPhone(form.mobile)) errors.mobile = 'Enter a valid phone number (at least 7 digits)'
  if (!form.email.trim()) errors.email = 'Email address is required'
  else if (validators.email()(form.email) !== true) errors.email = 'Enter a valid email address'
  if (!form.city.trim()) errors.city = 'City is required'

  if (clientType === 'Individual') {
    const p = form.individualProfile
    if (!p.fullLegalName.trim()) errors.fullLegalName = 'Full legal name is required'
    if (!p.nationality.trim()) errors.nationality = 'Nationality is required'
    if (!p.countryOfResidence.trim()) errors.countryOfResidence = 'Country of residence is required'
    if (!p.dateOfBirth.trim()) errors.dateOfBirth = 'Date of birth is required'
    else if (isFutureDate(p.dateOfBirth)) errors.dateOfBirth = 'Date of birth cannot be in the future'
  } else {
    const p = form.organisationProfile
    if (!p.legalName.trim()) errors.legalName = 'Legal name is required'
    if (!p.organisationType.trim()) errors.organisationType = 'Organisation type is required'
    if (!p.registrationNumber.trim()) errors.registrationNumber = 'Registration number is required'
    if (!p.countryOfRegistration.trim()) errors.countryOfRegistration = 'Country of registration is required'
    if (!p.dateOfIncorporation.trim()) errors.dateOfIncorporation = 'Date of incorporation is required'
    else if (isFutureDate(p.dateOfIncorporation)) errors.dateOfIncorporation = 'Date of incorporation cannot be in the future'
    if (p.website.trim() && !WEBSITE_PATTERN.test(p.website.trim())) errors.website = 'Enter a valid website address'
  }

  return errors
}
