<script setup lang="ts">
import { History } from '@lucide/vue'
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import { usePagination } from '@/composables/usePagination'
import type { QuotationAuditEvent, QuotationRevision } from '@/types/Quotation'
import { formatDate, formatDateTime } from '@/utils/dateFormatter'

const props = withDefaults(
  defineProps<{
    revisions: QuotationRevision[]
    events?: QuotationAuditEvent[]
  }>(),
  { events: () => [] },
)

const { t } = useI18n()

// Only the lifecycle events a reader of this history actually cares
// about -- not every row in the underlying audit trail. The trail also
// carries "Quotation created" (redundant with the R0 revision below),
// "Quotation finalized"/"reopened for editing" (internal lock-state
// bookkeeping), and one "Updated <field>" row per edited field on every
// save (redundant with that same save's own revision entry) -- all
// noise here. This list is deliberately an allowlist, not an exclude
// list, so a future, unrelated audit event never silently shows up.
const RELEVANT_EVENT_ACTIONS = new Set([
  'Quotation emailed',
  'Quotation downloaded',
  'Quotation printed',
  'Approval document uploaded',
  'Quotation approved',
  'Quotation rejected',
  'Quotation expired',
  'Quotation moved back to Draft',
])

function isLatestRevision(revision: QuotationRevision): boolean {
  return props.revisions[props.revisions.length - 1]?.id === revision.id
}

type HistoryEntry =
  | { kind: 'revision'; id: string; sortKey: string; revision: QuotationRevision }
  | { kind: 'event'; id: string; sortKey: string; event: QuotationAuditEvent }

const mergedEntries = computed<HistoryEntry[]>(() => {
  const revisionEntries: HistoryEntry[] = props.revisions.map((revision) => ({
    kind: 'revision',
    id: revision.id,
    // Revision dates are date-only (no time of day); normalized to
    // midnight so they compare correctly against events' full
    // timestamps below.
    sortKey: `${revision.date}T00:00:00`,
    revision,
  }))
  const eventEntries: HistoryEntry[] = props.events
    .filter((event) => RELEVANT_EVENT_ACTIONS.has(event.action))
    .map((event) => ({ kind: 'event', id: event.id, sortKey: event.timestamp, event }))
  return [...revisionEntries, ...eventEntries].sort((a, b) => b.sortKey.localeCompare(a.sortKey))
})

const { currentPage, pageSize, totalItems, totalPages, startIndex, endIndex, goToPage, setPageSize, resetPage } =
  usePagination(() => mergedEntries.value.length)
const pagedEntries = computed(() => mergedEntries.value.slice(startIndex.value, endIndex.value))
watch([() => props.revisions, () => props.events], () => resetPage())
</script>

<template>
  <Card :padded="false">
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('project.quotationHistory.title') }}</h3>
    </template>

    <EmptyState v-if="mergedEntries.length === 0" :icon="History" :title="t('project.revisionHistory.emptyTitle')" class="p-5" />

    <template v-else>
      <ul class="flex flex-col gap-4 p-5">
        <li
          v-for="entry in pagedEntries"
          :key="`${entry.kind}-${entry.id}`"
          class="flex flex-col gap-1 border-s-2 border-border-light ps-3"
        >
          <template v-if="entry.kind === 'revision'">
            <div class="flex items-center gap-2">
              <span class="text-sm font-semibold text-text-primary">{{ entry.revision.revision }}</span>
              <StatusBadge v-if="isLatestRevision(entry.revision)" :label="t('project.revisionHistory.current')" variant="success" size="sm" />
            </div>
            <p class="text-xs text-text-muted">{{ entry.revision.changedBy }} · {{ formatDate(entry.revision.date) }}</p>
            <p class="text-sm text-text-secondary">{{ entry.revision.summary }}</p>
          </template>
          <template v-else>
            <p class="text-sm font-semibold text-text-primary">{{ entry.event.action }}</p>
            <p class="text-xs text-text-muted">{{ entry.event.user }} · {{ formatDateTime(entry.event.timestamp) }}</p>
            <p v-if="entry.event.newValue" class="text-sm text-text-secondary">{{ entry.event.newValue }}</p>
            <p v-if="entry.event.reason" class="text-xs italic text-text-muted">{{ t('project.quotationHistory.reason', { reason: entry.event.reason }) }}</p>
          </template>
        </li>
      </ul>
      <TablePagination
        :current-page="currentPage"
        :total-pages="totalPages"
        :total-items="totalItems"
        :start-index="startIndex"
        :end-index="endIndex"
        :page-size="pageSize"
        @page-change="goToPage"
        @page-size-change="setPageSize"
      />
    </template>
  </Card>
</template>
