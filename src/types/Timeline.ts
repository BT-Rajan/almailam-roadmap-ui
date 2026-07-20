export type TimelineEventType = 'stage' | 'document' | 'quotation' | 'submission' | 'milestone' | 'task' | 'note'

export type TimelineEventStatus = 'completed' | 'in-progress' | 'upcoming'

export interface TimelineEvent {
  id: string
  projectId: string
  type: TimelineEventType
  title: string
  description?: string
  date: string
  status: TimelineEventStatus
  user?: string
}
