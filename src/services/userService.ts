import { apiClient } from '@/services/httpClient'
import type { RoleDefinition, RolePermission } from '@/types/Role'
import type { AppUser } from '@/types/User'

/**
 * Fetch all users from the backend API
 */
async function getUsers(): Promise<AppUser[]> {
  try {
    const response = await apiClient.get<AppUser[]>('/api/users')
    return response || []
  } catch (error) {
    console.error('Failed to fetch users:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch users')
  }
}

/**
 * Fetch all role definitions from the backend API
 */
async function getRoleDefinitions(): Promise<RoleDefinition[]> {
  try {
    const response = await apiClient.get<RoleDefinition[]>('/api/roles')
    return response || []
  } catch (error) {
    console.error('Failed to fetch roles:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch roles')
  }
}

export interface CreatedUser extends AppUser {
  /** Shown once to the admin right after creation -- not retrievable afterwards. */
  temporaryPassword: string
}

/**
 * Create a new user via backend API. The backend's UserCreate schema only
 * accepts name/email/designation/mobile/role (it derives the username
 * from the email, always generates the temporary password itself, and
 * always creates the user Active) -- this previously sent username/
 * password/is_active fields the backend silently ignores while never
 * sending the required 'name' field, so every create failed with a 422
 * ("Please check the 'name' field") that nothing surfaced to the admin.
 */
async function createUser(user: Partial<AppUser>): Promise<CreatedUser> {
  try {
    const { temporary_password, ...created } = await apiClient.post<AppUser & { temporary_password: string }>(
      '/api/users',
      {
        name: user.name,
        email: user.email,
        designation: user.designation,
        mobile: user.mobile,
        role: user.role,
      },
    )
    return { ...created, temporaryPassword: temporary_password }
  } catch (error) {
    console.error('Failed to create user:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create user')
  }
}

/**
 * Update an existing user via backend API. The backend's UserUpdate
 * schema only accepts name/designation/mobile/role -- email is
 * immutable via this endpoint and status changes go through the
 * dedicated /status endpoint (see setUserStatus) -- so the previous
 * email/full_name/is_active payload silently updated nothing (full_name
 * isn't a recognized field, email/is_active aren't accepted at all) while
 * still returning 200, making every edit look successful and save none
 * of it.
 */
async function updateUser(user: AppUser): Promise<AppUser> {
  try {
    const response = await apiClient.patch<AppUser>(`/api/users/${user.id}`, {
      name: user.name,
      designation: user.designation,
      mobile: user.mobile,
      role: user.role,
    })
    return response
  } catch (error) {
    console.error('Failed to update user:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update user')
  }
}

/**
 * Set user status (activate/deactivate) via backend API. Previously
 * PATCHed the general update endpoint with an is_active field that
 * endpoint's schema doesn't accept -- silently ignored, so toggling a
 * user's status always reported success without changing anything. The
 * dedicated status endpoint takes {status: 'Active' | 'Inactive'}.
 */
async function setUserStatus(userId: string, status: AppUser['status']): Promise<void> {
  try {
    await apiClient.patch(`/api/users/${userId}/status`, { status })
  } catch (error) {
    console.error('Failed to set user status:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to set user status')
  }
}

/**
 * Reset a user's password to a new, randomly-generated one via backend API.
 * Returns the generated password so it can be shown to the admin once --
 * it isn't retrievable afterwards.
 */
async function resetPassword(userId: string): Promise<string> {
  try {
    const response = await apiClient.post<{ temporary_password: string }>(
      `/api/users/${userId}/reset-password`,
    )
    return response.temporary_password
  } catch (error) {
    console.error('Failed to reset password:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to reset password')
  }
}

/**
 * Delete a user via backend API
 */
async function deleteUser(userId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/users/${userId}`)
  } catch (error) {
    console.error('Failed to delete user:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete user')
  }
}

/**
 * Update a role's permission matrix via backend API. Always sends the
 * full set of permissions for the role (see RoleDefinitionUpdate on the
 * backend) -- simpler to reason about than a partial per-cell PATCH.
 */
async function updateRoleDefinition(role: string, permissions: RolePermission[]): Promise<RoleDefinition> {
  try {
    const response = await apiClient.patch<RoleDefinition>(`/api/roles/${encodeURIComponent(role)}`, {
      permissions,
    })
    return response
  } catch (error) {
    console.error('Failed to update role permissions:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update role permissions')
  }
}

export const userService = {
  getUsers,
  getRoleDefinitions,
  createUser,
  updateUser,
  setUserStatus,
  resetPassword,
  deleteUser,
  updateRoleDefinition,
}
