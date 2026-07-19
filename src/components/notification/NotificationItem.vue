<script setup lang="ts">
import { computed } from 'vue'
import { Bell, Bot, FolderKanban, Landmark, ListChecks } from '@lucide/vue'
import type { Component } from 'vue'

import type { AppNotification, NotificationCategory } from '@/types/Notification'

interface Props {
  notification: AppNotification
}

const props = defineProps<Props>()

const emit = defineEmits<{
  select: [notification: AppNotification]
}>()

const CATEGORY_ICONS: Record<NotificationCategory, Component> = {
  Project: FolderKanban,
  Task: ListChecks,
  Government: Landmark,
  AI: Bot,
  System: Bell,
}

const CATEGORY_CLASSES: Record<NotificationCategory, string> = {
  Project: 'bg-primary-50 text-primary-600',
  Task: 'bg-success-50 text-success-700',
  Government: 'bg-warning-50 text-warning-700',
  AI: 'bg-ai-50 text-ai-700',
  System: 'bg-neutral-100 text-neutral-500',
}

const icon = computed(() => CATEGORY_ICONS[props.notification.category])
const iconClasses = computed(() => CATEGORY_CLASSES[props.notification.category])

const timeLabel = computed(() => {
  const date = new Date(props.notification.date)
  return date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
})
</script>

<template>
  <button
    type="button"
    class="flex w-full items-start gap-3 rounded-lg px-2 py-3 text-left transition-colors duration-fast hover:bg-bg-hover"
    @click="emit('select', notification)"
  >
    <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full" :class="iconClasses">
      <component :is="icon" :size="16" />
    </span>

    <span class="min-w-0 flex-1">
      <span class="flex items-start justify-between gap-2">
        <span class="text-sm font-semibold text-neutral-800" :class="{ 'text-neutral-600': notification.read }">
          {{ notification.title }}
        </span>
        <span
          v-if="!notification.read"
          class="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary-500"
          aria-hidden="true"
        />
      </span>
      <span class="mt-0.5 block text-sm text-neutral-500">{{ notification.message }}</span>
      <span class="mt-1 block text-xs text-neutral-400">{{ timeLabel }}</span>
    </span>
  </button>
</template>
