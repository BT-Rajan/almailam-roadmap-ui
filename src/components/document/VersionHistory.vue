<script setup lang="ts">
import { Download, FileClock } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { DocumentVersion } from '@/types/Document'
import { formatDate } from '@/utils/dateFormatter'

const props = defineProps<{
  versions: DocumentVersion[]
}>()

defineEmits<{
  download: [version: DocumentVersion]
}>()

const { t } = useI18n()

function isCurrentVersion(version: DocumentVersion): boolean {
  return props.versions[props.versions.length - 1]?.id === version.id
}
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('document.versionHistory.title') }}</h3>
    </template>

    <EmptyState v-if="versions.length === 0" :icon="FileClock" :title="t('document.versionHistory.emptyTitle')" />

    <ul v-else class="flex flex-col gap-4">
      <li v-for="version in [...versions].reverse()" :key="version.id" class="flex flex-col gap-1 border-l-2 border-border-light pl-3">
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <span class="text-sm font-semibold text-text-primary">{{ version.revision }}</span>
            <StatusBadge v-if="isCurrentVersion(version)" :label="t('document.versionHistory.current')" variant="success" size="sm" />
          </div>
          <IconButton :icon="Download" :label="t('document.versionHistory.downloadThisVersion')" size="sm" @click="$emit('download', version)" />
        </div>
        <p class="text-xs text-text-muted">{{ version.uploadedBy }} · {{ formatDate(version.uploadDate) }}</p>
        <p class="text-sm text-text-secondary">{{ version.notes }}</p>
      </li>
    </ul>
  </Card>
</template>
