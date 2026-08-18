<script setup lang="ts">
import { Download, MessageSquare, Sparkles } from '@lucide/vue'
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import MetadataPanel from '@/components/document/MetadataPanel.vue'
import PDFViewer from '@/components/document/PDFViewer.vue'
import VersionHistory from '@/components/document/VersionHistory.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useDocumentStore } from '@/stores/documentStore'
import { useToastStore } from '@/stores/toastStore'
import type { DocumentVersion } from '@/types/Document'

const route = useRoute()
const router = useRouter()
const documentStore = useDocumentStore()
const toastStore = useToastStore()

const documentId = computed(() => route.params.documentId as string)

const projectName = computed(
  () => documentStore.getProjectById(documentStore.currentDocument?.projectId ?? '')?.projectName ?? 'Unknown Project',
)

function loadData(): void {
  documentStore.loadDocumentDetail(documentId.value)
}

onMounted(loadData)
watch(documentId, loadData)

function openReview(): void {
  router.push({ name: ROUTE_NAMES.DOCUMENT_REVIEW, params: { documentId: documentId.value } })
}

async function handleDownload(): Promise<void> {
  try {
    await documentStore.downloadCurrentDocument()
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to download document', detail)
  }
}

async function handleDownloadVersion(version: DocumentVersion): Promise<void> {
  try {
    await documentStore.downloadVersion(version.id, version.originalFilename)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to download version', detail)
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader
      :title="documentStore.currentDocument?.title ?? 'Document Viewer'"
      :subtitle="documentStore.currentDocument ? `${documentStore.currentDocument.type} · ${documentStore.currentDocument.revision}` : undefined"
    >
      <template v-if="documentStore.currentDocument" #actions>
        <BaseButton :icon="Download" variant="secondary" @click="handleDownload">Download</BaseButton>
        <BaseButton :icon="Sparkles" variant="secondary" @click="openReview">AI Review</BaseButton>
      </template>
    </PageHeader>

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
        <VersionHistory :versions="documentStore.currentVersions" @download="handleDownloadVersion" />
      </div>
    </div>
  </div>
</template>
