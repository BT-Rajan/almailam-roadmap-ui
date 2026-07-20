<script setup lang="ts">
import { Bell, Menu, MessageSquare, Moon, Search, Sparkles, Sun, User } from '@lucide/vue'
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { useTheme } from '@/composables/useTheme'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAIAssistantStore } from '@/stores/aiAssistantStore'
import { useAIConfigStore } from '@/stores/aiConfigStore'
import { useNavigationStore } from '@/stores/navigationStore'
import { useNotificationStore } from '@/stores/notificationStore'
import { useSearchStore } from '@/stores/searchStore'

const router = useRouter()
const navigationStore = useNavigationStore()
const notificationStore = useNotificationStore()
const searchStore = useSearchStore()
const aiAssistantStore = useAIAssistantStore()
const aiConfigStore = useAIConfigStore()
const { isDark, toggleMode } = useTheme()

onMounted(() => {
  void notificationStore.loadNotifications()
  if (!aiConfigStore.config) void aiConfigStore.loadConfiguration()
})
</script>

<template>
  <header
    class="flex h-16 shrink-0 items-center justify-between gap-4 border-b border-[var(--color-border-default)] bg-[var(--color-bg-header)] px-4 lg:px-6"
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
        class="relative hidden w-72 items-center rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-secondary)] py-2 pl-9 pr-3 text-left text-sm text-[var(--color-text-muted)] transition-colors duration-fast hover:border-primary-500 md:flex"
        @click="searchStore.open"
      >
        <Search :size="16" class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" />
        <span class="flex-1 truncate">Search projects, documents, forms...</span>
        <kbd class="rounded border border-[var(--color-border-default)] bg-[var(--color-bg-card)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--color-text-muted)]">
          Ctrl K
        </kbd>
      </button>
    </div>

    <div class="flex items-center gap-2">
      <button
        v-if="aiConfigStore.config?.isEnabled !== false"
        type="button"
        class="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--color-text-secondary)] transition-colors duration-fast hover:bg-[var(--color-bg-hover)]"
        aria-label="AI Assistant"
        @click="aiAssistantStore.toggle"
      >
        <Sparkles :size="18" />
      </button>

      <button
        type="button"
        class="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--color-text-secondary)] transition-colors duration-fast hover:bg-[var(--color-bg-hover)]"
        aria-label="Toggle color theme"
        @click="toggleMode"
      >
        <Sun v-if="isDark" :size="18" />
        <Moon v-else :size="18" />
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

      <button
        type="button"
        class="flex items-center gap-2 rounded-lg py-1.5 pl-1.5 pr-3 text-sm font-medium text-[var(--color-text-primary)] transition-colors duration-fast hover:bg-[var(--color-bg-hover)]"
      >
        <span
          class="flex h-7 w-7 items-center justify-center rounded-full bg-primary-100 text-primary-700"
        >
          <User :size="16" />
        </span>
        <span class="hidden sm:inline">Rajan Kumar</span>
      </button>
    </div>
  </header>
</template>
