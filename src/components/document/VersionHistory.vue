<script setup lang="ts">
import { FileClock } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { DocumentVersion } from '@/types/Document'
import { formatDate } from '@/utils/dateFormatter'

const props = defineProps<{
  versions: DocumentVersion[]
}>()

function isCurrentVersion(version: DocumentVersion): boolean {
  return props.versions[props.versions.length - 1]?.id === version.id
}
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-neutral-800">Version History</h3>
    </template>

    <EmptyState v-if="versions.length === 0" :icon="FileClock" title="No previous versions" />

    <ul v-else class="flex flex-col gap-4">
      <li v-for="version in [...versions].reverse()" :key="version.id" class="flex flex-col gap-1 border-l-2 border-border-light pl-3">
        <div class="flex items-center gap-2">
          <span class="text-sm font-semibold text-neutral-800">{{ version.revision }}</span>
          <StatusBadge v-if="isCurrentVersion(version)" label="Current" variant="success" size="sm" />
        </div>
        <p class="text-xs text-neutral-500">{{ version.uploadedBy }} · {{ formatDate(version.uploadDate) }}</p>
        <p class="text-sm text-neutral-600">{{ version.notes }}</p>
      </li>
    </ul>
  </Card>
</template>
