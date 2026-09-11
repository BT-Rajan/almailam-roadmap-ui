import type { APIRequestContext } from '@playwright/test'

// The backend URL the frontend dev server proxies /api to -- see
// vite.config.ts (VITE_API_PROXY_TARGET, default localhost:8000).
export const API_BASE_URL = process.env.E2E_API_BASE_URL ?? 'http://localhost:8000/api'

export const TEST_USER = process.env.E2E_ADMIN_USER ?? 'admin'
export const TEST_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? 'Demo#2026'

/** Logs in exactly like the frontend does (POST /auth/login) and
 * returns an Authorization header value -- used so 03/04's direct
 * backend calls hit the real auth/permission path, not a bypass. */
export async function getAuthHeader(request: APIRequestContext): Promise<{ Authorization: string }> {
  const response = await request.post(`${API_BASE_URL}/auth/login`, {
    data: { username: TEST_USER, password: TEST_PASSWORD },
  })
  if (!response.ok()) {
    throw new Error(`Login failed for backend-direct calls: ${response.status()} ${await response.text()}`)
  }
  const body = await response.json()
  return { Authorization: `${body.token_type ?? 'Bearer'} ${body.access_token}` }
}

/** Throws with the response body on any non-2xx -- every workflow-step
 * call in 03-project-workflow.spec.ts should fail loudly, not proceed
 * on a silently-ignored 4xx/5xx from a stage/status transition that
 * didn't actually happen. */
export async function expectOk<T = unknown>(responsePromise: Promise<import('@playwright/test').APIResponse>): Promise<T> {
  const response = await responsePromise
  if (!response.ok()) {
    throw new Error(`Expected 2xx, got ${response.status()}: ${await response.text()}`)
  }
  return (await response.json()) as T
}
