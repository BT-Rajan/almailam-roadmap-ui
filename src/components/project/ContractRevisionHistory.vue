<script setup lang="ts">
import { History } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ContractRevision } from '@/types/Contract'
import { formatDate } from '@/utils/dateFormatter'

const props = defineProps<{
  revisions: ContractRevision[]
}>()

function isLatestRevision(revision: ContractRevision): boolean {
  return props.revisions[props.revisions.length - 1]?.id === revision.id
}
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-neutral-800">Revision History</h3>
    </template>

    <EmptyState v-if="revisions.length === 0" :icon="History" title="No revisions recorded" />

    <ul v-else class="flex flex-col gap-4">
      <li
        v-for="revision in [...revisions].reverse()"
        :key="revision.id"
        class="flex flex-col gap-1 border-l-2 border-border-light pl-3"
      >
        <div class="flex items-center gap-2">
          <span class="text-sm font-semibold text-neutral-800">{{ revision.revision }}</span>
          <StatusBadge v-if="isLatestRevision(revision)" label="Current" variant="success" size="sm" />
        </div>
        <p class="text-xs text-neutral-500">{{ revision.changedBy }} · {{ formatDate(revision.date) }}</p>
        <p class="text-sm text-neutral-600">{{ revision.summary }}</p>
      </li>
    </ul>
  </Card>
</template>
