<script setup lang="ts">
import { Inbox } from '@lucide/vue'
import type { Component } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'

interface Props {
  icon?: Component
  title: string
  description?: string
  actionLabel?: string
  // Renders its own card-like border/background by default, so an
  // empty state reads as a proper card rather than loose text
  // floating on the page -- matching the loading skeleton block most
  // of these same views fall back to before data arrives (`rounded-xl
  // border border-border-light bg-bg-card p-5`). Set to false only
  // when the caller already wraps this in its own Card (see
  // TaskList.vue/ActivityCalendarPage.vue), where a second border
  // would double up.
  bordered?: boolean
}

withDefaults(defineProps<Props>(), {
  icon: () => Inbox,
  description: undefined,
  actionLabel: undefined,
  bordered: true,
})

defineEmits<{
  action: []
}>()
</script>

<template>
  <div
    class="flex flex-col items-center justify-center gap-3 px-6 py-12 text-center"
    :class="bordered ? 'rounded-xl border border-border-light bg-bg-card shadow-glass-sm' : ''"
  >
    <span class="flex h-12 w-12 items-center justify-center rounded-full bg-bg-secondary ring-1 ring-inset ring-border-light">
      <component :is="icon" class="h-6 w-6 text-text-muted" />
    </span>
    <div class="flex flex-col gap-1">
      <p class="text-sm font-semibold text-text-secondary">{{ title }}</p>
      <p v-if="description" class="max-w-sm text-sm text-text-muted">{{ description }}</p>
    </div>
    <BaseButton v-if="actionLabel" variant="secondary" size="sm" @click="$emit('action')">
      {{ actionLabel }}
    </BaseButton>
  </div>
</template>
