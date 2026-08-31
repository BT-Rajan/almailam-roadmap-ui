<script setup lang="ts">
import { ref } from 'vue'

import PageHeader from '@/components/common/PageHeader.vue'
import DocumentTabs from '@/components/administration/DocumentTabs.vue'
import type { DocumentTab, DocumentTabKey } from '@/components/administration/DocumentTabs.vue'
import DocumentTemplatesPanel from '@/components/administration/DocumentTemplatesPanel.vue'
import GovernmentFormsPanel from '@/components/administration/GovernmentFormsPanel.vue'
import ServiceDocumentMapPanel from '@/components/administration/ServiceDocumentMapPanel.vue'

const TABS: DocumentTab[] = [
  { key: 'forms', label: 'Government Forms' },
  { key: 'serviceMap', label: 'Service Document Map' },
  { key: 'templates', label: 'Quotation & Contract Templates' },
]

const SUBTITLES: Record<DocumentTabKey, string> = {
  forms: 'Maintain authorities, forms and their document requirements.',
  serviceMap:
    'For each service, which fillable government forms/agreements a project needs. Staff fill these in from the project itself (Approvals & Permits) -- this only controls which ones are offered there.',
  templates: 'Upload the .docx templates used to generate Quotation and Contract documents, and choose the default for each.',
}

const activeTab = ref<DocumentTabKey>('forms')
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader title="Documents" :subtitle="SUBTITLES[activeTab]" />

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
