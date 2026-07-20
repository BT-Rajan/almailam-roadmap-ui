<script setup lang="ts">
import type { ClientWorkspaceTab, ClientWorkspaceTabKey } from '@/types/Client'

interface Props {
  tabs: ClientWorkspaceTab[]
  activeTab: ClientWorkspaceTabKey
}

defineProps<Props>()

const emit = defineEmits<{
  select: [tab: ClientWorkspaceTabKey]
}>()
</script>

<template>
  <div class="no-print flex gap-1 overflow-x-auto border-b border-border-light" role="tablist">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      type="button"
      role="tab"
      class="shrink-0 whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors duration-fast"
      :class="
        activeTab === tab.key
          ? 'border-primary-600 text-primary-700'
          : 'border-transparent text-neutral-500 hover:text-neutral-800'
      "
      :aria-selected="activeTab === tab.key"
      @click="emit('select', tab.key)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>
