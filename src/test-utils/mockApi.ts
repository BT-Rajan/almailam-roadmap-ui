/**
 * A stand-in for `apiClient` (src/services/httpClient.ts) so page and
 * component tests run against the real components, router and Pinia stores
 * with only the network faked -- no backend needed.
 *
 * Responses come from ./fixtures/handoverWorkspace.json: real API responses
 * captured for one project sitting at the Handover stage with a Design and a
 * Supervision payment plan, trimmed to that project's own records.
 *
 * Usage (must be in the test file itself -- vi.mock is hoisted per file):
 *
 *   vi.mock('@/services/httpClient', async (importOriginal) => {
 *     const actual = await importOriginal<typeof import('@/services/httpClient')>()
 *     const { mockApiClient } = await import('@/test-utils/mockApi')
 *     return { ...actual, apiClient: mockApiClient }
 *   })
 *
 * This module deliberately does NOT import httpClient (the mock factory above
 * imports *this* module, so that would be circular). Tests that need an
 * ApiError import it from '@/services/httpClient' themselves and pass a
 * factory in.
 */
import type { CurrentUser, PermissionAction } from '@/services/authService'

import fixtureJson from './fixtures/handoverWorkspace.json'

// The fixture is plain captured JSON; tests read it loosely.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const fixture = fixtureJson as any

export interface MockCall {
  method: string
  path: string
}

type Handler = (ctx: { method: string; path: string; body: unknown }) => unknown

/** Every request made since the last reset, in order. */
export const mockCalls: MockCall[] = []
/** Requests no route matched (they get `[]`). Tests assert this stays empty so a stale fixture can't hide behind silent defaults. */
export const mockUnmatched: string[] = []

let overrides: { match: RegExp; method?: string; handler: Handler }[] = []
let rateLimit: { limit: number; makeError: () => Error } | undefined
// Mutable copy so confirm/unconfirm-payment behave like the real endpoints.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let project: any = structuredClone(fixture.project)

// A real macrotask per request. Without it a remount loop would resolve
// entirely in microtasks, starve the event loop and hang the test run
// instead of failing it.
const LATENCY_MS = 5

export function resetMockApi(): void {
  mockCalls.length = 0
  mockUnmatched.length = 0
  overrides = []
  rateLimit = undefined
  project = structuredClone(fixture.project)
}

/** Replace the response for matching requests (first matching override wins). Throw from the handler to simulate an error. */
export function overrideMockApi(match: RegExp, handler: Handler, method?: string): void {
  overrides.unshift({ match, handler, method })
}

/**
 * Behave like the real backend's limiter (300 requests / 60s per client, see
 * backend/app/core/rate_limit.py): once more than `limit` requests have been
 * made, every further one rejects. A page that starts hammering the API ends
 * the way it did in production instead of looping forever.
 */
export function setMockRateLimit(limit: number, makeError: () => Error): void {
  rateLimit = { limit, makeError }
}

export function countCalls(match: RegExp, method = 'GET'): number {
  return mockCalls.filter((c) => c.method === method && match.test(c.path)).length
}

function defaultRoute(method: string, path: string): unknown {
  const [pathname] = path.split('?')
  let m: RegExpMatchArray | null

  if (method === 'GET') {
    if (pathname === '/api/server-time') return fixture.serverTime
    if (pathname === '/api/users') return fixture.users
    if (pathname === '/api/projects') return fixture.projectsPage
    if ((m = pathname.match(/^\/api\/projects\/[^/]+\/handover$/))) return fixture.handover
    if (/^\/api\/projects\/[^/]+$/.test(pathname)) return project
    if (pathname === '/api/clients') return fixture.clientsPage
    if (pathname === '/api/service-catalog/services') return fixture.serviceCatalog
    if (pathname === '/api/financial-agreements') return fixture.agreements
    if ((m = pathname.match(/^\/api\/financial-agreements\/by-project\/[^/]+$/))) {
      const stream = new URLSearchParams(path.split('?')[1] ?? '').get('stream')
      return fixture.agreements.find((a: { stream: string }) => !stream || a.stream === stream) ?? null
    }
    if ((m = pathname.match(/^\/api\/financial-agreements\/([^/]+)\/(payments|audit-events|refunds|adjustments)$/))) {
      return fixture.agreementDetail[m[1]]?.[m[2]] ?? []
    }
    if ((m = pathname.match(/^\/api\/financial-agreements\/([^/]+)\/obligations$/))) {
      return fixture.obligations.filter((o: { agreementId: string }) => o.agreementId === m![1])
    }
    if (pathname === '/api/obligations') return fixture.obligations
    if (pathname === '/api/quotations') return fixture.quotations
    if ((m = pathname.match(/^\/api\/quotations\/([^/]+)\/audit-events$/))) return fixture.quotationAudit[m[1]] ?? []
    if (pathname === '/api/contracts') return fixture.contracts
  }

  if (method === 'POST' && /\/handover\/confirm-payment$/.test(pathname)) {
    project = {
      ...project,
      handoverPaymentConfirmedAt: '2026-09-19T20:00:00+03:00',
      handoverPaymentConfirmedBy: 'Sandbox Admin',
    }
    return project
  }
  if (method === 'POST' && /\/handover\/unconfirm-payment$/.test(pathname)) {
    project = { ...project, handoverPaymentConfirmedAt: null, handoverPaymentConfirmedBy: null }
    return project
  }

  mockUnmatched.push(`${method} ${path}`)
  return []
}

async function route(method: string, path: string, body?: unknown): Promise<unknown> {
  mockCalls.push({ method, path })
  await new Promise((resolve) => setTimeout(resolve, LATENCY_MS))
  if (rateLimit && mockCalls.length > rateLimit.limit) throw rateLimit.makeError()
  const override = overrides.find((o) => o.match.test(path) && (!o.method || o.method === method))
  if (override) return override.handler({ method, path, body })
  return structuredClone(defaultRoute(method, path))
}

export const mockApiClient = {
  get: (path: string) => route('GET', path),
  post: (path: string, body?: unknown) => route('POST', path, body),
  put: (path: string, body?: unknown) => route('PUT', path, body),
  patch: (path: string, body?: unknown) => route('PATCH', path, body),
  delete: (path: string) => route('DELETE', path),
  postForm: (path: string) => route('POST', path),
  getBlob: (path: string) => route('GET', path),
}

/** Permission matrices matching the backend's seeded roles (verified against /api/auth/me for each role). */
type ModuleFlags = Record<PermissionAction, boolean>
const ALL: ModuleFlags = { view: true, edit: true, delete: true }
const READ: ModuleFlags = { view: true, edit: false, delete: false }
const NONE: ModuleFlags = { view: false, edit: false, delete: false }
const modules = ['Projects', 'Clients', 'Documents', 'Government', 'Finance', 'Reports', 'Administration', 'Knowledgebase']
function matrix(base: Record<string, ModuleFlags>): Record<string, ModuleFlags> {
  return Object.fromEntries(modules.map((m) => [m, base[m] ?? NONE]))
}

export const PERMISSIONS_BY_ROLE = {
  Administrator: matrix(Object.fromEntries(modules.map((m) => [m, ALL]))),
  Engineer: matrix({ Projects: { view: true, edit: true, delete: false }, Finance: READ, Clients: READ }),
  Viewer: matrix({ Projects: READ, Finance: READ, Clients: READ }),
  'Document Controller': matrix({ Projects: READ, Clients: READ, Documents: { view: true, edit: true, delete: false } }),
}

export function testUser(
  role: keyof typeof PERMISSIONS_BY_ROLE,
  permissions?: Record<string, ModuleFlags> | null,
): CurrentUser {
  return {
    id: 'USR-900',
    name: `${role} Tester`,
    designation: null,
    email: `${role.toLowerCase().replace(/ /g, '.')}@example.com`,
    mobile: null,
    role,
    avatar: 'TT',
    status: 'Active',
    // `null` = "the server sent no permissions" (older session / failed field)
    ...(permissions === null ? {} : { permissions: permissions ?? PERMISSIONS_BY_ROLE[role] }),
  }
}
