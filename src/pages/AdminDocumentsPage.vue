<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import PageHeader from '@/components/common/PageHeader.vue'
import DocumentTabs from '@/components/administration/DocumentTabs.vue'
import type { DocumentTab, DocumentTabKey } from '@/components/administration/DocumentTabs.vue'
import DocumentTemplatesPanel from '@/components/administration/DocumentTemplatesPanel.vue'
import GovernmentFormsPanel from '@/components/administration/GovernmentFormsPanel.vue'
import ServiceDocumentMapPanel from '@/components/administration/ServiceDocumentMapPanel.vue'

const { t } = useI18n()

const TABS = computed<DocumentTab[]>(() => [
  { key: 'forms', label: t('administration.adminDocumentsPage.formsTab') },
  { key: 'serviceMap', label: t('administration.adminDocumentsPage.serviceMapTab') },
  { key: 'templates', label: t('administration.adminDocumentsPage.templatesTab') },
])

const SUBTITLES = computed<Record<DocumentTabKey, string>>(() => ({
  forms: t('administration.adminDocumentsPage.formsSubtitle'),
  serviceMap: t('administration.adminDocumentsPage.serviceMapSubtitle'),
  templates: t('administration.adminDocumentsPage.templatesSubtitle'),
}))

const activeTab = ref<DocumentTabKey>('forms')
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader :title="t('administration.adminDocumentsPage.pageTitle')" :subtitle="SUBTITLES[activeTab]" />

    <DocumentTabs :tabs="TABS" :active-tab="activeTab" @select="activeTab = $event" />

    <div v-if="activeTab === 'forms'" id="document-tabpanel-forms" role="tabpanel" aria-labelledby="document-tab-forms">
      <GovernmentFormsPanel />
    </div>
    <div v-else-if="activeTab === 'serviceMap'" id="document-tabpanel-serviceMap" role="tabpanel" aria-labelledby="document-tab-serviceMap">
      <ServiceDocumentMapPanel />
    </div>
    <div v-else-if="activeTab === 'templates'" id="document-tabpanel-templates" role="tabpanel" aria-labelledby="document-tab-templates">
      <DocumentTemplatesPanel />
    </div>
  </div>
</template>
