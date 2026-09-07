<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import ToastContainer from '@/components/common/ToastContainer.vue'
import ResultDialog from '@/components/common/ResultDialog.vue'
import KnowledgeChatDrawer from '@/components/knowledge/KnowledgeChatDrawer.vue'
import NotificationDrawer from '@/components/notification/NotificationDrawer.vue'
import CommandPalette from '@/components/search/CommandPalette.vue'
import { useIdleLogout } from '@/composables/useIdleLogout'
import { useCompanyStore } from '@/stores/companyStore'
import AuthLayout from '@/layouts/AuthLayout.vue'
import DashboardLayout from '@/layouts/DashboardLayout.vue'
import CustomerPortalLayout from '@/layouts/CustomerPortalLayout.vue'
import SitePortalLayout from '@/layouts/SitePortalLayout.vue'

const route = useRoute()
const { t } = useI18n()
const companyStore = useCompanyStore()

useIdleLogout()

// Applies whatever brand color/logo Administration > Company has
// configured app-wide -- every role, every layout, AND the sign-in
// screen itself, since GET /api/company/branding is fully public (no
// session needed). Loaded once at boot, not gated on auth state --
// there's no "wait for login" case to handle. See
// src/utils/colorScale.ts's applyBrandColor.
onMounted(() => companyStore.loadBranding())

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
