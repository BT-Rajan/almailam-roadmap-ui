<script setup lang="ts">
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
  await router.push(redirect ?? { name: ROUTE_NAMES.SITE_PORTAL_REPORT })
}
</script>

<template>
  <AuthCard title="Site Engineer Sign In" subtitle="File your daily status report and view your report history.">
    <StaffLoginForm
      id-label="Employee ID"
      id-placeholder="Enter your Employee ID"
      :login-fn="authStore.loginWithEmployeeId"
      :initial-message="initialMessage"
      @success="handleSuccess"
    />
  </AuthCard>
</template>
