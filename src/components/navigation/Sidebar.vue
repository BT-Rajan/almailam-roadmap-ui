<script setup lang="ts">
import { ChevronLeft, ChevronRight } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import SidebarItem from '@/components/navigation/SidebarItem.vue'
import { useAuth } from '@/composables/useAuthComposable'
import { PRIMARY_NAV_ITEMS } from '@/constants/navigation'
import { useNavigationStore } from '@/stores/navigationStore'

const navigationStore = useNavigationStore()
const { isAdmin } = useAuth()
const { t } = useI18n()

// adminOnly items (currently just Administration) are hidden from the nav
// entirely for every other role -- the route itself also redirects a
// non-admin who navigates there directly (see router/index.ts's adminOnly
// guard), but a visible menu link to a page you'll immediately get bounced
// out of is confusing on its own, so it's filtered out here too.
const visibleNavItems = computed(() => PRIMARY_NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin.value))
</script>

<template>
  <aside
    class="group relative hidden shrink-0 flex-col border-r border-[var(--color-border-default)] bg-bg-sidebar shadow-glass-sm transition-all duration-normal lg:flex"
    :class="navigationStore.isSidebarCollapsed ? 'w-18' : 'w-70'"
  >
    <div class="flex h-16 items-center gap-2 border-b border-[var(--color-border-default)] px-4">
      <div
        class="gradient-luxe-accent flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-sm font-semibold text-white shadow-glass-sm"
      >
        SO
      </div>
      <span
        v-if="!navigationStore.isSidebarCollapsed"
        class="truncate text-base font-semibold text-[var(--color-text-primary)]"
      >
        {{ t('common.appName') }}
      </span>
    </div>

    <nav class="flex-1 space-y-1 overflow-y-auto px-3 py-4">
      <SidebarItem
        v-for="item in visibleNavItems"
        :key="item.routeName"
        :item="item"
        :collapsed="navigationStore.isSidebarCollapsed"
      />
    </nav>

    <!-- Edge toggle: sits on the sidebar's border instead of taking a
    permanent footer row. Stays clickable at all times but only visible
    while the pointer is over the sidebar (group-hover), so it doesn't
    compete for attention with the nav items above it. -->
    <button
      type="button"
      class="absolute -right-3 top-16 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-full border border-[var(--color-border-default)] bg-bg-sidebar text-[var(--color-text-secondary)] opacity-0 shadow-glass-sm transition-opacity duration-fast hover:text-[var(--color-text-primary)] group-hover:opacity-100"
      :aria-label="navigationStore.isSidebarCollapsed ? t('navigation.expandSidebar') : t('navigation.collapseSidebar')"
      @click="navigationStore.toggleSidebarCollapsed"
    >
      <ChevronLeft v-if="!navigationStore.isSidebarCollapsed" :size="14" />
      <ChevronRight v-else :size="14" />
    </button>
  </aside>
</template>
