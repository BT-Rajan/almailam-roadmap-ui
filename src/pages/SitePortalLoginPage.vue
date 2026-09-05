<script setup lang="ts">
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
  await router.push(redirect ?? { name: ROUTE_NAMES.SITE_PORTAL_REPORT })
}
</script>

<template>
  <AuthCard :title="t('sitePortal.loginPage.title')" :subtitle="t('sitePortal.loginPage.subtitle')">
    <StaffLoginForm
      :id-label="t('sitePortal.loginPage.idLabel')"
      :id-placeholder="t('sitePortal.loginPage.idPlaceholder')"
      :login-fn="authStore.login"
      :initial-message="initialMessage"
      @success="handleSuccess"
    />
  </AuthCard>
</template>
