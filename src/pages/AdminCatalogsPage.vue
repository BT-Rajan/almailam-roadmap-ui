<script setup lang="ts">
import { ref } from 'vue'

import PageHeader from '@/components/common/PageHeader.vue'
import CatalogTabs from '@/components/administration/CatalogTabs.vue'
import type { CatalogTab, CatalogTabKey } from '@/components/administration/CatalogTabs.vue'
import ServiceCatalogPanel from '@/components/administration/ServiceCatalogPanel.vue'
import TypeActivityCatalogPanel from '@/components/administration/TypeActivityCatalogPanel.vue'
import PermitCatalogPanel from '@/components/administration/PermitCatalogPanel.vue'

const TABS: CatalogTab[] = [
  { key: 'services', label: 'Service Catalog' },
  { key: 'activities', label: 'Additional Activity Catalog' },
  { key: 'permits', label: 'Permit Catalog' },
]

const SUBTITLES: Record<CatalogTabKey, string> = {
  services: "Configure the services offered and each service's activities and fixed costs.",
  activities:
    'Configure the engagement type categories (Design, Supervision, etc) offered at project creation, and each category\'s checklist of priced additional activities.',
  permits: 'Configure the permits that can be attached to a project during setup.',
}

const activeTab = ref<CatalogTabKey>('services')
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader title="Catalogs" :subtitle="SUBTITLES[activeTab]" />

    <CatalogTabs :tabs="TABS" :active-tab="activeTab" @select="activeTab = $event" />

    <div v-if="activeTab === 'services'" id="catalog-tabpanel-services" role="tabpanel" aria-labelledby="catalog-tab-services">
      <ServiceCatalogPanel />
    </div>
    <div v-else-if="activeTab === 'activities'" id="catalog-tabpanel-activities" role="tabpanel" aria-labelledby="catalog-tab-activities">
      <TypeActivityCatalogPanel />
    </div>
    <div v-else-if="activeTab === 'permits'" id="catalog-tabpanel-permits" role="tabpanel" aria-labelledby="catalog-tab-permits">
      <PermitCatalogPanel />
    </div>
  </div>
</template>
