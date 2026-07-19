<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import ToastContainer from '@/components/common/ToastContainer.vue'
import NotificationDrawer from '@/components/notification/NotificationDrawer.vue'
import CommandPalette from '@/components/search/CommandPalette.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'
import DashboardLayout from '@/layouts/DashboardLayout.vue'
import CustomerPortalLayout from '@/layouts/CustomerPortalLayout.vue'

const route = useRoute()

const layout = computed(() => {
  if (route.meta.layout === 'auth') return AuthLayout
  if (route.meta.layout === 'customer-portal') return CustomerPortalLayout
  return DashboardLayout
})
</script>

<template>
  <a href="#main-content" class="skip-link">Skip to main content</a>
  <component :is="layout" />
  <ToastContainer />
  <NotificationDrawer />
  <CommandPalette />
</template>
