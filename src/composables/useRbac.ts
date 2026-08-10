import { computed } from 'vue'
import { useAuth } from '@/composables/useAuthComposable'

export type UserRole = 'Administrator' | 'Project Manager' | 'Engineer' | 'Document Controller' | 'Viewer'

export interface Permission {
  name: string
  roles: UserRole[]
}

/**
 * Define all application permissions and which roles can access them
 */
const PERMISSIONS: Record<string, Permission> = {
  // User Management
  'users.view': { name: 'View Users', roles: ['Administrator', 'Project Manager'] },
  'users.create': { name: 'Create User', roles: ['Administrator'] },
  'users.edit': { name: 'Edit User', roles: ['Administrator'] },
  'users.delete': { name: 'Delete User', roles: ['Administrator'] },

  // Client Management
  'clients.view': { name: 'View Clients', roles: ['Administrator', 'Project Manager', 'Engineer'] },
  'clients.create': { name: 'Create Client', roles: ['Administrator', 'Project Manager'] },
  'clients.edit': { name: 'Edit Client', roles: ['Administrator', 'Project Manager'] },
  'clients.delete': { name: 'Delete Client', roles: ['Administrator'] },

  // Project Management
  'projects.view': { name: 'View Projects', roles: ['Administrator', 'Project Manager', 'Engineer', 'Document Controller'] },
  'projects.create': { name: 'Create Project', roles: ['Administrator', 'Project Manager'] },
  'projects.edit': { name: 'Edit Project', roles: ['Administrator', 'Project Manager'] },
  'projects.delete': { name: 'Delete Project', roles: ['Administrator'] },

  // Quotation Management
  'quotations.view': { name: 'View Quotations', roles: ['Administrator', 'Project Manager', 'Engineer'] },
  'quotations.create': { name: 'Create Quotation', roles: ['Administrator', 'Project Manager'] },
  'quotations.edit': { name: 'Edit Quotation', roles: ['Administrator', 'Project Manager'] },
  'quotations.delete': { name: 'Delete Quotation', roles: ['Administrator'] },

  // Contract Management
  'contracts.view': { name: 'View Contracts', roles: ['Administrator', 'Project Manager', 'Engineer'] },
  'contracts.create': { name: 'Create Contract', roles: ['Administrator', 'Project Manager'] },
  'contracts.edit': { name: 'Edit Contract', roles: ['Administrator', 'Project Manager'] },
  'contracts.delete': { name: 'Delete Contract', roles: ['Administrator'] },

  // Document Management
  'documents.view': { name: 'View Documents', roles: ['Administrator', 'Project Manager', 'Engineer', 'Document Controller'] },
  'documents.upload': { name: 'Upload Document', roles: ['Administrator', 'Project Manager', 'Engineer', 'Document Controller'] },
  'documents.delete': { name: 'Delete Document', roles: ['Administrator', 'Document Controller'] },

  // Payment Management
  'payments.view': { name: 'View Payments', roles: ['Administrator', 'Project Manager'] },
  'payments.create': { name: 'Create Payment', roles: ['Administrator', 'Project Manager'] },
  'payments.edit': { name: 'Edit Payment', roles: ['Administrator'] },
  'payments.delete': { name: 'Delete Payment', roles: ['Administrator'] },

  // Government Management
  'government.view': { name: 'View Government Forms', roles: ['Administrator', 'Project Manager', 'Engineer'] },
  'government.submit': { name: 'Submit Government Form', roles: ['Administrator', 'Project Manager'] },

  // Reports
  'reports.view': { name: 'View Reports', roles: ['Administrator', 'Project Manager'] },
  'reports.executive': { name: 'View Executive Reports', roles: ['Administrator'] },

  // Activity Calendar
  // Every role gets their own activity; only Administrators can browse
  // other users' activity (cross-user filter, "All Users" option, CSV
  // export of the whole team).
  'activity.view': {
    name: 'View Own Activity Calendar',
    roles: ['Administrator', 'Project Manager', 'Engineer', 'Document Controller', 'Viewer'],
  },
  'activity.viewAll': { name: 'View All Users Activity', roles: ['Administrator'] },
}

/**
 * RBAC composable for checking permissions in components
 *
 * Usage:
 * ```typescript
 * const { can, canAny, cannot, hasRole } = useRbac()
 *
 * if (can('users.create')) {
 *   // Show create button
 * }
 * ```
 */
export function useRbac() {
  const { user } = useAuth()

  /**
   * Check if current user has a specific permission
   */
  const can = (permissionName: string): boolean => {
    if (!user.value) return false
    const permission = PERMISSIONS[permissionName]
    if (!permission) {
      console.warn(`Permission "${permissionName}" not defined`)
      return false
    }
    return permission.roles.includes(user.value.role as UserRole)
  }

  /**
   * Check if current user has any of the specified permissions
   */
  const canAny = (permissionNames: string[]): boolean => {
    return permissionNames.some((name) => can(name))
  }

  /**
   * Check if current user does NOT have a specific permission
   */
  const cannot = (permissionName: string): boolean => {
    return !can(permissionName)
  }

  /**
   * Check if current user has a specific role
   */
  const hasRole = (role: UserRole | UserRole[]): boolean => {
    if (!user.value) return false
    if (Array.isArray(role)) {
      return role.includes(user.value.role as UserRole)
    }
    return user.value.role === role
  }

  /**
   * Check if current user is an administrator
   */
  const isAdmin = computed(() => {
    return hasRole('Administrator')
  })

  /**
   * Get all permissions for current user's role
   */
  const getUserPermissions = (): string[] => {
    if (!user.value) return []
    return Object.entries(PERMISSIONS)
      .filter(([, perm]) => perm.roles.includes(user.value!.role as UserRole))
      .map(([key]) => key)
  }

  return {
    can,
    canAny,
    cannot,
    hasRole,
    isAdmin,
    getUserPermissions,
    PERMISSIONS,
  }
}
