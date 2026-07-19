import { PROJECTS } from '@/mock/projects'
import type { Project } from '@/types/Project'
import { simulateNetworkDelay } from '@/utils/mockDelay'

async function getProjects(): Promise<Project[]> {
  await simulateNetworkDelay()
  return [...PROJECTS]
}

async function getProjectById(projectId: string): Promise<Project | undefined> {
  await simulateNetworkDelay()
  return PROJECTS.find((project) => project.id === projectId)
}

async function getProjectsByClient(clientId: string): Promise<Project[]> {
  await simulateNetworkDelay()
  return PROJECTS.filter((project) => project.clientId === clientId)
}

export const projectService = {
  getProjects,
  getProjectById,
  getProjectsByClient,
}
