<script setup lang="ts">
import { ChevronLeft, ChevronRight } from '@lucide/vue'

import SidebarItem from '@/components/navigation/SidebarItem.vue'
import { PRIMARY_NAV_ITEMS } from '@/constants/navigation'
import { useNavigationStore } from '@/stores/navigationStore'

const navigationStore = useNavigationStore()
</script>

<template>
  <aside
    class="hidden shrink-0 flex-col border-r border-[var(--color-border-default)] bg-[var(--color-bg-sidebar)] transition-all duration-normal lg:flex"
    :class="navigationStore.isSidebarCollapsed ? 'w-18' : 'w-70'"
  >
    <div class="flex h-16 items-center gap-2 border-b border-[var(--color-border-default)] px-4">
      <div
        class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-600 text-sm font-semibold text-white"
      >
        SO
      </div>
      <span
        v-if="!navigationStore.isSidebarCollapsed"
        class="truncate text-base font-semibold text-[var(--color-text-primary)]"
      >
        ServiceOS
      </span>
    </div>

    <nav class="flex-1 space-y-1 overflow-y-auto px-3 py-4">
      <SidebarItem
        v-for="item in PRIMARY_NAV_ITEMS"
        :key="item.routeName"
        :item="item"
        :collapsed="navigationStore.isSidebarCollapsed"
      />
    </nav>

    <div class="border-t border-[var(--color-border-default)] p-3">
      <button
        type="button"
        class="flex w-full items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-[var(--color-text-secondary)] transition-colors duration-fast hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-primary)]"
        @click="navigationStore.toggleSidebarCollapsed"
      >
        <ChevronLeft v-if="!navigationStore.isSidebarCollapsed" :size="18" />
        <ChevronRight v-else :size="18" />
        <span v-if="!navigationStore.isSidebarCollapsed">Collapse</span>
      </button>
    </div>
  </aside>
</template>
