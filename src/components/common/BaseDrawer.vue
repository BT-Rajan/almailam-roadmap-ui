<script setup lang="ts">
import { X } from '@lucide/vue'
import { onBeforeUnmount, watch } from 'vue'

import IconButton from '@/components/common/IconButton.vue'

interface Props {
  modelValue: boolean
  title?: string
  side?: 'left' | 'right'
  width?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  title: undefined,
  side: 'right',
  width: 'md',
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  close: []
}>()

const widthClasses: Record<string, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-xl',
}

const closeDrawer = (): void => {
  emit('update:modelValue', false)
  emit('close')
}

const handleKeydown = (event: KeyboardEvent): void => {
  if (event.key === 'Escape' && props.modelValue) {
    closeDrawer()
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
    <div v-if="modelValue" class="fixed inset-0 z-drawer flex" :class="side === 'left' ? '' : 'justify-end'">
      <div class="absolute inset-0 bg-neutral-900/50" @click="closeDrawer" />
      <div
        class="relative flex h-full w-full flex-col bg-bg-card shadow-elevated"
        :class="widthClasses[width]"
      >
        <div v-if="title" class="flex items-center justify-between border-b border-border-light px-5 py-4">
          <h2 class="text-lg font-semibold text-neutral-800">{{ title }}</h2>
          <IconButton :icon="X" label="Close" size="sm" @click="closeDrawer" />
        </div>
        <div class="flex-1 overflow-y-auto px-5 py-4">
          <slot />
        </div>
        <div v-if="$slots.footer" class="border-t border-border-light px-5 py-4">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>
