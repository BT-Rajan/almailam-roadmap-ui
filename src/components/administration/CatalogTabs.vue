<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useLocale } from '@/composables/useLocale'

export type CatalogTabKey = 'services' | 'permits'

export interface CatalogTab {
  key: CatalogTabKey
  label: string
}

interface Props {
  tabs: CatalogTab[]
  activeTab: CatalogTabKey
}

const props = defineProps<Props>()
const { t } = useI18n()
const { isRtl } = useLocale()

const emit = defineEmits<{
  select: [tab: CatalogTabKey]
}>()

const tabRefs = ref<HTMLButtonElement[]>([])

function setTabRef(el: unknown, index: number): void {
  if (el instanceof HTMLButtonElement) tabRefs.value[index] = el
}

// Same WAI-ARIA tabs keyboard pattern as ClientWorkspaceTabs.vue: arrow
// keys move focus and activate the newly-focused tab, wrapping at either
// end.
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
  <div class="flex gap-1 overflow-x-auto border-b border-border-light" role="tablist" :aria-label="t('administration.catalogsPage.tabsAriaLabel')">
    <button
      v-for="(tab, index) in tabs"
      :key="tab.key"
      :ref="(el) => setTabRef(el, index)"
      :id="`catalog-tab-${tab.key}`"
      type="button"
      role="tab"
      class="shrink-0 whitespace-nowrap rounded-t-md border-b-2 px-4 py-3 text-sm font-medium transition-colors duration-fast focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500"
      :class="
        activeTab === tab.key
          ? 'border-accent-500 text-accent-700 dark:text-accent-400'
          : 'border-transparent text-text-muted hover:text-text-primary'
      "
      :aria-selected="activeTab === tab.key"
      :aria-controls="`catalog-tabpanel-${tab.key}`"
      :tabindex="activeTab === tab.key ? 0 : -1"
      @click="emit('select', tab.key)"
      @keydown="handleKeydown($event, index)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>
