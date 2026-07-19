<script setup lang="ts">
import { Inbox } from '@lucide/vue'
import type { Component } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'

interface Props {
  icon?: Component
  title: string
  description?: string
  actionLabel?: string
}

withDefaults(defineProps<Props>(), {
  icon: Inbox,
  description: undefined,
  actionLabel: undefined,
})

defineEmits<{
  action: []
}>()
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3 px-6 py-12 text-center">
    <span class="flex h-12 w-12 items-center justify-center rounded-full bg-bg-secondary">
      <component :is="icon" class="h-6 w-6 text-neutral-400" />
    </span>
    <div class="flex flex-col gap-1">
      <p class="text-sm font-semibold text-neutral-700">{{ title }}</p>
      <p v-if="description" class="text-sm text-neutral-400">{{ description }}</p>
    </div>
    <BaseButton v-if="actionLabel" variant="secondary" size="sm" @click="$emit('action')">
      {{ actionLabel }}
    </BaseButton>
  </div>
</template>
