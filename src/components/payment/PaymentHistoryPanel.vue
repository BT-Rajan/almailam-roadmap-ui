<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { FinancialAuditEvent } from '@/types/Payment'

interface Props {
  events: FinancialAuditEvent[]
}

const props = defineProps<Props>()

const { t } = useI18n()

const sortedEvents = computed(() => [...props.events].sort((a, b) => b.timestamp.localeCompare(a.timestamp)))

function formatTimestamp(timestamp: string): string {
  return new Date(timestamp).toLocaleString('en-AE', { dateStyle: 'medium', timeStyle: 'short' })
}
</script>

<template>
  <Card :padded="false">
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('payment.historyPanel.title') }}</h3>
    </template>

    <EmptyState v-if="sortedEvents.length === 0" :title="t('payment.historyPanel.emptyTitle')" :description="t('payment.historyPanel.emptyDescription')" />

    <ul v-else class="divide-y divide-border-light">
      <li v-for="event in sortedEvents" :key="event.id" class="flex flex-col gap-1 px-4 py-3">
        <div class="flex items-center justify-between gap-3">
          <p class="text-sm font-medium text-text-primary">{{ event.action }}</p>
          <p class="text-xs text-text-muted">{{ formatTimestamp(event.timestamp) }}</p>
        </div>
        <p class="text-xs text-text-muted">{{ t('payment.historyPanel.by', { user: event.user }) }}</p>
        <p v-if="event.previousValue || event.newValue" class="text-xs text-text-secondary">
          <span v-if="event.previousValue">{{ event.previousValue }} → </span>
          <span v-if="event.newValue">{{ event.newValue }}</span>
        </p>
        <p v-if="event.reason" class="text-xs italic text-text-muted">{{ t('payment.historyPanel.reason', { reason: event.reason }) }}</p>
      </li>
    </ul>
  </Card>
</template>
