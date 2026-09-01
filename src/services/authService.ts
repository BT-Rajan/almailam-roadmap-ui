import { apiClient } from '@/services/httpClient'

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface CurrentUser {
  id: string
  name: string
  designation: string | null
  email: string
  mobile: string | null
  role: string
  avatar: string
  status: string
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
