<script setup lang="ts">
import { LogOut, X } from '@lucide/vue'
import { useRouter } from 'vue-router'

import SidebarItem from '@/components/navigation/SidebarItem.vue'
import { PRIMARY_NAV_ITEMS } from '@/constants/navigation'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'
import { useNavigationStore } from '@/stores/navigationStore'

const router = useRouter()
const authStore = useAuthStore()
const navigationStore = useNavigationStore()

function handleLogout(): void {
  navigationStore.closeMobileSidebar()
  authStore.logout()
  router.push({ name: ROUTE_NAMES.LOGIN })
}
</script>

<template>
  <Transition name="fade">
    <div
      v-if="navigationStore.isMobileSidebarOpen"
      class="fixed inset-0 z-drawer bg-neutral-900/40 lg:hidden"
      @click="navigationStore.closeMobileSidebar"
    />
  </Transition>

  <Transition name="slide">
    <aside
      v-if="navigationStore.isMobileSidebarOpen"
      class="fixed inset-y-0 left-0 z-drawer flex w-70 flex-col bg-[var(--color-bg-sidebar)] lg:hidden"
    >
      <div class="flex h-16 items-center justify-between border-b border-[var(--color-border-default)] px-4">
        <div class="flex items-center gap-2">
          <div
            class="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-600 text-sm font-semibold text-white"
          >
            SO
          </div>
          <span class="text-base font-semibold text-[var(--color-text-primary)]">ServiceOS</span>
        </div>
        <button
          type="button"
          class="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)]"
          aria-label="Close navigation menu"
          @click="navigationStore.closeMobileSidebar"
        >
          <X :size="20" />
        </button>
      </div>

      <nav class="flex-1 space-y-1 overflow-y-auto px-3 py-4" @click="navigationStore.closeMobileSidebar">
        <SidebarItem v-for="item in PRIMARY_NAV_ITEMS" :key="item.routeName" :item="item" />
      </nav>

      <div class="border-t border-[var(--color-border-default)] p-3">
        <button
          type="button"
          class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-[var(--color-text-secondary)] transition-colors duration-fast hover:bg-danger-50 hover:text-danger-500"
          @click="handleLogout"
        >
          <LogOut :size="18" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  </Transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--tw-duration, 200ms) ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 200ms ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(-100%);
}
</style>
