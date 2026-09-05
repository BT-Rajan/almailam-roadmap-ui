<script setup lang="ts">
import { LogOut } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'

import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

async function handleLogout(): Promise<void> {
  await authStore.logout()
  router.push({ name: ROUTE_NAMES.CUSTOMER_PORTAL_LOGIN })
}

// Same app-shell chrome as the Site Engineer Portal (see
// SitePortalLayout) -- one header pattern shared by both portals
// instead of two different ones, and Logout lives here once instead
// of being duplicated on every page.
const isLoginPage = () => route.name === ROUTE_NAMES.CUSTOMER_PORTAL_LOGIN
</script>

<template>
  <div class="flex min-h-screen flex-col bg-bg-secondary">
    <header class="sticky top-0 z-sticky border-b border-border-light bg-bg-header shadow-glass-sm backdrop-blur-xl">
      <div class="mx-auto flex max-w-2xl items-center justify-between px-4 py-4">
        <div class="flex items-center gap-2">
          <div class="gradient-luxe-accent flex h-10 w-10 items-center justify-center rounded-lg text-sm font-semibold text-white shadow-glass-sm">
            SO
          </div>
          <div class="text-start">
            <p class="text-sm font-semibold text-text-primary">Customer Portal</p>
            <p class="hidden text-xs text-text-muted tablet:block">Almailam Engineering Consultants</p>
          </div>
        </div>
        <button
          v-if="!isLoginPage()"
          type="button"
          class="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-text-muted transition-colors hover:bg-bg-hover hover:text-text-primary"
          @click="handleLogout"
        >
          <LogOut class="h-4 w-4" />
          Log Out
        </button>
      </div>
    </header>

    <main id="main-content" tabindex="-1" class="mx-auto w-full max-w-2xl flex-1 px-4 py-6 outline-none">
      <RouterView v-slot="{ Component }">
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>
  </div>
</template>
