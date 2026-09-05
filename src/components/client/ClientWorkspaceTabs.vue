<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useLocale } from '@/composables/useLocale'
import type { ClientWorkspaceTab, ClientWorkspaceTabKey } from '@/types/Client'

interface Props {
  tabs: ClientWorkspaceTab[]
  activeTab: ClientWorkspaceTabKey
}

const props = defineProps<Props>()

const emit = defineEmits<{
  select: [tab: ClientWorkspaceTabKey]
}>()

const { t } = useI18n()
const { isRtl } = useLocale()

const tabRefs = ref<HTMLButtonElement[]>([])

function setTabRef(el: unknown, index: number): void {
  if (el instanceof HTMLButtonElement) tabRefs.value[index] = el
}

// WAI-ARIA tabs pattern: arrow keys move focus between tabs (wrapping
// at either end) and activate the newly-focused tab, matching how a
// native <select> or radio group behaves -- Tab/Shift+Tab still only
// stop once at whichever tab is currently selected (roving tabindex
// below), not at every tab in sequence.
function focusAndSelect(index: number): void {
  const wrapped = (index + props.tabs.length) % props.tabs.length
  const tab = props.tabs[wrapped]
  if (!tab) return
  emit('select', tab.key)
  nextTick(() => tabRefs.value[wrapped]?.focus())
}

// Right/Left Arrow follow reading direction, not physical direction --
// per the WAI-ARIA tabs pattern, they swap under RTL so "next" still
// means "the tab in front of this one," wherever that visually sits.
function handleKeydown(event: KeyboardEvent, index: number): void {
  switch (event.key) {
    case 'ArrowRight':
      event.preventDefault()
      focusAndSelect(isRtl.value ? index - 1 : index + 1)
      break
    case 'ArrowLeft':
      event.preventDefault()
      focusAndSelect(isRtl.value ? index + 1 : index - 1)
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
  <div class="no-print flex gap-1 overflow-x-auto border-b border-border-light" role="tablist" :aria-label="t('client.workspaceTabs.sectionsAria')">
    <button
      v-for="(tab, index) in tabs"
      :key="tab.key"
      :ref="(el) => setTabRef(el, index)"
      :id="`client-tab-${tab.key}`"
      type="button"
      role="tab"
      class="shrink-0 whitespace-nowrap rounded-t-md border-b-2 px-4 py-3 text-sm font-medium transition-colors duration-fast focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500"
      :class="
        activeTab === tab.key
          ? 'border-accent-500 text-accent-700 dark:text-accent-400'
          : 'border-transparent text-text-muted hover:text-text-primary'
      "
      :aria-selected="activeTab === tab.key"
      :aria-controls="`client-tabpanel-${tab.key}`"
      :tabindex="activeTab === tab.key ? 0 : -1"
      @click="emit('select', tab.key)"
      @keydown="handleKeydown($event, index)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>
