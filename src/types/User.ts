export type UserRole = 'Administrator' | 'Project Manager' | 'Engineer' | 'Document Controller' | 'Viewer' | 'Customer'

export type UserStatus = 'Active' | 'Inactive'

export interface AppUser {
  id: string
  name: string
  designation: string
  email: string
  mobile: string
  role: UserRole
  avatar: string
  status: UserStatus
}
