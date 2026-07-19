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
}
