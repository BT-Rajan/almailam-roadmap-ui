<script setup lang="ts">
import { ShieldCheck } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'

import AuthCard from '@/components/auth/AuthCard.vue'
import StaffLoginForm from '@/components/auth/StaffLoginForm.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const initialMessage = typeof route.query.reason === 'string' ? route.query.reason : undefined

async function handleSuccess(): Promise<void> {
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : undefined
  await router.push(redirect ?? { name: ROUTE_NAMES.CUSTOMER_PORTAL_PROJECTS })
}
</script>

<template>
  <AuthCard title="Track Your Project" subtitle="Sign in with your Customer ID to view live progress, milestones, and deliverables.">
    <StaffLoginForm
      id-label="Customer ID"
      id-placeholder="Enter your Customer ID"
      :login-fn="authStore.login"
      :initial-message="initialMessage"
      @success="handleSuccess"
    />

    <template #footer>
      <p class="flex items-center justify-center gap-1.5 text-center text-xs text-text-muted">
        <ShieldCheck class="h-3.5 w-3.5 shrink-0 text-text-muted" />
        Only you can view your project, verified against your Customer ID and password.
      </p>
    </template>
  </AuthCard>
</template>
