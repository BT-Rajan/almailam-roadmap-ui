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

function loginWithEmployeeId(employeeId: string, password: string): Promise<TokenResponse> {
  return apiClient.post<TokenResponse>(
    '/api/site-portal/login',
    { employeeId, password },
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

export const authService = { login, loginWithEmployeeId, refresh, logout, me }
