<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import ToastContainer from '@/components/common/ToastContainer.vue'
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
  <component :is="layout" />
  <ToastContainer />
</template>
