<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

function signIn() {
  authStore.login()
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : undefined
  router.push(redirect ?? { name: ROUTE_NAMES.DASHBOARD })
}
</script>

<template>
  <div>
    <h1 class="text-xl font-semibold text-[var(--color-text-primary)]">Sign in</h1>
    <p class="mt-1 text-sm text-[var(--color-text-secondary)]">
      Access the ServiceOS engineering consultancy workspace.
    </p>

    <button
      type="button"
      class="mt-6 w-full rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors duration-fast hover:bg-primary-700"
      @click="signIn"
    >
      Sign In (Demo)
    </button>

    <p class="mt-4 text-center text-xs text-[var(--color-text-muted)]">
      Authentication form arrives in a future pass. This demo button unlocks the prototype.
    </p>
  </div>
</template>
