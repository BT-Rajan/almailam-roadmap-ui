<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push({ name: 'customer-portal' })
}
</script>

<template>
  <div class="min-h-screen">
    <!-- Header -->
    <header class="border-b border-border-light bg-bg-header shadow-glass-sm">
      <div class="max-w-7xl mx-auto px-4 tablet:px-6 py-4 flex items-center justify-between">
        <button class="flex items-center gap-2 hover:opacity-80 transition-opacity" @click="goHome">
          <div class="gradient-luxe flex h-10 w-10 items-center justify-center rounded-lg text-sm font-semibold text-white shadow-glass-sm">
            SO
          </div>
          <div>
            <p class="text-sm font-semibold text-neutral-900">ServiceOS</p>
            <p class="text-xs text-neutral-500">Project Tracking</p>
          </div>
        </button>
        <div class="text-right">
          <p class="text-xs text-neutral-500">Almailam Engineering Consultants</p>
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
        <p class="text-xs text-neutral-500">
          &copy; {{ new Date().getFullYear() }} Almailam Engineering Consultants. All rights reserved.
        </p>
        <p class="text-xs text-neutral-400 mt-2">
          This portal allows clients to track project progress using their mobile number and project ID.
        </p>
      </div>
    </footer>
  </div>
</template>
