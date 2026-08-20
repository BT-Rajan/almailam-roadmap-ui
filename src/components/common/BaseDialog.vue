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

// "lg" is deliberately much wider than "md" (not just a step up) --
// this is the tier used for multi-section forms with many fields
// (Edit Client, Edit Project, etc.), which felt cramped at the old
// max-w-2xl (672px) despite being the largest size available. "sm" and
// "md" are unchanged: appropriate for confirmations and single-section
// forms respectively, and widening those too would just add awkward
// empty space around a handful of fields.
const sizeClasses: Record<ComponentSize, string> = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-4xl',
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
      <div class="absolute inset-0 bg-neutral-900/40 backdrop-blur-sm" @click="closeDialog" />
      <div
        class="glass-panel relative flex max-h-[90vh] w-full flex-col rounded-xl shadow-elevated"
        :class="sizeClasses[size]"
        role="dialog"
        aria-modal="true"
      >
        <div v-if="title || closable" class="flex shrink-0 items-center justify-between border-b border-border-light px-6 py-4">
          <h2 v-if="title" class="text-lg font-semibold text-text-primary">{{ title }}</h2>
          <IconButton v-if="closable" :icon="X" label="Close dialog" size="sm" @click="closeDialog" />
        </div>
        <!-- The actual scroll fix: previously nothing in this component had
             overflow-y set anywhere, and the body scroll was deliberately
             disabled while a dialog was open -- so any dialog whose content
             was taller than the viewport (a real, common case for a
             multi-section edit form) had content and even the Save/Cancel
             buttons pushed off-screen with no way to reach them at all. Now
             only this middle region scrolls; the header and footer stay
             pinned and always reachable. -->
        <div class="flex-1 overflow-y-auto px-6 py-5">
          <slot />
        </div>
        <div v-if="$slots.footer" class="flex shrink-0 justify-end gap-3 border-t border-border-light px-6 py-4">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>
