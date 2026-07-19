<script setup lang="ts">
import { Bell, Menu, Moon, Search, Sun, User } from '@lucide/vue'

import { useTheme } from '@/composables/useTheme'
import { useNavigationStore } from '@/stores/navigationStore'

const navigationStore = useNavigationStore()
const { isDark, toggleMode } = useTheme()
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

      <label class="relative hidden md:block">
        <Search
          :size="16"
          class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]"
        />
        <input
          type="text"
          placeholder="Search projects, documents, forms..."
          class="w-72 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-bg-secondary)] py-2 pl-9 pr-3 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
        />
      </label>
    </div>

    <div class="flex items-center gap-2">
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
      >
        <Bell :size="18" />
        <span
          class="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-danger-500"
          aria-hidden="true"
        />
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
