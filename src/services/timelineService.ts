import { apiClient } from '@/services/httpClient'
import type { TimelineEvent, TimelineEventStatus } from '@/types/Timeline'

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

export interface TimelineEventInput {
  title: string
  description?: string
  date: string
  status: TimelineEventStatus
}

/**
 * Record a new timeline entry for a project via backend API
 */
async function createEvent(projectId: string, input: TimelineEventInput): Promise<TimelineEvent> {
  try {
    return await apiClient.post<TimelineEvent>(`/api/projects/${projectId}/timeline`, input)
  } catch (error) {
    console.error(`Failed to create timeline entry for project ${projectId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to create timeline entry')
  }
}

/**
 * Update a timeline entry via backend API
 */
async function updateEvent(
  projectId: string,
  eventId: string,
  input: Partial<TimelineEventInput>,
): Promise<TimelineEvent> {
  try {
    return await apiClient.patch<TimelineEvent>(`/api/projects/${projectId}/timeline/${eventId}`, input)
  } catch (error) {
    console.error(`Failed to update timeline entry ${eventId}:`, error)
    throw new Error(error instanceof Error ? error.message : 'Failed to update timeline entry')
  }
}

export const timelineService = {
  getTimelineForProject,
  createEvent,
  updateEvent,
}
