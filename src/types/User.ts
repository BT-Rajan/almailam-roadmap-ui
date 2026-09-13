export type UserRole = 'Administrator' | 'Project Manager' | 'Engineer' | 'Document Controller' | 'Viewer' | 'Customer'

export type UserStatus = 'Active' | 'Inactive'

export type UserSalutation = 'Mr.' | 'Ms.'

export interface AppUser {
  id: string
  name: string
  // Optional -- see backend migration 0097. Printed ahead of the name
  // on generated documents (Quotation/Contract "Prepared By") once set;
  // left unset, documents just print the bare name as before.
  salutation?: UserSalutation
  designation: string
  email: string
  mobile: string
  role: UserRole
  avatar: string
  status: UserStatus
}
