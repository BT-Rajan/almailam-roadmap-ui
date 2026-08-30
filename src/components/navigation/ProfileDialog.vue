<script setup lang="ts">
import { Mail, Phone, Shield, User } from '@lucide/vue'
import { computed } from 'vue'

import BaseDialog from '@/components/common/BaseDialog.vue'
import { useAuth } from '@/composables/useAuthComposable'

defineProps<{
  modelValue: boolean
}>()

defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const { user } = useAuth()

const initials = computed(() => {
  const name = user.value?.name?.trim()
  if (!name) return ''
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
})
</script>

<template>
  <BaseDialog title="My Profile" size="sm" :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <div class="flex flex-col items-center gap-3 pb-2 text-center">
      <span class="gradient-luxe-accent flex h-16 w-16 items-center justify-center rounded-full text-xl font-semibold text-white">
        {{ initials }}
      </span>
      <div>
        <p class="text-base font-semibold text-text-primary">{{ user?.name }}</p>
        <p class="text-sm text-text-muted">{{ user?.designation || user?.role }}</p>
      </div>
    </div>

    <dl class="flex flex-col divide-y divide-border-light border-t border-border-light">
      <div class="flex items-center gap-3 py-3">
        <Mail :size="16" class="shrink-0 text-text-muted" />
        <dt class="sr-only">Email</dt>
        <dd class="truncate text-sm text-text-primary">{{ user?.email }}</dd>
      </div>
      <div v-if="user?.mobile" class="flex items-center gap-3 py-3">
        <Phone :size="16" class="shrink-0 text-text-muted" />
        <dt class="sr-only">Mobile</dt>
        <dd class="text-sm text-text-primary">{{ user?.mobile }}</dd>
      </div>
      <div class="flex items-center gap-3 py-3">
        <Shield :size="16" class="shrink-0 text-text-muted" />
        <dt class="sr-only">Role</dt>
        <dd class="text-sm text-text-primary">{{ user?.role }}</dd>
      </div>
      <div class="flex items-center gap-3 py-3">
        <User :size="16" class="shrink-0 text-text-muted" />
        <dt class="sr-only">Status</dt>
        <dd class="text-sm text-text-primary">{{ user?.status }}</dd>
      </div>
    </dl>
  </BaseDialog>
</template>
