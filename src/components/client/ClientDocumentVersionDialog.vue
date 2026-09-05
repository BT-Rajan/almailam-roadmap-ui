<script setup lang="ts">
import { Download } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

import BaseDialog from '@/components/common/BaseDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ClientDocument, ClientDocumentVersion } from '@/types/Client'
import { formatDateTime } from '@/utils/dateFormatter'

const props = defineProps<{
  modelValue: boolean
  document?: ClientDocument
  versions: ClientDocumentVersion[]
  loading?: boolean
}>()

defineEmits<{
  'update:modelValue': [value: boolean]
  download: [version: ClientDocumentVersion]
}>()

const { t } = useI18n()

function isCurrentVersion(version: ClientDocumentVersion): boolean {
  return props.versions[props.versions.length - 1]?.id === version.id
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="document ? t('client.documentVersionDialog.titleWithName', { name: document.title }) : t('client.documentVersionDialog.title')"
    size="md"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <SkeletonLoader v-if="loading" variant="block" height="8rem" />

    <EmptyState
      v-else-if="versions.length === 0"
      :title="t('client.documentVersionDialog.noVersionsTitle')"
      :description="t('client.documentVersionDialog.noVersionsDescription')"
    />

    <ul v-else class="flex flex-col gap-4">
      <li
        v-for="version in [...versions].reverse()"
        :key="version.id"
        class="flex flex-col gap-1 border-s-2 border-border-light ps-3"
      >
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <span class="text-sm font-semibold text-text-primary">{{ t('client.documentVersionDialog.version', { version: version.version }) }}</span>
            <StatusBadge v-if="isCurrentVersion(version)" :label="t('client.documentVersionDialog.current')" variant="success" size="sm" />
          </div>
          <IconButton :icon="Download" :label="t('client.documentVersionDialog.downloadVersion', { version: version.version })" size="sm" @click="$emit('download', version)" />
        </div>
        <p class="text-xs text-text-muted">{{ version.uploadedBy }} · {{ formatDateTime(version.uploadDate) }}</p>
        <p class="text-sm text-text-secondary">{{ version.notes }}</p>
        <p class="text-xs text-text-muted">{{ version.originalFilename }}</p>
      </li>
    </ul>
  </BaseDialog>
</template>
