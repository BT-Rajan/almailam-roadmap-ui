<script setup lang="ts">
import { History } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ContractAuditEvent, ContractRevision } from '@/types/Contract'
import { formatDate, formatDateTime } from '@/utils/dateFormatter'

const props = withDefaults(
  defineProps<{
    revisions: ContractRevision[]
    auditEvents?: ContractAuditEvent[]
  }>(),
  { auditEvents: () => [] },
)

const { t } = useI18n()

// Document activity worth surfacing alongside content revisions --
// downloads, prints, emails, and the moment a contract was signed --
// so staff can see who sent or signed what and when without leaving
// this panel. Every other audit-log row (creation, reopen, etc.) is
// left off; it's implicit in the revision entries themselves. Mirrors
// QuotationRevisionHistory.vue's own copy of this exactly.
const ACTIVITY_LABEL_KEYS: Record<string, string> = {
  'Document downloaded': 'project.revisionHistory.documentDownloaded',
  'Document printed': 'project.revisionHistory.documentPrinted',
  'Document emailed': 'project.revisionHistory.documentEmailed',
}

interface HistoryEntry {
  id: string
  date: string
  title: string
  byline: string
  description?: string
  isCurrentRevision: boolean
}

const entries = computed<HistoryEntry[]>(() => {
  const revisionEntries: HistoryEntry[] = props.revisions.map((revision) => ({
    id: `revision-${revision.id}`,
    date: revision.date,
    title: revision.revision,
    byline: `${revision.changedBy} · ${formatDate(revision.date)}`,
    description: revision.summary,
    isCurrentRevision: revision.id === props.revisions[props.revisions.length - 1]?.id,
  }))

  const activityEntries: HistoryEntry[] = props.auditEvents
    .filter((event) => event.action in ACTIVITY_LABEL_KEYS || (event.action === 'Status changed' && event.newValue === 'Signed'))
    .map((event) => ({
      id: `event-${event.id}`,
      date: event.timestamp,
      title: event.action === 'Status changed' ? t('project.revisionHistory.contractSigned') : t(ACTIVITY_LABEL_KEYS[event.action]),
      byline: `${event.user} · ${formatDateTime(event.timestamp)}`,
      isCurrentRevision: false,
    }))

  return [...revisionEntries, ...activityEntries].sort((a, b) => b.date.localeCompare(a.date))
})
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('project.revisionHistory.title') }}</h3>
    </template>

    <EmptyState v-if="entries.length === 0" :icon="History" :title="t('project.revisionHistory.emptyTitle')" />

    <ul v-else class="flex flex-col gap-4">
      <li
        v-for="entry in entries"
        :key="entry.id"
        class="flex flex-col gap-1 border-s-2 border-border-light ps-3"
      >
        <div class="flex items-center gap-2">
          <span class="text-sm font-semibold text-text-primary">{{ entry.title }}</span>
          <StatusBadge v-if="entry.isCurrentRevision" :label="t('project.revisionHistory.current')" variant="success" size="sm" />
        </div>
        <p class="text-xs text-text-muted">{{ entry.byline }}</p>
        <p v-if="entry.description" class="text-sm text-text-secondary">{{ entry.description }}</p>
      </li>
    </ul>
  </Card>
</template>
