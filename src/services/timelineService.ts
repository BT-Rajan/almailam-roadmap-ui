import { apiClient } from '@/services/httpClient'
import type { TimelineEvent } from '@/types/Timeline'

/**
 * Fetch timeline events for a specific project from backend API
 */
async function getTimelineForProject(projectId: string): Promise<TimelineEvent[]> {
  try {
    return await apiClient.get<TimelineEvent[]>(`/api/projects/${projectId}/timeline`)
  } catch (error) {
    console.error(`Failed to fetch timeline for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to fetch timeline')
  }
}

export const timelineService = {
  getTimelineForProject,
}
