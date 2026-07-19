<script setup lang="ts">
import { FileText } from '@lucide/vue'
import { computed } from 'vue'
import type { DocumentItem } from '@/types/Dashboard'
import Card from '@/components/common/Card.vue'

interface Props {
  documents: DocumentItem[]
  title?: string
  maxItems?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Recent Documents',
  maxItems: 5,
})

defineEmits<{
  'document-click': [documentId: string]
}>()


const displayedDocuments = computed(() =>
  [...props.documents]
    .sort((a, b) => new Date(b.uploadedAt).getTime() - new Date(a.uploadedAt).getTime())
    .slice(0, props.maxItems),
)

const formatSize = (size: string) => size

const formatDate = (date: string) => {
  const d = new Date(date)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <Card>
    <template #header>
      <h3 class="font-medium text-neutral-900">{{ title }}</h3>
    </template>

    <div v-if="displayedDocuments.length === 0" class="py-8 text-center text-neutral-500">
      <p class="text-sm">No recent documents</p>
    </div>
    <div v-else class="space-y-2">
      <div
        v-for="doc in displayedDocuments"
        :key="doc.id"
        class="p-3 rounded-lg border border-border-light hover:bg-bg-hover transition-colors cursor-pointer flex items-start gap-3"
        @click="$emit('document-click', doc.id)"
      >
        <FileText class="h-5 w-5 text-neutral-400 flex-shrink-0 mt-0.5" />
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-neutral-900 truncate">{{ doc.name }}</p>
          <p class="text-xs text-neutral-500 mt-1">{{ doc.project }}</p>
          <div class="flex items-center justify-between mt-2">
            <span class="text-xs text-neutral-400">{{ doc.uploadedBy }}</span>
            <span class="text-xs text-neutral-400">{{ formatSize(doc.size) }}</span>
          </div>
          <p class="text-xs text-neutral-400 mt-1">{{ formatDate(doc.uploadedAt) }}</p>
        </div>
      </div>
    </div>
  </Card>
</template>
