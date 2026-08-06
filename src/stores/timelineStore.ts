import { defineStore } from 'pinia'

import { timelineService } from '@/services/timelineService'
import type { TimelineEventInput } from '@/services/timelineService'
import type { TimelineEvent } from '@/types/Timeline'

interface TimelineStoreState {
  projectId: string | undefined
  events: TimelineEvent[]
  isLoading: boolean
  error: string | undefined
  isMutating: boolean
  mutationError: string | undefined
}

export const useTimelineStore = defineStore('timeline', {
  state: (): TimelineStoreState => ({
    projectId: undefined,
    events: [],
    isLoading: false,
    error: undefined,
    isMutating: false,
    mutationError: undefined,
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

    addEvent(event: TimelineEvent) {
      this.events = [...this.events, event].sort((a, b) => a.date.localeCompare(b.date))
    },

    // Persists a new timeline entry via the backend API. Prefer this over
    // addEvent() above, which only mutates local state -- that was the
    // cause of a real bug: "Add Update" entries on a project's Timeline
    // and Activity tabs appeared to save but were lost on refresh, and
    // the tabs themselves failed to load at all since there was no
    // backend for GET /api/projects/{id}/timeline either.
    async createEvent(projectId: string, input: TimelineEventInput) {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const event = await timelineService.createEvent(projectId, input)
        this.events = [...this.events, event].sort((a, b) => a.date.localeCompare(b.date))
        return event
      } catch {
        this.mutationError = 'Unable to save the timeline entry. Please try again.'
        return undefined
      } finally {
        this.isMutating = false
      }
    },

    updateEvent(eventId: string, updates: Partial<Pick<TimelineEvent, 'title' | 'description' | 'status' | 'date'>>) {
      const event = this.events.find((item) => item.id === eventId)
      if (!event) return
      Object.assign(event, updates)
      this.events = [...this.events].sort((a, b) => a.date.localeCompare(b.date))
    },

    // Persists an update to a timeline entry via the backend API. Prefer
    // this over updateEvent() above, which only mutates local state.
    async saveEventUpdate(
      projectId: string,
      eventId: string,
      updates: Partial<Pick<TimelineEvent, 'title' | 'description' | 'status' | 'date'>>,
    ) {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const updated = await timelineService.updateEvent(projectId, eventId, updates)
        this.events = [...this.events.filter((item) => item.id !== eventId), updated].sort((a, b) =>
          a.date.localeCompare(b.date),
        )
        return updated
      } catch {
        this.mutationError = 'Unable to save the timeline entry. Please try again.'
        return undefined
      } finally {
        this.isMutating = false
      }
    },
  },
})
