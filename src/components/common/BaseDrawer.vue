<script setup lang="ts">
import { X } from '@lucide/vue'
import { onBeforeUnmount, watch } from 'vue'
import type { Component } from 'vue'

import IconButton from '@/components/common/IconButton.vue'

interface Props {
  modelValue: boolean
  title?: string
  icon?: Component
  side?: 'left' | 'right'
  width?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  title: undefined,
  icon: undefined,
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
      <div class="absolute inset-0 bg-neutral-900/40 backdrop-blur-sm" @click="closeDrawer" />
      <div
        class="glass-panel relative flex h-full w-full flex-col shadow-elevated"
        :class="widthClasses[width]"
      >
        <div v-if="title" class="flex items-center justify-between border-b border-border-light px-5 py-4">
          <h2 class="flex items-center gap-2 text-lg font-semibold text-neutral-800">
            <span
              v-if="icon"
              class="gradient-luxe-accent flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-white"
            >
              <component :is="icon" :size="15" />
            </span>
            {{ title }}
          </h2>
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
