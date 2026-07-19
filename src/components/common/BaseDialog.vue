<script setup lang="ts">
import { X } from '@lucide/vue'
import { onBeforeUnmount, watch } from 'vue'

import IconButton from '@/components/common/IconButton.vue'
import type { ComponentSize } from '@/types/Ui'

interface Props {
  modelValue: boolean
  title?: string
  size?: ComponentSize
  closable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: undefined,
  size: 'md',
  closable: true,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  close: []
}>()

const sizeClasses: Record<ComponentSize, string> = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
}

const closeDialog = (): void => {
  if (!props.closable) return
  emit('update:modelValue', false)
  emit('close')
}

const handleKeydown = (event: KeyboardEvent): void => {
  if (event.key === 'Escape' && props.modelValue) {
    closeDialog()
  }
}

watch(
  () => props.modelValue,
  (isOpen) => {
    document.body.classList.toggle('overflow-hidden', isOpen)
  },
)

window.addEventListener('keydown', handleKeydown)
onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
  document.body.classList.remove('overflow-hidden')
})
</script>

<template>
  <Teleport to="body">
    <div v-if="modelValue" class="fixed inset-0 z-modal flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-neutral-900/50" @click="closeDialog" />
      <div
        class="relative w-full rounded-xl bg-bg-card p-6 shadow-elevated"
        :class="sizeClasses[size]"
        role="dialog"
        aria-modal="true"
      >
        <div v-if="title || closable" class="mb-4 flex items-center justify-between">
          <h2 v-if="title" class="text-lg font-semibold text-neutral-800">{{ title }}</h2>
          <IconButton v-if="closable" :icon="X" label="Close dialog" size="sm" @click="closeDialog" />
        </div>
        <slot />
        <div v-if="$slots.footer" class="mt-6 flex justify-end gap-3">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>
