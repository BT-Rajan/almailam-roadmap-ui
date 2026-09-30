import { apiClient } from '@/services/httpClient'
import type { CompanyBranding } from '@/types/CompanySettings'
import type { ServerTime } from '@/types/ServerTime'

interface TokenResponse {
  access_token: string
  token_type: string
  /** The signed-in user, same as /api/auth/me -- saves a second round trip.
   * Optional so a server that predates it still works (falls back to me()). */
  user?: CurrentUser
  /** What the app needs to start, so it doesn't ask separately (see authStore._applySession). */
  session?: SessionBootstrap
}

export interface SessionBootstrap {
  serverTime: ServerTime
  branding: CompanyBranding
  /** Knowledgebase assistant on -- false when this user can't use it. */
  knowledgeEnabled: boolean
}

export type PermissionAction = 'view' | 'edit' | 'delete'

export interface CurrentUser {
  id: string
  name: string
  designation: string | null
  email: string
  mobile: string | null
  role: string
  avatar: string
  status: string
  /**
   * The caller's effective permissions per module, straight from the
   * server's role matrix (the same one require_permission enforces).
   * Optional only so older cached/mocked users don't crash: consumers
   * must treat a missing entry as "no access" (see usePermissions).
   */
  permissions?: Record<string, Record<PermissionAction, boolean>>
}

function login(username: string, password: string): Promise<TokenResponse> {
  return apiClient.post<TokenResponse>(
    '/api/auth/login',
    { username, password },
    { skipAuth: true },
  )
}

function refresh(): Promise<TokenResponse> {
  return apiClient.post<TokenResponse>('/api/auth/refresh', undefined, { skipAuth: true })
}

function logout(): Promise<void> {
  return apiClient.post<void>('/api/auth/logout')
}

function me(): Promise<CurrentUser> {
  return apiClient.get<CurrentUser>('/api/auth/me')
}

function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  return apiClient.post<void>('/api/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}

export interface ProfileUpdatePayload {
  name?: string
  designation?: string | null
  mobile?: string | null
}

function updateProfile(payload: ProfileUpdatePayload): Promise<CurrentUser> {
  return apiClient.patch<CurrentUser>('/api/auth/me', payload)
}

export const authService = { login, refresh, logout, me, changePassword, updateProfile }
