<script setup lang="ts">
import { nextTick, ref } from 'vue'

import type { ProjectWorkspaceTab, ProjectWorkspaceTabKey } from '@/types/Project'

interface Props {
  tabs: ProjectWorkspaceTab[]
  activeTab: ProjectWorkspaceTabKey
}

const props = defineProps<Props>()

const emit = defineEmits<{
  select: [tab: ProjectWorkspaceTabKey]
}>()

const tabRefs = ref<HTMLButtonElement[]>([])

function setTabRef(el: unknown, index: number): void {
  if (el instanceof HTMLButtonElement) tabRefs.value[index] = el
}

// WAI-ARIA tabs pattern -- same as ClientWorkspaceTabs.vue: arrow keys
// move focus between tabs (wrapping at either end) and activate the
// newly-focused tab, while Tab/Shift+Tab only stop once at whichever
// tab is currently selected (roving tabindex below), not at every tab
// in sequence.
function focusAndSelect(index: number): void {
  const wrapped = (index + props.tabs.length) % props.tabs.length
  const tab = props.tabs[wrapped]
  if (!tab) return
  emit('select', tab.key)
  nextTick(() => tabRefs.value[wrapped]?.focus())
}

function handleKeydown(event: KeyboardEvent, index: number): void {
  switch (event.key) {
    case 'ArrowRight':
      event.preventDefault()
      focusAndSelect(index + 1)
      break
    case 'ArrowLeft':
      event.preventDefault()
      focusAndSelect(index - 1)
      break
    case 'Home':
      event.preventDefault()
      focusAndSelect(0)
      break
    case 'End':
      event.preventDefault()
      focusAndSelect(props.tabs.length - 1)
      break
  }
}
</script>

<template>
  <div class="no-print flex gap-1 overflow-x-auto border-b border-border-light" role="tablist" aria-label="Project workspace sections">
    <button
      v-for="(tab, index) in tabs"
      :key="tab.key"
      :ref="(el) => setTabRef(el, index)"
      :id="`project-tab-${tab.key}`"
      type="button"
      role="tab"
      class="shrink-0 whitespace-nowrap rounded-t-md border-b-2 px-4 py-3 text-sm font-medium transition-colors duration-fast focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500"
      :class="
        activeTab === tab.key
          ? 'border-accent-500 text-accent-700 dark:text-accent-400'
          : 'border-transparent text-text-muted hover:text-text-primary'
      "
      :aria-selected="activeTab === tab.key"
      :aria-controls="`project-tabpanel-${tab.key}`"
      :tabindex="activeTab === tab.key ? 0 : -1"
      @click="emit('select', tab.key)"
      @keydown="handleKeydown($event, index)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>
