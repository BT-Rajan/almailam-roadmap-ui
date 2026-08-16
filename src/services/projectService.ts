import { apiClient } from '@/services/httpClient'
import type { PagedResponse, PageParams } from '@/types/Pagination'
import type { Project, ProjectPriority } from '@/types/Project'
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
  params: PageParams & { clientId?: string; status?: string; priority?: string; stage?: string } = {},
): Promise<PagedResponse<Project>> {
  try {
    const query = buildQuery({
      clientId: params.clientId,
      status: params.status,
      priority: params.priority,
      stage: params.stage,
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
  clientId: string
  service: string
  engineerId: string
  priority: ProjectPriority
  startDate: string
  targetDate: string
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

/**
 * Update a project via backend API
 */
async function updateProject(projectId: string, projectData: Partial<Project>): Promise<Project> {
  try {
    return await apiClient.patch<Project>(`/api/projects/${projectId}`, projectData)
  } catch (error) {
    console.error(`Failed to update project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update project')
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

export const projectService = {
  getProjects,
  getProjectsPage,
  getProjectById,
  getProjectsByClient,
  createProject,
  updateProject,
  deleteProject,
}
