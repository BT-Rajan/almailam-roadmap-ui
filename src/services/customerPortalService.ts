import type { CustomerProjectStatus, ProjectDeliverable, ProjectMilestone, ProjectUpdate } from '@/types/CustomerPortal'

// Deliberately not using the shared apiClient (src/services/httpClient.ts):
// that client attaches the staff session's access token to every request
// and logs the staff member out on a 401. The customer portal is a
// completely separate, public-facing auth flow with its own token type --
// mixing the two could incorrectly invalidate an unrelated staff session
// if a customer's access link expires while an admin has the app open in
// another tab.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export class CustomerPortalError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const data = await response.json()
    return data?.detail ?? data?.message ?? `Request failed (${response.status})`
  } catch {
    return `Request failed (${response.status})`
  }
}

interface VerifyResponse {
  accessToken: string
  projectId: string
}

/**
 * Verify a customer's access to a project by project ID and mobile number,
 * via the real backend. Returns the access token to use for subsequent
 * requests, or throws if verification fails.
 */
async function verify(projectId: string, mobileNumber: string): Promise<VerifyResponse> {
  const response = await fetch(`${API_BASE_URL}/api/customer-portal/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ projectId, mobileNumber }),
  })
  if (!response.ok) {
    throw new CustomerPortalError(response.status, await extractErrorMessage(response))
  }
  return (await response.json()) as VerifyResponse
}

interface CustomerProjectView {
  project: CustomerProjectStatus
  milestones: ProjectMilestone[]
  deliverables: ProjectDeliverable[]
  updates: ProjectUpdate[]
}

/**
 * Fetch the full project view (status, milestones, deliverables, updates)
 * for a verified customer session.
 */
async function getProjectView(projectId: string, accessToken: string): Promise<CustomerProjectView> {
  const response = await fetch(`${API_BASE_URL}/api/customer-portal/projects/${projectId}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  if (!response.ok) {
    throw new CustomerPortalError(response.status, await extractErrorMessage(response))
  }
  return (await response.json()) as CustomerProjectView
}

/**
 * Download a deliverable document's stored file. Only documents that
 * have actually been shared (not "Draft") are downloadable -- the
 * backend enforces this regardless of what the frontend requests.
 */
async function downloadDocument(projectId: string, documentId: string, accessToken: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/customer-portal/projects/${projectId}/documents/${documentId}/download`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  if (!response.ok) {
    throw new CustomerPortalError(response.status, await extractErrorMessage(response))
  }
  return await response.blob()
}

export const customerPortalService = {
  verify,
  getProjectView,
  downloadDocument,
}
