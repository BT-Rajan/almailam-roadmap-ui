<script setup lang="ts">
import { Download, History } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ScopeRevision } from '@/types/Project'
import { formatDate } from '@/utils/dateFormatter'

const props = defineProps<{
  revisions: ScopeRevision[]
}>()

const emit = defineEmits<{
  download: [revision: ScopeRevision]
}>()

const { t } = useI18n()

function isLatestRevision(revision: ScopeRevision): boolean {
  return props.revisions[props.revisions.length - 1]?.id === revision.id
}
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('project.revisionHistory.scopeTitle') }}</h3>
    </template>

    <EmptyState v-if="revisions.length === 0" :icon="History" :title="t('project.revisionHistory.emptyTitle')" />

    <ul v-else class="flex flex-col gap-4">
      <li
        v-for="revision in [...revisions].reverse()"
        :key="revision.id"
        class="flex flex-col gap-1 border-s-2 border-border-light ps-3"
      >
        <div class="flex items-center gap-2">
          <span class="text-sm font-semibold text-text-primary">{{ revision.revision }}</span>
          <StatusBadge v-if="isLatestRevision(revision)" :label="t('project.revisionHistory.current')" variant="success" size="sm" />
        </div>
        <p class="text-xs text-text-muted">{{ revision.changedBy }} · {{ formatDate(revision.date) }}</p>
        <p class="text-sm text-text-secondary">{{ revision.summary }}</p>
        <BaseButton
          v-if="revision.hasDocument"
          variant="ghost"
          size="sm"
          :icon="Download"
          class="self-start no-print"
          @click="emit('download', revision)"
        >
          {{ revision.documentName ?? t('project.revisionHistory.attachedDocument') }}
        </BaseButton>
      </li>
    </ul>
  </Card>
</template>
