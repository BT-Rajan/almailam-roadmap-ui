<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push({ name: 'customer-portal' })
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-primary-50 to-info-50">
    <!-- Header -->
    <header class="border-b border-border-light bg-white shadow-soft">
      <div class="max-w-7xl mx-auto px-4 tablet:px-6 py-4 flex items-center justify-between">
        <button class="flex items-center gap-2 hover:opacity-80 transition-opacity" @click="goHome">
          <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-600 text-sm font-semibold text-white">
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
    <main class="flex-1">
      <RouterView />
    </main>

    <!-- Footer -->
    <footer class="border-t border-border-light bg-white py-6 mt-12">
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
