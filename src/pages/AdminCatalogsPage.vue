<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import PageHeader from '@/components/common/PageHeader.vue'
import CatalogTabs from '@/components/administration/CatalogTabs.vue'
import type { CatalogTab, CatalogTabKey } from '@/components/administration/CatalogTabs.vue'
import ServiceCatalogPanel from '@/components/administration/ServiceCatalogPanel.vue'
import PermitCatalogPanel from '@/components/administration/PermitCatalogPanel.vue'
import DocumentRequirementsPanel from '@/components/administration/DocumentRequirementsPanel.vue'

const { t } = useI18n()

const TABS = computed<CatalogTab[]>(() => [
  { key: 'services', label: t('administration.catalogsPage.servicesTab') },
  { key: 'permits', label: t('administration.catalogsPage.permitsTab') },
  { key: 'documents', label: t('administration.catalogsPage.documentsTab') },
])

const SUBTITLES = computed<Record<CatalogTabKey, string>>(() => ({
  services: t('administration.catalogsPage.servicesSubtitle'),
  permits: t('administration.catalogsPage.permitsSubtitle'),
  documents: t('administration.catalogsPage.documentsSubtitle'),
}))

const activeTab = ref<CatalogTabKey>('services')
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader :title="t('administration.catalogsPage.pageTitle')" :subtitle="SUBTITLES[activeTab]" />

    <CatalogTabs :tabs="TABS" :active-tab="activeTab" @select="activeTab = $event" />

    <div v-if="activeTab === 'services'" id="catalog-tabpanel-services" role="tabpanel" aria-labelledby="catalog-tab-services">
      <ServiceCatalogPanel />
    </div>
    <div v-else-if="activeTab === 'permits'" id="catalog-tabpanel-permits" role="tabpanel" aria-labelledby="catalog-tab-permits">
      <PermitCatalogPanel />
    </div>
    <div v-else-if="activeTab === 'documents'" id="catalog-tabpanel-documents" role="tabpanel" aria-labelledby="catalog-tab-documents">
      <DocumentRequirementsPanel />
    </div>
  </div>
</template>
