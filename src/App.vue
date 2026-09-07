<script setup lang="ts">
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import ToastContainer from '@/components/common/ToastContainer.vue'
import ResultDialog from '@/components/common/ResultDialog.vue'
import KnowledgeChatDrawer from '@/components/knowledge/KnowledgeChatDrawer.vue'
import NotificationDrawer from '@/components/notification/NotificationDrawer.vue'
import CommandPalette from '@/components/search/CommandPalette.vue'
import { useIdleLogout } from '@/composables/useIdleLogout'
import { useAuthStore } from '@/stores/authStore'
import { useCompanyStore } from '@/stores/companyStore'
import AuthLayout from '@/layouts/AuthLayout.vue'
import DashboardLayout from '@/layouts/DashboardLayout.vue'
import CustomerPortalLayout from '@/layouts/CustomerPortalLayout.vue'
import SitePortalLayout from '@/layouts/SitePortalLayout.vue'

const route = useRoute()
const { t } = useI18n()
const authStore = useAuthStore()
const companyStore = useCompanyStore()

useIdleLogout()

// Applies whatever brand color Administration > Company has configured
// app-wide (every role, every layout -- not just the admin page itself),
// the moment a session becomes authenticated -- including a page refresh
// that silently restores a session via tryRefresh, not just a fresh
// login. See src/utils/colorScale.ts's applyBrandColor.
watch(
  () => authStore.isAuthenticated,
  (isAuthed) => {
    if (isAuthed) companyStore.loadBranding()
  },
  { immediate: true },
)

const layout = computed(() => {
  if (route.meta.layout === 'customer-portal') return CustomerPortalLayout
  if (route.meta.layout === 'site-portal') return SitePortalLayout
  if (route.meta.layout === 'dashboard') return DashboardLayout
  // Anything else -- including the unmatched start location before the
  // router's initial navigation resolves -- falls back to the unauthenticated
  // shell rather than the dashboard shell, so an unmatched route never
  // flashes authenticated-looking UI.
  return AuthLayout
})
</script>

<template>
  <a href="#main-content" class="skip-link">{{ t('common.skipToMainContent') }}</a>
  <component :is="layout" />
  <ToastContainer />
  <ResultDialog />
  <NotificationDrawer />
  <CommandPalette />
  <KnowledgeChatDrawer />
</template>
