<script setup lang="ts">
import { Bell, Calendar, Menu, MessageSquare, Search, Sparkles } from '@lucide/vue'
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import UserMenu from '@/components/navigation/UserMenu.vue'
import { useRbac } from '@/composables/useRbac'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useKnowledgeStore } from '@/stores/knowledgeStore'
import { useNavigationStore } from '@/stores/navigationStore'
import { useNotificationStore } from '@/stores/notificationStore'
import { useSearchStore } from '@/stores/searchStore'

const router = useRouter()
const navigationStore = useNavigationStore()
const notificationStore = useNotificationStore()
const searchStore = useSearchStore()
const knowledgeStore = useKnowledgeStore()
const { can } = useRbac()

onMounted(() => {
  void notificationStore.loadNotifications()
  if (knowledgeStore.isEnabled === undefined) void knowledgeStore.loadStatus()
})
</script>

<template>
  <header
    class="flex h-16 shrink-0 items-center justify-between gap-4 border-b border-[var(--color-border-default)] bg-bg-header px-4 shadow-glass-sm lg:px-6"
  >
    <div class="flex items-center gap-3">
      <button
        type="button"
        class="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)] lg:hidden"
        aria-label="Open navigation menu"
        @click="navigationStore.openMobileSidebar"
      >
        <Menu :size="20" />
      </button>

      <button
        type="button"
        class="relative hidden w-72 items-center rounded-lg border border-[var(--color-border-default)] bg-bg-secondary py-2 pl-9 pr-3 text-left text-sm text-[var(--color-text-muted)] transition-colors duration-fast hover:border-accent-400 md:flex"
        @click="searchStore.open"
      >
        <Search :size="16" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" />
        <span class="flex-1 truncate">Search clients, projects, documents...</span>
        <kbd class="rounded border border-[var(--color-border-default)] bg-[var(--color-bg-card)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--color-text-muted)]">
          Ctrl K
        </kbd>
      </button>
    </div>

    <div class="flex items-center gap-2">
      <button
        v-if="can('knowledgebase.view') && knowledgeStore.isEnabled !== false"
        type="button"
        class="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--color-text-secondary)] transition-colors duration-fast hover:bg-[var(--color-bg-hover)]"
        aria-label="Knowledge Assistant"
        @click="knowledgeStore.toggleDrawer"
      >
        <Sparkles :size="18" />
      </button>

      <button
        v-if="can('activity.view')"
        type="button"
        class="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--color-text-secondary)] transition-colors duration-fast hover:bg-[var(--color-bg-hover)]"
        aria-label="Activity Calendar"
        @click="router.push({ name: ROUTE_NAMES.ADMIN_ACTIVITY_CALENDAR })"
      >
        <Calendar :size="18" />
      </button>

      <button
        type="button"
        class="relative flex h-9 w-9 items-center justify-center rounded-lg text-[var(--color-text-secondary)] transition-colors duration-fast hover:bg-[var(--color-bg-hover)]"
        aria-label="Notifications"
        @click="notificationStore.toggleDrawer"
      >
        <Bell :size="18" />
        <span
          v-if="notificationStore.hasUnread"
          class="absolute right-1.5 top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-danger-500 px-1 text-[10px] font-semibold leading-none text-white"
          aria-hidden="true"
        >
          {{ notificationStore.unreadCount > 9 ? '9+' : notificationStore.unreadCount }}
        </span>
      </button>

      <button
        type="button"
        class="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--color-text-secondary)] transition-colors duration-fast hover:bg-[var(--color-bg-hover)]"
        aria-label="Message Centre"
        @click="router.push({ name: ROUTE_NAMES.MESSAGE_CENTRE })"
      >
        <MessageSquare :size="18" />
      </button>

      <UserMenu />
    </div>
  </header>
</template>
