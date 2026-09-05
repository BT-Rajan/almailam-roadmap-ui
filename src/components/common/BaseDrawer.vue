<script setup lang="ts">
import { X } from '@lucide/vue'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import IconButton from '@/components/common/IconButton.vue'
import { useFocusTrap } from '@/composables/useFocusTrap'
import { useLocale } from '@/composables/useLocale'
import { useOverlayStack } from '@/composables/useOverlayStack'

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

const { t } = useI18n()
const { isRtl } = useLocale()

const widthClasses: Record<string, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-xl',
}

// `side` picks which logical edge the panel is pinned to -- the flex
// `justify-end`/`justify-start` placement below already mirrors that
// correctly under dir="rtl" for free. The slide-in transform can't:
// CSS transforms move along the physical X axis regardless of writing
// direction, so the enter/leave animation needs to know which physical
// edge the panel actually lands on once RTL has flipped it.
const physicalSide = computed<'left' | 'right'>(() => {
  if (!isRtl.value) return props.side
  return props.side === 'left' ? 'right' : 'left'
})

const panelRef = ref<HTMLElement>()

const closeDrawer = (): void => {
  emit('update:modelValue', false)
  emit('close')
}

const { isTopmost } = useOverlayStack(() => props.modelValue)
useFocusTrap(panelRef, () => props.modelValue)

const handleKeydown = (event: KeyboardEvent): void => {
  if (event.key === 'Escape' && props.modelValue && isTopmost()) {
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
      <Transition appear name="drawer-backdrop">
        <div class="absolute inset-0 bg-neutral-900/40 backdrop-blur-sm" @click="closeDrawer" />
      </Transition>
      <Transition appear :name="physicalSide === 'left' ? 'drawer-slide-from-left' : 'drawer-slide-from-right'">
        <div
          ref="panelRef"
          class="glass-panel relative flex h-full w-full flex-col shadow-elevated focus:outline-none"
          :class="widthClasses[width]"
          tabindex="-1"
        >
          <div v-if="title" class="flex items-center justify-between border-b border-border-light px-5 py-4">
            <h2 class="text-lg font-semibold text-text-primary">{{ title }}</h2>
            <IconButton :icon="X" :label="t('common.close')" size="sm" @click="closeDrawer" />
          </div>
          <div class="flex-1 overflow-y-auto px-5 py-4">
            <slot />
          </div>
          <div v-if="$slots.footer" class="border-t border-border-light px-5 py-4">
            <slot name="footer" />
          </div>
        </div>
      </Transition>
    </div>
  </Teleport>
</template>

<style scoped>
.drawer-backdrop-enter-active,
.drawer-backdrop-leave-active {
  transition: opacity 200ms ease;
}
.drawer-backdrop-enter-from,
.drawer-backdrop-leave-to {
  opacity: 0;
}

.drawer-slide-from-right-enter-active,
.drawer-slide-from-right-leave-active,
.drawer-slide-from-left-enter-active,
.drawer-slide-from-left-leave-active {
  transition: transform 240ms cubic-bezier(0.16, 1, 0.3, 1);
}
.drawer-slide-from-right-enter-from,
.drawer-slide-from-right-leave-to {
  transform: translateX(100%);
}
.drawer-slide-from-left-enter-from,
.drawer-slide-from-left-leave-to {
  transform: translateX(-100%);
}

@media (prefers-reduced-motion: reduce) {
  .drawer-backdrop-enter-active,
  .drawer-backdrop-leave-active,
  .drawer-slide-from-right-enter-active,
  .drawer-slide-from-right-leave-active,
  .drawer-slide-from-left-enter-active,
  .drawer-slide-from-left-leave-active {
    transition: none;
  }
}
</style>
