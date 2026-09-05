<script setup lang="ts">
import { X } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import SidebarItem from '@/components/navigation/SidebarItem.vue'
import { useAuth } from '@/composables/useAuthComposable'
import { useLocale } from '@/composables/useLocale'
import { PRIMARY_NAV_ITEMS } from '@/constants/navigation'
import { useNavigationStore } from '@/stores/navigationStore'

const navigationStore = useNavigationStore()
const { isAdmin } = useAuth()
const { t } = useI18n()
const { isRtl } = useLocale()

// Same adminOnly filter as Sidebar.vue -- kept in sync so the mobile drawer
// never shows a link the desktop nav wouldn't.
const visibleNavItems = computed(() => PRIMARY_NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin.value))
</script>

<template>
  <Transition name="fade">
    <div
      v-if="navigationStore.isMobileSidebarOpen"
      class="fixed inset-0 z-drawer bg-neutral-900/40 lg:hidden"
      @click="navigationStore.closeMobileSidebar"
    />
  </Transition>

  <Transition :name="isRtl ? 'slide-from-right' : 'slide-from-left'">
    <aside
      v-if="navigationStore.isMobileSidebarOpen"
      class="fixed inset-y-0 start-0 z-drawer flex w-70 flex-col bg-bg-sidebar shadow-glass lg:hidden"
    >
      <div class="flex h-16 items-center justify-between border-b border-[var(--color-border-default)] px-4">
        <div class="flex items-center gap-2">
          <div
            class="gradient-luxe-accent flex h-9 w-9 items-center justify-center rounded-lg text-sm font-semibold text-white shadow-glass-sm"
          >
            SO
          </div>
          <span class="text-base font-semibold text-[var(--color-text-primary)]">{{ t('common.appName') }}</span>
        </div>
        <button
          type="button"
          class="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)]"
          :aria-label="t('common.closeNavigationMenu')"
          @click="navigationStore.closeMobileSidebar"
        >
          <X :size="20" />
        </button>
      </div>

      <nav class="flex-1 space-y-1 overflow-y-auto px-3 py-4" @click="navigationStore.closeMobileSidebar">
        <SidebarItem v-for="item in visibleNavItems" :key="item.routeName" :item="item" />
      </nav>
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

.slide-from-left-enter-active,
.slide-from-left-leave-active,
.slide-from-right-enter-active,
.slide-from-right-leave-active {
  transition: transform 200ms ease;
}
.slide-from-left-enter-from,
.slide-from-left-leave-to {
  transform: translateX(-100%);
}
.slide-from-right-enter-from,
.slide-from-right-leave-to {
  transform: translateX(100%);
}
</style>
