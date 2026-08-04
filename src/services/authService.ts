import { apiClient } from '@/services/httpClient'

export interface TokenResponse {
  access_token: string
  refresh_token: string
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

function refresh(refreshToken: string): Promise<TokenResponse> {
  return apiClient.post<TokenResponse>(
    '/api/auth/refresh',
    { refresh_token: refreshToken },
    { skipAuth: true },
  )
}

function logout(refreshToken: string): Promise<void> {
  return apiClient.post<void>('/api/auth/logout', { refresh_token: refreshToken })
}

function me(): Promise<CurrentUser> {
  return apiClient.get<CurrentUser>('/api/auth/me')
}

export const authService = { login, refresh, logout, me }
