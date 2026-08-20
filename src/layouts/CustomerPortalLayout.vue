<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ROUTE_NAMES } from '@/constants/routeNames'

const router = useRouter()

const goHome = () => {
  router.push({ name: ROUTE_NAMES.CUSTOMER_PORTAL_LOGIN })
}
</script>

<template>
  <div class="min-h-screen">
    <!-- Header -->
    <header class="sticky top-0 z-sticky border-b border-border-light bg-bg-header shadow-glass-sm backdrop-blur-xl">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 tablet:px-6">
        <button class="flex items-center gap-2 transition-opacity hover:opacity-80" @click="goHome">
          <div class="gradient-luxe flex h-10 w-10 items-center justify-center rounded-lg text-sm font-semibold text-white shadow-glass-sm">
            SO
          </div>
          <div class="text-left">
            <p class="text-sm font-semibold text-text-primary">ServiceOS</p>
            <p class="text-xs text-text-muted">Project Tracking</p>
          </div>
        </button>
        <div class="text-right">
          <p class="text-xs text-text-muted">Almailam Engineering Consultants</p>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main id="main-content" tabindex="-1" class="flex-1 outline-none">
      <RouterView v-slot="{ Component }">
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>

    <!-- Footer -->
    <footer class="border-t border-border-light bg-bg-header py-6 mt-12">
      <div class="max-w-7xl mx-auto px-4 tablet:px-6 text-center">
        <p class="text-xs text-text-muted">
          &copy; {{ new Date().getFullYear() }} Almailam Engineering Consultants. All rights reserved.
        </p>
        <p class="text-xs text-text-muted mt-2">
          This portal allows clients to track project progress using their mobile number and project ID.
        </p>
      </div>
    </footer>
  </div>
</template>
