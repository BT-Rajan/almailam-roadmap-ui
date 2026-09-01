import { apiClient } from '@/services/httpClient'
import { useAuthStore } from '@/stores/authStore'
import type { PagedResponse, PageParams } from '@/types/Pagination'
import type { Project, ProjectPriority, ScopeOfWork, SelectedSupervisionActivity } from '@/types/Project'
import type { SelectedServiceActivity } from '@/types/ServiceCatalog'
import { fetchAllPages } from '@/utils/fetchAllPages'

function buildQuery(params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') query.set(key, String(value))
  }
  const queryString = query.toString()
  return queryString ? `?${queryString}` : ''
}

/**
 * Fetch a single page of projects from the backend API. Prefer this over
 * getProjects() for any UI that displays/paginates the list directly, since
 * it only asks the server for one page at a time instead of the whole table.
 */
async function getProjectsPage(
  params: PageParams & { clientId?: string; status?: string; priority?: string; stage?: string; engineerId?: string } = {},
): Promise<PagedResponse<Project>> {
  try {
    const query = buildQuery({
      clientId: params.clientId,
      status: params.status,
      priority: params.priority,
      stage: params.stage,
      engineerId: params.engineerId,
      search: params.search,
      sort: params.sort,
      page: params.page,
      pageSize: params.pageSize,
    })
    return await apiClient.get<PagedResponse<Project>>(`/api/projects${query}`)
  } catch (error) {
    console.error('Failed to fetch projects:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch projects')
  }
}

/**
 * Fetch every project from the backend API as a flat array. Internally
 * walks the paginated endpoint page by page (each request is still bounded
 * server-side) so existing callers that need the full list -- e.g. cross-
 * reference lookups like resolving a project's name elsewhere in the app --
 * don't have to change.
 */
async function getProjects(): Promise<Project[]> {
  return fetchAllPages<Project>((page, pageSize) => getProjectsPage({ page, pageSize }))
}

/**
 * Fetch a specific project by ID from backend API
 */
async function getProjectById(projectId: string): Promise<Project | undefined> {
  try {
    return await apiClient.get<Project>(`/api/projects/${projectId}`)
  } catch (error) {
    console.error(`Failed to fetch project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch project')
  }
}

/**
 * Fetch projects for a specific client from backend API
 */
async function getProjectsByClient(clientId: string): Promise<Project[]> {
  return fetchAllPages<Project>((page, pageSize) => getProjectsPage({ clientId, page, pageSize }))
}

export interface ProjectCreateInput {
  projectName: string
  description?: string
  clientId: string
  service: string
  engineerId: string
  priority: ProjectPriority
  startDate: string
  targetDate: string
  // Optional granular breakdown from the service picker. Sent alongside
  // `service` (which stays the comma-joined summary) so a backend that
  // hasn't been extended to store it yet can just ignore these two fields
  // without the request failing.
  selectedActivities?: SelectedServiceActivity[]
  serviceTotal?: number
  // Supervision activities picked in the same unified service picker,
  // each carrying its own start/end window. Optional -- a project can
  // pick no Supervision work at all, and an older/unaware backend can
  // just ignore the field. supervisionStartDate/supervisionEndDate are
  // the overall engagement window (required once any activity is
  // selected -- enforced server-side).
  selectedSupervisionActivities?: SelectedSupervisionActivity[]
  supervisionStartDate?: string
  supervisionEndDate?: string
  // Permits the client already holds -- sent through so the backend can
  // persist them as mandatory-upload requirements on the project. Optional
  // for the same reason as selectedActivities above.
  requiredPermitDocuments?: string[]
}

/**
 * Create a new project via backend API
 */
async function createProject(projectData: ProjectCreateInput): Promise<Project> {
  try {
    return await apiClient.post<Project>('/api/projects', projectData)
  } catch (error) {
    console.error('Failed to create project:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create project')
  }
}

export interface ProjectUpdateInput {
  projectName?: string
  description?: string
  service?: string
  engineerId?: string
  priority?: ProjectPriority
  // progress deliberately not here -- it's derived from current_stage
  // server-side (see project_service.recompute_progress), not settable
  // directly.
  targetDate?: string
}

/**
 * Update a project's core details via backend API. For stage/status
 * changes, use setStage()/setStatus() below instead -- those go through
 * dedicated endpoints with transition validation and reason capture.
 */
async function updateProject(projectId: string, projectData: ProjectUpdateInput): Promise<Project> {
  try {
    return await apiClient.patch<Project>(`/api/projects/${projectId}`, projectData)
  } catch (error) {
    console.error(`Failed to update project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update project')
  }
}

/**
 * Advance/change a project's workflow stage. `reason` is required for
 * some transitions (enforced server-side, see PROJECT_STAGE_STATUSES_
 * REQUIRING_REASON and the Government Submission->Design reopen case)
 * -- always pass it through when the user provided one.
 */
async function setStage(projectId: string, currentStage: string, reason?: string): Promise<Project> {
  try {
    return await apiClient.patch<Project>(`/api/projects/${projectId}/stage`, { currentStage, reason })
  } catch (error) {
    console.error(`Failed to change stage for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to change project stage')
  }
}

/**
 * Change a project's operational status (Active/On Hold/Cancelled).
 * `reason` is required for some transitions (On Hold, Cancelled, and
 * reopening a Cancelled project) -- enforced server-side.
 */
async function setStatus(projectId: string, status: string, reason?: string): Promise<Project> {
  try {
    return await apiClient.patch<Project>(`/api/projects/${projectId}/status`, { status, reason })
  } catch (error) {
    console.error(`Failed to change status for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to change project status')
  }
}

/**
 * Delete a project via backend API
 */
async function deleteProject(projectId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/projects/${projectId}`)
  } catch (error) {
    console.error(`Failed to delete project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to delete project')
  }
}

/**
 * Shared multipart upload helper -- same 401-retry-once + error-shape
 * handling as documentService's uploadDocument, since apiClient always
 * JSON-encodes its body and can't be used for file uploads.
 */
async function uploadMultipart<T>(path: string, formData: FormData): Promise<T> {
  const authStore = useAuthStore()
  const doRequest = () =>
    fetch(path, {
      method: 'POST',
      headers: authStore.accessToken ? { Authorization: `Bearer ${authStore.accessToken}` } : undefined,
      credentials: 'include',
      body: formData,
    })

  let response = await doRequest()
  if (response.status === 401) {
    const refreshed = await authStore.tryRefresh()
    if (refreshed) response = await doRequest()
  }
  if (!response.ok) {
    const data = await response.json().catch(() => undefined)
    throw new Error(data?.error ?? data?.detail ?? data?.message ?? `Upload failed with status ${response.status}`)
  }
  return (await response.json()) as T
}

/**
 * Fetch the Requirement stage's scope-of-work text, approval status, and
 * revision history for a project via backend API.
 */
async function getScopeOfWork(projectId: string): Promise<ScopeOfWork> {
  try {
    return await apiClient.get<ScopeOfWork>(`/api/projects/${projectId}/scope-of-work`)
  } catch (error) {
    console.error(`Failed to fetch scope of work for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch scope of work')
  }
}

/**
 * Save the Requirement stage's scope-of-work text, writing a new revision.
 * Reopens an already-approved scope back to Draft -- see project_service.
 * save_scope_of_work.
 */
async function saveScopeOfWork(
  projectId: string,
  scopeText: string,
  summary: string | undefined,
  file: File | undefined,
): Promise<ScopeOfWork> {
  try {
    const formData = new FormData()
    formData.append('scopeText', scopeText)
    if (summary) formData.append('summary', summary)
    if (file) formData.append('file', file)
    return await uploadMultipart<ScopeOfWork>(`/api/projects/${projectId}/scope-of-work`, formData)
  } catch (error) {
    console.error(`Failed to save scope of work for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to save scope of work')
  }
}

/**
 * Internal approval of the scope of work -- once approved, the backend
 * automatically moves the project on to the Quotation stage (assuming its
 * other exit criteria, e.g. client identification, are already met).
 */
async function approveScopeOfWork(projectId: string): Promise<Project> {
  try {
    return await apiClient.post<Project>(`/api/projects/${projectId}/scope-of-work/approve`, {})
  } catch (error) {
    console.error(`Failed to approve scope of work for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to approve scope of work')
  }
}

/**
 * Download the document attached to one scope-of-work revision.
 */
async function downloadScopeRevisionDocument(projectId: string, revisionId: string): Promise<Blob> {
  const authStore = useAuthStore()
  const doRequest = () =>
    fetch(`/api/projects/${projectId}/scope-of-work/${revisionId}/document`, {
      method: 'GET',
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

export const projectService = {
  getProjects,
  getProjectsPage,
  getProjectById,
  getProjectsByClient,
  createProject,
  updateProject,
  setStage,
  setStatus,
  deleteProject,
  getScopeOfWork,
  saveScopeOfWork,
  approveScopeOfWork,
  downloadScopeRevisionDocument,
}
