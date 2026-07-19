<script setup lang="ts">
import { Bell, CheckCircle2, FileText, TrendingUp } from '@lucide/vue'
import { computed } from 'vue'
import type { ProjectUpdate } from '@/types/CustomerPortal'
import Card from '@/components/common/Card.vue'

interface Props {
  updates: ProjectUpdate[]
}

const props = defineProps<Props>()

const sortedUpdates = computed(() => {
  return [...props.updates].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()).slice(0, 8)
})

const getUpdateIcon = (type: string) => {
  if (type === 'milestone') return CheckCircle2
  if (type === 'deliverable') return FileText
  if (type === 'status') return TrendingUp
  return Bell
}

const getUpdateColor = (type: string) => {
  if (type === 'milestone') return 'bg-success-50 border-success-200'
  if (type === 'deliverable') return 'bg-info-50 border-info-200'
  if (type === 'status') return 'bg-warning-50 border-warning-200'
  return 'bg-neutral-50 border-neutral-200'
}

const getIconColor = (type: string) => {
  if (type === 'milestone') return 'text-success-600'
  if (type === 'deliverable') return 'text-info-600'
  if (type === 'status') return 'text-warning-600'
  return 'text-neutral-600'
}

const formatDate = (date: string) => {
  const d = new Date(date)
  const today = new Date()
  const diff = Math.floor((today.getTime() - d.getTime()) / (1000 * 60 * 60 * 24))

  if (diff === 0) return 'Today'
  if (diff === 1) return 'Yesterday'
  if (diff < 7) return `${diff} days ago`

  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <Card>
    <template #header>
      <h2 class="text-xl font-semibold text-neutral-900">Recent Updates</h2>
    </template>

    <div v-if="sortedUpdates.length === 0" class="py-8 text-center text-neutral-500">
      <p>No updates yet</p>
    </div>

    <div v-else class="space-y-3">
      <div v-for="update in sortedUpdates" :key="update.id" :class="['p-4 rounded-lg border', getUpdateColor(update.type)]">
        <div class="flex gap-3">
          <component :is="getUpdateIcon(update.type)" :class="['h-5 w-5 flex-shrink-0 mt-0.5', getIconColor(update.type)]" />
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-2">
              <div>
                <h3 class="font-medium text-neutral-900">{{ update.title }}</h3>
                <p v-if="update.description" class="text-sm text-neutral-700 mt-1">{{ update.description }}</p>
              </div>
              <span class="text-xs text-neutral-500 flex-shrink-0 mt-0.5">{{ formatDate(update.date) }}</span>
            </div>
            <div v-if="update.attachments && update.attachments.length > 0" class="mt-2 flex flex-wrap gap-2">
              <a
                v-for="attachment in update.attachments"
                :key="attachment"
                :href="`#${attachment}`"
                class="inline-flex items-center gap-1 text-xs text-neutral-600 hover:text-neutral-900 transition-colors"
              >
                <FileText class="h-3 w-3" />
                {{ attachment }}
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>
