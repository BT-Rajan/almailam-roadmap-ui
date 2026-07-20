<script setup lang="ts">
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { FinancialAuditEvent } from '@/types/Payment'

interface Props {
  events: FinancialAuditEvent[]
}

const props = defineProps<Props>()

const sortedEvents = computed(() => [...props.events].sort((a, b) => b.timestamp.localeCompare(a.timestamp)))

function formatTimestamp(timestamp: string): string {
  return new Date(timestamp).toLocaleString('en-AE', { dateStyle: 'medium', timeStyle: 'short' })
}
</script>

<template>
  <Card :padded="false">
    <template #header>
      <h3 class="text-sm font-semibold text-neutral-800">Payment History</h3>
    </template>

    <EmptyState v-if="sortedEvents.length === 0" title="No financial events yet" description="Agreement creation, payments, refunds, and adjustments will be logged here." />

    <ul v-else class="divide-y divide-border-light">
      <li v-for="event in sortedEvents" :key="event.id" class="flex flex-col gap-1 px-4 py-3">
        <div class="flex items-center justify-between gap-3">
          <p class="text-sm font-medium text-neutral-800">{{ event.eventType }}</p>
          <p class="text-xs text-neutral-400">{{ formatTimestamp(event.timestamp) }}</p>
        </div>
        <p class="text-xs text-neutral-500">By {{ event.user }}</p>
        <p v-if="event.previousValue || event.newValue" class="text-xs text-neutral-600">
          <span v-if="event.previousValue">{{ event.previousValue }} → </span>
          <span v-if="event.newValue">{{ event.newValue }}</span>
        </p>
        <p v-if="event.reason" class="text-xs italic text-neutral-500">Reason: {{ event.reason }}</p>
      </li>
    </ul>
  </Card>
</template>
