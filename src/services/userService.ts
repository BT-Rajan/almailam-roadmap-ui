import { apiClient } from '@/services/httpClient'
import type { RoleDefinition } from '@/types/Role'
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

/**
 * Create a new user via backend API
 */
async function createUser(user: Partial<AppUser>): Promise<AppUser> {
  try {
    const response = await apiClient.post<AppUser>('/api/users', {
      username: user.id,
      email: user.email,
      full_name: user.name,
      password: user.id, // Temporary - should be generated or requested
      role: user.role,
      is_active: true,
    })
    return response
  } catch (error) {
    console.error('Failed to create user:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create user')
  }
}

/**
 * Update an existing user via backend API
 */
async function updateUser(user: AppUser): Promise<AppUser> {
  try {
    const response = await apiClient.patch<AppUser>(`/api/users/${user.id}`, {
      email: user.email,
      full_name: user.name,
      role: user.role,
      is_active: user.status === 'Active',
    })
    return response
  } catch (error) {
    console.error('Failed to update user:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update user')
  }
}

/**
 * Set user status (activate/deactivate) via backend API
 */
async function setUserStatus(userId: string, status: AppUser['status']): Promise<void> {
  try {
    await apiClient.patch(`/api/users/${userId}`, {
      is_active: status === 'Active',
    })
  } catch (error) {
    console.error('Failed to set user status:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to set user status')
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

export const userService = {
  getUsers,
  getRoleDefinitions,
  createUser,
  updateUser,
  setUserStatus,
  deleteUser,
}
