<script setup lang="ts">
import { nextTick, ref } from 'vue'

import { useLocale } from '@/composables/useLocale'

// A generic tab strip (WAI-ARIA tabs pattern, same look and keyboard
// handling as ProjectWorkspaceTabs.vue/ClientWorkspaceTabs.vue, which
// stay tied to their own key types). A disabled tab is shown but can't
// be selected -- arrow keys skip over it.
export interface TabBarTab {
  key: string
  label: string
  disabled?: boolean
  // Native tooltip, e.g. why a tab is disabled.
  title?: string
}

interface Props {
  tabs: TabBarTab[]
  modelValue: string
  tablistLabel: string
  // Prefix for the tab/tabpanel ids (`${idPrefix}-tab-${key}` and
  // `${idPrefix}-tabpanel-${key}`) so a page can wire its panels up.
  idPrefix?: string
}

const props = withDefaults(defineProps<Props>(), {
  idPrefix: 'tabbar',
})

const emit = defineEmits<{
  'update:modelValue': [key: string]
}>()

const { isRtl } = useLocale()

const tabRefs = ref<HTMLButtonElement[]>([])

function setTabRef(el: unknown, index: number): void {
  if (el instanceof HTMLButtonElement) tabRefs.value[index] = el
}

// Moves to the nearest enabled tab in `step` direction from `from`
// (wrapping at either end), or does nothing if there's none.
function focusAndSelect(from: number, step: 1 | -1): void {
  const count = props.tabs.length
  for (let offset = 1; offset <= count; offset += 1) {
    const index = (from + step * offset + count * offset) % count
    const tab = props.tabs[index]
    if (tab && !tab.disabled) {
      emit('update:modelValue', tab.key)
      nextTick(() => tabRefs.value[index]?.focus())
      return
    }
  }
}

function focusEdge(edge: 'first' | 'last'): void {
  const indexes = props.tabs.map((_, index) => index)
  const ordered = edge === 'first' ? indexes : indexes.reverse()
  const index = ordered.find((candidate) => !props.tabs[candidate]?.disabled)
  if (index === undefined) return
  emit('update:modelValue', props.tabs[index].key)
  nextTick(() => tabRefs.value[index]?.focus())
}

// Right/Left Arrow follow reading direction, so they swap under RTL.
function handleKeydown(event: KeyboardEvent, index: number): void {
  switch (event.key) {
    case 'ArrowRight':
      event.preventDefault()
      focusAndSelect(index, isRtl.value ? -1 : 1)
      break
    case 'ArrowLeft':
      event.preventDefault()
      focusAndSelect(index, isRtl.value ? 1 : -1)
      break
    case 'Home':
      event.preventDefault()
      focusEdge('first')
      break
    case 'End':
      event.preventDefault()
      focusEdge('last')
      break
  }
}
</script>

<template>
  <div class="no-print flex gap-1 overflow-x-auto border-b border-border-light" role="tablist" :aria-label="tablistLabel">
    <button
      v-for="(tab, index) in tabs"
      :key="tab.key"
      :ref="(el) => setTabRef(el, index)"
      :id="`${idPrefix}-tab-${tab.key}`"
      type="button"
      role="tab"
      class="shrink-0 whitespace-nowrap rounded-t-md border-b-2 px-4 py-3 text-sm font-medium transition-colors duration-fast focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500"
      :class="
        modelValue === tab.key
          ? 'border-accent-500 text-accent-700 dark:text-accent-400'
          : tab.disabled
            ? 'cursor-not-allowed border-transparent text-text-muted opacity-50'
            : 'border-transparent text-text-muted hover:text-text-primary'
      "
      :aria-selected="modelValue === tab.key"
      :aria-controls="`${idPrefix}-tabpanel-${tab.key}`"
      :aria-disabled="tab.disabled || undefined"
      :title="tab.disabled ? tab.title : undefined"
      :tabindex="modelValue === tab.key ? 0 : -1"
      @click="!tab.disabled && emit('update:modelValue', tab.key)"
      @keydown="handleKeydown($event, index)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>
