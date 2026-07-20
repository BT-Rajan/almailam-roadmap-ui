import type { UserRole } from '@/types/User'

export type PermissionModule = 'Projects' | 'Documents' | 'Government' | 'Reports' | 'Administration'

export interface RolePermission {
  module: PermissionModule
  view: boolean
  edit: boolean
  delete: boolean
}

export interface RoleDefinition {
  role: UserRole
  description: string
  permissions: RolePermission[]
}
