<script setup lang="ts">
import { computed } from 'vue'
import type { Activity } from '@/types/Dashboard'
import Card from '@/components/common/Card.vue'
import Divider from '@/components/common/Divider.vue'

interface Props {
  activities: Activity[]
  title?: string
  maxItems?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Recent Activity',
  maxItems: 5,
})


const displayedActivities = computed(() => props.activities.slice(0, props.maxItems))

const activityColor = computed(() => (type: string) => {
  const colors: Record<string, string> = {
    project: 'primary',
    document: 'info',
    submission: 'warning',
    task: 'success',
    ai: 'ai',
  }
  return colors[type] || 'neutral'
})

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString()
}
</script>

<template>
  <Card>
    <template #header>
      <h3 class="font-medium text-neutral-900">{{ title }}</h3>
    </template>

    <div class="space-y-0">
      <div v-for="(activity, index) in displayedActivities" :key="activity.id">
        <div class="py-3 flex gap-3">
          <div v-if="activity.icon" class="flex-shrink-0 w-8 h-8 rounded-full bg-bg-secondary flex items-center justify-center text-sm">
            {{ activity.icon }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-neutral-900">{{ activity.title }}</p>
            <p v-if="activity.description" class="text-xs text-neutral-500 mt-0.5 line-clamp-2">
              {{ activity.description }}
            </p>
            <div class="flex items-center gap-2 mt-1">
              <span class="text-xs text-neutral-400">{{ activity.user }}</span>
              <span class="text-xs text-neutral-400">{{ formatTime(activity.timestamp) }}</span>
            </div>
          </div>
        </div>
        <Divider v-if="index < displayedActivities.length - 1" class="my-0" />
      </div>
    </div>
  </Card>
</template>
