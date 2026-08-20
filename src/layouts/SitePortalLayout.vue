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
  router.push({ name: ROUTE_NAMES.SITE_PORTAL_LOGIN })
}

const isLoginPage = () => route.name === ROUTE_NAMES.SITE_PORTAL_LOGIN
</script>

<template>
  <div class="flex min-h-screen flex-col bg-bg-secondary">
    <header class="sticky top-0 z-sticky border-b border-border-light bg-bg-header shadow-glass-sm backdrop-blur-xl">
      <div class="mx-auto flex max-w-2xl items-center justify-between px-4 py-4">
        <div class="flex items-center gap-2">
          <div class="gradient-luxe flex h-10 w-10 items-center justify-center rounded-lg text-sm font-semibold text-white shadow-glass-sm">
            SO
          </div>
          <div class="text-left">
            <p class="text-sm font-semibold text-text-primary">Site Engineer Portal</p>
            <p class="text-xs text-text-muted">Almailam Engineering Consultants</p>
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

      <nav v-if="!isLoginPage()" class="mx-auto flex max-w-2xl gap-1 px-4">
        <RouterLink
          :to="{ name: ROUTE_NAMES.SITE_PORTAL_REPORT }"
          class="border-b-2 px-3 py-2.5 text-sm font-medium transition-colors"
          :class="route.name === ROUTE_NAMES.SITE_PORTAL_REPORT ? 'border-primary-500 text-primary-600' : 'border-transparent text-text-muted hover:text-text-primary'"
        >
          Today's Report
        </RouterLink>
        <RouterLink
          :to="{ name: ROUTE_NAMES.SITE_PORTAL_CALENDAR }"
          class="border-b-2 px-3 py-2.5 text-sm font-medium transition-colors"
          :class="route.name === ROUTE_NAMES.SITE_PORTAL_CALENDAR ? 'border-primary-500 text-primary-600' : 'border-transparent text-text-muted hover:text-text-primary'"
        >
          My Reports
        </RouterLink>
      </nav>
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
