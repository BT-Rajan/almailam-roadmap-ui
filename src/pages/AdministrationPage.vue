<script setup lang="ts">
import AdminModuleCard from '@/components/administration/AdminModuleCard.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { ADMINISTRATION_MODULES } from '@/constants/administrationModules'
</script>

<template>
  <div class="flex flex-col gap-6 p-4 lg:p-6">
    <PageHeader title="Administration" subtitle="Configure and manage ServiceOS across the firm." />

    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <AdminModuleCard v-for="module in ADMINISTRATION_MODULES" :key="module.routeName" :module="module" />
    </div>
  </div>
</template>
