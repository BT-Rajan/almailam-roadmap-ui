import { apiClient } from '@/services/httpClient'
import { useAuthStore } from '@/stores/authStore'
import type { PagedResponse, PageParams } from '@/types/Pagination'
import type { AddServicesInput, HandoverStatus, Project, ProjectPriority, ScopeOfWork, SelectedPermit, SelectedSupervisionActivity, StageEligibility } from '@/types/Project'
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
  params: PageParams & {
    clientId?: string
    status?: string
    priority?: string
    stage?: string
    engineerId?: string
    /** true to browse soft-deleted projects instead of active ones -- see restoreProject. */
    deleted?: boolean
  } = {},
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
      deleted: params.deleted ? 'true' : undefined,
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

export interface ProjectCreateInput {
  projectName: string
  description?: string
  // The project/plot address -- fills a Quotation/Contract document
  // template's address placeholder (see document_template_service.
  // MERGE_FIELD_CATALOG). Distinct from any of the client's own
  // addresses.
  siteAddress?: string
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
  // Permits this project needs to apply for, picked in the unified
  // ServicePickerDialog -- becomes the Permit track's own trackable
  // rows.
  selectedPermits?: { permitId: string; permitName: string }[]
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
  siteAddress?: string
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
 * Adds more billable Design and/or Supervision activities to an
 * existing project -- see AddServicesInput. Only genuinely new
 * activities are inserted server-side; sending one already selected is
 * harmless (silently ignored), not an error.
 */
async function addServices(projectId: string, input: AddServicesInput): Promise<Project> {
  try {
    return await apiClient.post<Project>(`/api/projects/${projectId}/services`, input)
  } catch (error) {
    console.error(`Failed to add services to project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to add services')
  }
}

/**
 * One entry per structurally-reachable next stage for this project
 * right now, each with whether it's actually eligible and, if not, why
 * -- backs the Stage dialog's proactive validation (see
 * project_service.get_stage_eligibility, the single source of truth
 * this mirrors rather than duplicating the exit-criteria rules here).
 */
async function getStageEligibility(projectId: string): Promise<StageEligibility[]> {
  try {
    return await apiClient.get<StageEligibility[]>(`/api/projects/${projectId}/stage-eligibility`)
  } catch (error) {
    console.error(`Failed to fetch stage eligibility for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch stage eligibility')
  }
}

/**
 * Directly closes a Design activity (Complete or Cancelled) regardless
 * of its linked tasks' state -- the user always has full manual
 * control, on top of the auto-close that happens when every linked
 * task is completed (see taskService.setTaskStatus).
 */
async function closeDesignActivity(
  projectId: string, activityId: string, status: 'Complete' | 'Cancelled',
): Promise<SelectedServiceActivity> {
  try {
    return await apiClient.post<SelectedServiceActivity>(
      `/api/projects/${projectId}/design-activities/${activityId}/close`, { status },
    )
  } catch (error) {
    console.error(`Failed to close design activity ${activityId} on project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to close design activity')
  }
}

/** Undoes a close (manual or auto-derived) regardless of linked task state. */
async function reopenDesignActivity(projectId: string, activityId: string): Promise<SelectedServiceActivity> {
  try {
    return await apiClient.post<SelectedServiceActivity>(
      `/api/projects/${projectId}/design-activities/${activityId}/reopen`, {},
    )
  } catch (error) {
    console.error(`Failed to reopen design activity ${activityId} on project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to reopen design activity')
  }
}

/**
 * Directly sets a Permit's status -- Permits have no sub-tasks, so
 * (unlike Design activities) this is the only way any of a permit's
 * status transitions happen; 'Eligible' isn't settable this way, it's
 * computed once its prerequisite Design activities are all Complete.
 */
async function setPermitStatus(
  projectId: string, permitId: string, status: 'In Progress' | 'Complete' | 'Cancelled',
): Promise<SelectedPermit> {
  try {
    return await apiClient.post<SelectedPermit>(`/api/projects/${projectId}/permits/${permitId}/status`, { status })
  } catch (error) {
    console.error(`Failed to set status for permit ${permitId} on project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update permit status')
  }
}

/**
 * Directly sets a Supervision activity's status -- same reasoning as
 * setPermitStatus: no sub-tasks, the user sets this based on their own
 * read of site-engineer reports. 'Eligible' isn't settable this way.
 */
async function setSupervisionStatus(
  projectId: string, activityId: string, status: 'In Progress' | 'Complete' | 'Cancelled',
): Promise<SelectedSupervisionActivity> {
  try {
    return await apiClient.post<SelectedSupervisionActivity>(
      `/api/projects/${projectId}/supervision-activities/${activityId}/status`, { status },
    )
  } catch (error) {
    console.error(`Failed to set status for supervision activity ${activityId} on project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update supervision activity status')
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
 * Delete (soft-delete) a project via backend API -- recoverable via
 * restoreProject below.
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
 * Restore a soft-deleted project via backend API -- undoes deleteProject.
 */
async function restoreProject(projectId: string): Promise<Project> {
  try {
    return await apiClient.post<Project>(`/api/projects/${projectId}/restore`, {})
  } catch (error) {
    console.error(`Failed to restore project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to restore project')
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
 * Save the Requirement stage's scope-of-work text, writing a new revision.
 * Clears any existing client confirmation -- see project_service.
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
 * Confirms the Requirement stage's scope of work is finalized -- the
 * sole approval this stage requires -- and, on success, moves the
 * project straight to Quotation. A direct staff action with no
 * client-facing artifact involved. See
 * project_service.confirm_requirement_scope.
 */
async function confirmRequirementScope(projectId: string): Promise<ScopeOfWork> {
  try {
    return await apiClient.post<ScopeOfWork>(`/api/projects/${projectId}/requirement/confirm-scope`, {})
  } catch (error) {
    console.error(`Failed to confirm scope of work for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to confirm scope of work')
  }
}

/**
 * The project's hand-over readiness: whether Administrators have been
 * notified it's ready, and the generated hand-over checklist (empty
 * until every Design/Permit/Supervision item is closed and payment is
 * fully settled). See project_service.try_complete_project / GET
 * /{project_no}/handover.
 */
async function getHandoverStatus(projectId: string): Promise<HandoverStatus> {
  try {
    return await apiClient.get<HandoverStatus>(`/api/projects/${projectId}/handover`)
  } catch (error) {
    console.error(`Failed to load hand-over status for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to load hand-over status')
  }
}

/**
 * Re-notifies Administrators the project is ready for hand-over.
 * Normally notified automatically once the project first becomes ready
 * (try_complete_project); this is the manual re-notify path. See
 * project_service.notify_handover_ready.
 */
async function notifyHandoverReady(projectId: string): Promise<HandoverStatus> {
  try {
    return await apiClient.post<HandoverStatus>(`/api/projects/${projectId}/handover/notify-ready`, {})
  } catch (error) {
    console.error(`Failed to notify hand-over readiness for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to notify hand-over readiness')
  }
}

/**
 * Records the client's hand-over acknowledgment -- a scan of their
 * physically signed copy, uploaded here. On success the project's
 * status flips to Completed. See project_service.
 * confirm_project_handover.
 */
async function confirmProjectHandover(projectId: string, file: File): Promise<Project> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    return await apiClient.postForm<Project>(`/api/projects/${projectId}/handover/confirm`, formData)
  } catch (error) {
    console.error(`Failed to confirm hand-over for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to confirm hand-over')
  }
}

export const projectService = {
  getProjects,
  getProjectsPage,
  getProjectById,
  createProject,
  updateProject,
  setStage,
  getStageEligibility,
  closeDesignActivity,
  reopenDesignActivity,
  setPermitStatus,
  setSupervisionStatus,
  addServices,
  setStatus,
  deleteProject,
  restoreProject,
  saveScopeOfWork,
  confirmRequirementScope,
  getHandoverStatus,
  notifyHandoverReady,
  confirmProjectHandover,
}
