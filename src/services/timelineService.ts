import { TIMELINE_EVENTS } from '@/mock/timelineEvents'
import type { TimelineEvent } from '@/types/Timeline'
import { simulateNetworkDelay } from '@/utils/mockDelay'

async function getTimelineForProject(projectId: string): Promise<TimelineEvent[]> {
  await simulateNetworkDelay()
  return TIMELINE_EVENTS.filter((event) => event.projectId === projectId).sort((a, b) =>
    a.date.localeCompare(b.date),
  )
}

export const timelineService = {
  getTimelineForProject,
}
