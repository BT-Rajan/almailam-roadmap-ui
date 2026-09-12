import { useAuthStore } from '@/stores/authStore'

// Empty string by default: requests go to relative paths (e.g. /api/auth/login),
// which the Vite dev server proxies to the FastAPI backend (see vite.config.ts).
// Set VITE_API_BASE_URL in .env.local to point at a different backend (e.g. in prod).
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

// A hung request (dropped wifi, a stalled connection, a backend that
// never responds) previously left a "Submitting..." button spinning
// forever, with no way to know whether to keep waiting or try again --
// fetch() itself has no timeout at all by default. File uploads get a
// longer budget since a multi-MB PDF genuinely can take longer than a
// plain JSON call.
const DEFAULT_TIMEOUT_MS = 20_000
const UPLOAD_TIMEOUT_MS = 60_000

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
    // project is marked 'Cancelled' and can no longer have new records
    // added to it.", "A reason is required to reject a document.", every
    // single one of them, everywhere in the app -- was silently discarded
    // in favor of a generic "Request failed (422)", the whole time.
    return data?.error ?? data?.detail ?? data?.message ?? `Request failed (${response.status})`
  } catch {
    return `Request failed (${response.status})`
  }
}

// Wraps every fetch() call in this file with a timeout and normalizes
// the two ways a request can fail before a response ever comes back:
// aborted-for-timeout, and a genuine network failure (offline, DNS,
// server unreachable, CORS). Both surface as an ApiError with a plain,
// actionable message instead of fetch's own browser-internal string
// (e.g. "Failed to fetch", "The user aborted a request") reaching
// someone mid-form.
async function fetchWithTimeout(url: string, init: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)
  try {
    return await fetch(url, { ...init, signal: controller.signal })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(0, 'This is taking longer than expected. Please check your connection and try again.')
    }
    throw new ApiError(0, 'Unable to reach the server. Please check your connection and try again.')
  } finally {
    clearTimeout(timeoutId)
  }
}

// Multipart upload counterpart to request<T>() -- FormData bodies (a
// file plus a few string fields) can't go through the JSON path above:
// no Content-Type header here at all, since the browser has to set its
// own multipart boundary. Same auth/401-retry/error-extraction
// behavior as request<T>() otherwise, so every file-upload call site
// (document uploads, the signed-PDF confirmation dialogs) gets the
// same session-refresh handling as every JSON call already does,
// instead of each hand-rolling its own fetch.
async function requestForm<T>(
  path: string,
  formData: FormData,
  options: { _retried?: boolean } = {},
): Promise<T> {
  const authStore = useAuthStore()
  const headers: Record<string, string> = {}
  if (authStore.accessToken) headers.Authorization = `Bearer ${authStore.accessToken}`

  const response = await fetchWithTimeout(
    `${API_BASE_URL}${path}`,
    {
      method: 'POST',
      headers,
      credentials: 'include',
      body: formData,
    },
    UPLOAD_TIMEOUT_MS,
  )

  if (response.status === 401 && !options._retried) {
    const refreshed = await authStore.tryRefresh()
    if (refreshed) {
      return requestForm<T>(path, formData, { _retried: true })
    }
    authStore.logout()
    throw new ApiError(401, 'Session expired. Please log in again.')
  }

  if (!response.ok) {
    throw new ApiError(response.status, await extractErrorMessage(response))
  }

  return (await response.json()) as T
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const authStore = useAuthStore()
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }

  if (!options.skipAuth && authStore.accessToken) {
    headers.Authorization = `Bearer ${authStore.accessToken}`
  }

  const response = await fetchWithTimeout(
    `${API_BASE_URL}${path}`,
    {
      method: options.method ?? 'GET',
      headers,
      // The refresh token now lives in an httpOnly cookie (never touched by
      // this code) instead of localStorage -- 'include' is what makes the
      // browser actually send/accept it, same-origin or cross-origin.
      credentials: 'include',
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    },
    DEFAULT_TIMEOUT_MS,
  )

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

// Blob counterpart to request<T>() -- for file downloads, which can't go
// through request<T>() (always calls response.json()) or requestForm<T>()
// (also json-only, and POST-only). Same auth/401-retry/timeout behavior
// as everywhere else. Previously each of documentService.ts's three
// binary-response calls (addVersion, downloadDocument, downloadVersion)
// hand-rolled this same auth-header/401-retry logic itself -- one of the
// three even remembered to extract the backend's specific error message
// on failure, the other two didn't (just "Download failed with status
// {code}"), so a permission or storage error had a real, useful message
// or a useless generic one depending on which of three nearly-identical
// blocks of code happened to handle it.
async function requestBlob(path: string, options: { method?: 'GET' | 'POST'; _retried?: boolean } = {}): Promise<Blob> {
  const authStore = useAuthStore()
  const headers: Record<string, string> = {}
  if (authStore.accessToken) headers.Authorization = `Bearer ${authStore.accessToken}`

  const response = await fetchWithTimeout(
    `${API_BASE_URL}${path}`,
    { method: options.method ?? 'GET', headers, credentials: 'include' },
    DEFAULT_TIMEOUT_MS,
  )

  if (response.status === 401 && !options._retried) {
    const refreshed = await authStore.tryRefresh()
    if (refreshed) {
      return requestBlob(path, { ...options, _retried: true })
    }
    authStore.logout()
    throw new ApiError(401, 'Session expired. Please log in again.')
  }

  if (!response.ok) {
    throw new ApiError(response.status, await extractErrorMessage(response))
  }

  return await response.blob()
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
  postForm: <T>(path: string, formData: FormData) => requestForm<T>(path, formData),
  getBlob: (path: string) => requestBlob(path, { method: 'GET' }),
}
