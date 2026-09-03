export type AppLanguage = 'English' | 'Arabic'

export interface CompanySettings {
  companyName: string
  tagline: string
  tradeLicenseNumber: string
  email: string
  phone: string
  website: string
  address: string
  city: string
  country: string
  brandColor: string
  defaultLanguage: AppLanguage
  timezone: string
  dateFormat: string
  currency: string
  defaultPaymentTermsDays: number
  defaultQuotationValidityDays: number
  staleProjectAlertDays: number
  staleOnboardingAlertDays: number
  statusReportRecipientId?: string | null
  // Whether a company logo has been uploaded (Administration > Company)
  // -- insertable into any Quotation/Contract document template via its
  // Company Logo merge field. Fetch the actual image from
  // companyService.getLogoBlob(); hasLogo just avoids an unnecessary
  // request when there isn't one.
  hasLogo: boolean
  logoFilename?: string | null
}
