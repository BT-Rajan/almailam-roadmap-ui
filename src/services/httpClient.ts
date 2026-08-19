import { useAuthStore } from '@/stores/authStore'

// Empty string by default: requests go to relative paths (e.g. /api/auth/login),
// which the Vite dev server proxies to the FastAPI backend (see vite.config.ts).
// Set VITE_API_BASE_URL in .env.local to point at a different backend (e.g. in prod).
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  /** Skip attaching the access token (e.g. for the login call itself). */
  skipAuth?: boolean
  /** Internal: prevents infinite refresh loops. */
  _retried?: boolean
}

async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const data = await response.json()
    // The backend's own exception handler (register_exception_handlers in
    // backend/app/core/exceptions.py) returns every custom AppError --
    // ValidationAppError, ConflictError, NotFoundError, AuthError,
    // PermissionDeniedError, RateLimitError, and the RequestValidationError
    // handler's own crafted messages -- under an "error" key, not "detail"
    // or "message" (that's FastAPI's default HTTPException shape, which
    // this app doesn't actually use for its own raised errors). This
    // meant every specific, helpful backend error message -- "This
    // project is marked 'Completed' and can no longer have new records
    // added to it.", "A reason is required to reject a document.", every
    // single one of them, everywhere in the app -- was silently discarded
    // in favor of a generic "Request failed (422)", the whole time.
    return data?.error ?? data?.detail ?? data?.message ?? `Request failed (${response.status})`
  } catch {
    return `Request failed (${response.status})`
  }
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const authStore = useAuthStore()
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }

  if (!options.skipAuth && authStore.accessToken) {
    headers.Authorization = `Bearer ${authStore.accessToken}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? 'GET',
    headers,
    // The refresh token now lives in an httpOnly cookie (never touched by
    // this code) instead of localStorage -- 'include' is what makes the
    // browser actually send/accept it, same-origin or cross-origin.
    credentials: 'include',
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  })

  if (response.status === 401 && !options.skipAuth && !options._retried) {
    const refreshed = await authStore.tryRefresh()
    if (refreshed) {
      return request<T>(path, { ...options, _retried: true })
    }
    authStore.logout()
    throw new ApiError(401, 'Session expired. Please log in again.')
  }

  if (!response.ok) {
    throw new ApiError(response.status, await extractErrorMessage(response))
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export const apiClient = {
  get: <T>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'POST', body }),
  put: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'PATCH', body }),
  delete: <T>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'DELETE' }),
}
