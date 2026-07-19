export type ClientStatus = 'Active' | 'Inactive'

export interface Client {
  id: string
  code: string
  companyName: string
  contactPerson: string
  mobile: string
  email: string
  city: string
  status: ClientStatus
}
