import { CircleDot, Clock, FileText, Flag, Landmark, ListChecks, MessageSquare, Receipt } from '@lucide/vue'
import type { Component } from 'vue'

import type { BadgeVariant } from '@/types/Ui'
import type { TimelineEventStatus, TimelineEventType } from '@/types/Timeline'

const TYPE_ICONS: Record<TimelineEventType, Component> = {
  stage: CircleDot,
  document: FileText,
  quotation: Receipt,
  submission: Landmark,
  milestone: Flag,
  task: ListChecks,
  note: MessageSquare,
}

const STATUS_VARIANTS: Record<TimelineEventStatus, BadgeVariant> = {
  completed: 'success',
  'in-progress': 'warning',
  upcoming: 'neutral',
}

const STATUS_LABELS: Record<TimelineEventStatus, string> = {
  completed: 'Completed',
  'in-progress': 'In Progress',
  upcoming: 'Upcoming',
}

export function getTimelineStatusLabel(status: TimelineEventStatus): string {
  return STATUS_LABELS[status]
}

export function getTimelineEventIcon(type: TimelineEventType): Component {
  return TYPE_ICONS[type] ?? Clock
}

export function getTimelineStatusVariant(status: TimelineEventStatus): BadgeVariant {
  return STATUS_VARIANTS[status]
}
