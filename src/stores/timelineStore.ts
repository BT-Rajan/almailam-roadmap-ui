import { defineStore } from 'pinia'

import { timelineService } from '@/services/timelineService'
import type { TimelineEvent } from '@/types/Timeline'

interface TimelineStoreState {
  projectId: string | undefined
  events: TimelineEvent[]
  isLoading: boolean
  error: string | undefined
}

export const useTimelineStore = defineStore('timeline', {
  state: (): TimelineStoreState => ({
    projectId: undefined,
    events: [],
    isLoading: false,
    error: undefined,
  }),

  actions: {
    async loadTimelineForProject(projectId: string) {
      this.isLoading = true
      this.error = undefined
      try {
        this.projectId = projectId
        this.events = await timelineService.getTimelineForProject(projectId)
      } catch {
        this.error = 'Unable to load the project timeline. Please try again.'
      } finally {
        this.isLoading = false
      }
    },
  },
})
