<script setup lang="ts">
import { ShieldCheck } from '@lucide/vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import AuthCard from '@/components/auth/AuthCard.vue'
import StaffLoginForm from '@/components/auth/StaffLoginForm.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'

const { t } = useI18n()
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
  <AuthCard :title="t('customer.loginPage.title')" :subtitle="t('customer.loginPage.subtitle')">
    <StaffLoginForm
      :id-label="t('customer.loginPage.idLabel')"
      :id-placeholder="t('customer.loginPage.idPlaceholder')"
      :login-fn="authStore.login"
      :initial-message="initialMessage"
      @success="handleSuccess"
    />

    <template #footer>
      <p class="flex items-center justify-center gap-1.5 text-center text-xs text-text-muted">
        <ShieldCheck class="h-3.5 w-3.5 shrink-0 text-text-muted" />
        {{ t('customer.loginPage.footerNotice') }}
      </p>
    </template>
  </AuthCard>
</template>
