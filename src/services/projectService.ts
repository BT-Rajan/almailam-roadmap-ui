import { apiClient } from '@/services/httpClient'
import type { Project } from '@/types/Project'

/**
 * Fetch all projects from backend API
 */
async function getProjects(): Promise<Project[]> {
  try {
    return await apiClient.get<Project[]>('/api/projects')
  } catch (error) {
    console.error('Failed to fetch projects:', error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch projects')
  }
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
  try {
    return await apiClient.get<Project[]>(`/api/clients/${clientId}/projects`)
  } catch (error) {
    console.error(`Failed to fetch projects for client ${clientId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch projects')
  }
}

/**
 * Create a new project via backend API
 */
async function createProject(projectData: Partial<Project>): Promise<Project> {
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
  getProjectById,
  getProjectsByClient,
  createProject,
  updateProject,
  deleteProject,
}
