<script setup lang="ts">
import { MessageSquare } from '@lucide/vue'
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import MetadataPanel from '@/components/document/MetadataPanel.vue'
import PDFViewer from '@/components/document/PDFViewer.vue'
import VersionHistory from '@/components/document/VersionHistory.vue'
import { useDocumentStore } from '@/stores/documentStore'

const route = useRoute()
const documentStore = useDocumentStore()

const documentId = computed(() => route.params.documentId as string)

const projectName = computed(
  () => documentStore.getProjectById(documentStore.currentDocument?.projectId ?? '')?.projectName ?? 'Unknown Project',
)

function loadData(): void {
  documentStore.loadDocumentDetail(documentId.value)
}

onMounted(loadData)
watch(documentId, loadData)
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader
      :title="documentStore.currentDocument?.title ?? 'Document Viewer'"
      :subtitle="documentStore.currentDocument ? `${documentStore.currentDocument.type} · ${documentStore.currentDocument.revision}` : undefined"
    />

    <ErrorState v-if="documentStore.error" :description="documentStore.error" @retry="loadData" />

    <div v-else-if="documentStore.isDetailLoading" class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="rounded-xl border border-border-light bg-bg-card p-5 laptop:col-span-2">
        <SkeletonLoader :rows="8" />
      </div>
      <div class="flex flex-col gap-6">
        <div class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="6" />
        </div>
        <div class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="4" />
        </div>
      </div>
    </div>

    <EmptyState v-else-if="!documentStore.currentDocument" title="Document not found" description="This document may have been removed or the link is incorrect." />

    <div v-else class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="flex flex-col gap-6 laptop:col-span-2">
        <PDFViewer :title="documentStore.currentDocument.title" />

        <Card>
          <template #header>
            <h3 class="text-sm font-semibold text-neutral-800">Comments</h3>
          </template>
          <EmptyState :icon="MessageSquare" title="No comments yet" description="Comment threads for this document will appear here." />
        </Card>
      </div>

      <div class="flex flex-col gap-6">
        <MetadataPanel :document="documentStore.currentDocument" :project-name="projectName" />
        <VersionHistory :versions="documentStore.currentVersions" />
      </div>
    </div>
  </div>
</template>
