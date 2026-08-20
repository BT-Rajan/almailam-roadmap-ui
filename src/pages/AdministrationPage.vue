<script setup lang="ts">
import AdminModuleCard from '@/components/administration/AdminModuleCard.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { ADMINISTRATION_MODULE_GROUPS } from '@/constants/administrationModules'
</script>

<template>
  <div class="flex flex-col gap-8 p-4 lg:p-6">
    <PageHeader title="Administration" subtitle="Configure and manage ServiceOS across the firm." />

    <section v-for="group in ADMINISTRATION_MODULE_GROUPS" :key="group.label" class="flex flex-col gap-3">
      <div>
        <h2 class="text-sm font-semibold text-neutral-800">{{ group.label }}</h2>
        <p class="text-xs text-neutral-500">{{ group.description }}</p>
      </div>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <AdminModuleCard v-for="module in group.modules" :key="module.routeName" :module="module" />
      </div>
    </section>
  </div>
</template>
