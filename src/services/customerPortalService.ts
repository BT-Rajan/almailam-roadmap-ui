import { apiClient } from '@/services/httpClient'
import { useAuthStore } from '@/stores/authStore'
import type {
  CustomerProjectStatus,
  ProjectActivityGroup,
  ProjectBudget,
  ProjectDeliverable,
  ProjectMilestone,
  ProjectUpdate,
} from '@/types/CustomerPortal'

// Now the same authenticated apiClient (src/services/httpClient.ts) every
// other service uses -- the Customer Portal authenticates through the
// shared authStore/access-token session like the staff app and Site
// Engineer Portal, not a separate bespoke token type, so there's no
// longer a reason to keep it on its own raw-fetch plumbing.

export interface CustomerProjectOption {
  projectId: string
  projectName: string
}

/** Every project belonging to the logged-in customer's client record. */
async function listMyProjects(): Promise<CustomerProjectOption[]> {
  return apiClient.get<CustomerProjectOption[]>('/api/customer-portal/projects')
}

interface CustomerProjectView {
  project: CustomerProjectStatus
  milestones: ProjectMilestone[]
  deliverables: ProjectDeliverable[]
  updates: ProjectUpdate[]
  activities: ProjectActivityGroup[]
  budget: ProjectBudget | null
}

/** Fetch the full project view (status, milestones, deliverables, updates). */
async function getProjectView(projectId: string): Promise<CustomerProjectView> {
  return apiClient.get<CustomerProjectView>(`/api/customer-portal/projects/${projectId}`)
}

/**
 * Download a deliverable document's stored file. Only documents that
 * have actually been shared (not "Draft") are downloadable -- the
 * backend enforces this regardless of what the frontend requests.
 *
 * apiClient.get parses JSON, so a raw authenticated fetch is used here
 * instead -- same 401-retry-once handling as the rest of apiClient.
 */
async function downloadDocument(projectId: string, documentId: string): Promise<Blob> {
  const authStore = useAuthStore()
  const path = `/api/customer-portal/projects/${projectId}/documents/${documentId}/download`

  const doRequest = () =>
    fetch(path, {
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
    })

  let response = await doRequest()
  if (response.status === 401) {
    const refreshed = await authStore.tryRefresh()
    if (refreshed) response = await doRequest()
  }
  if (!response.ok) {
    throw new Error(`Download failed with status ${response.status}`)
  }
  return await response.blob()
}

export const customerPortalService = {
  listMyProjects,
  getProjectView,
  downloadDocument,
}
