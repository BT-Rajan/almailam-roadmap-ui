<script setup lang="ts">
import { ChevronLeft, ChevronRight, FileText } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { DocumentItem } from '@/types/Dashboard'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PaginatedList from '@/components/common/PaginatedList.vue'
import { useLocale } from '@/composables/useLocale'
import { formatShortDateTime } from '@/utils/dateFormatter'

interface Props {
  documents: DocumentItem[]
  title?: string
  pageSize?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: undefined,
  pageSize: 5,
})

defineEmits<{
  'document-click': [documentId: string]
}>()

const { t } = useI18n()
const { isRtl } = useLocale()
const chevronIcon = computed(() => (isRtl.value ? ChevronLeft : ChevronRight))

const displayedDocuments = computed(() =>
  [...props.documents]
    .sort((a, b) => new Date(b.uploadedAt).getTime() - new Date(a.uploadedAt).getTime()),
)

const formatSize = (size: string | null) => size ?? t('dashboard.noFile')

const formatDate = formatShortDateTime
</script>

<template>
  <Card :padded="false">
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ title ?? t('dashboard.recentDocuments') }}</h3>
    </template>

    <EmptyState v-if="displayedDocuments.length === 0" :title="t('dashboard.noRecentDocuments')" :bordered="false" />
    <PaginatedList v-else :items="displayedDocuments" :page-size="pageSize">
      <template #default="{ items }">
        <ul class="divide-y divide-border-light">
          <li
            v-for="doc in items"
            :key="doc.id"
            class="flex cursor-pointer items-center gap-3 px-5 py-3.5 transition-colors hover:bg-bg-hover"
            @click="$emit('document-click', doc.id)"
          >
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-bg-secondary">
              <FileText class="h-5 w-5 text-text-muted" />
            </span>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-text-primary">{{ doc.name }}</p>
              <p class="mt-0.5 truncate text-xs text-text-muted">{{ doc.project }}</p>
              <div class="mt-1.5 flex items-center justify-between">
                <span class="text-xs text-text-muted">{{ doc.uploadedBy }} · {{ formatSize(doc.size) }}</span>
                <span class="text-xs text-text-muted">{{ formatDate(doc.uploadedAt) }}</span>
              </div>
            </div>
            <component :is="chevronIcon" class="h-4 w-4 shrink-0 text-text-muted" />
          </li>
        </ul>
      </template>
    </PaginatedList>
  </Card>
</template>
