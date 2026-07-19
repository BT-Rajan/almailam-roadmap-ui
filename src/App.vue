<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import AuthLayout from '@/layouts/AuthLayout.vue'
import DashboardLayout from '@/layouts/DashboardLayout.vue'

const route = useRoute()

const layout = computed(() => (route.meta.layout === 'auth' ? AuthLayout : DashboardLayout))
</script>

<template>
  <component :is="layout" />
</template>
