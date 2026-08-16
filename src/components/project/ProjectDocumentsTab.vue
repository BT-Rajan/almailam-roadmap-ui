<script setup lang="ts">
import { Upload } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import DocumentCard from '@/components/document/DocumentCard.vue'
import DocumentUploadDialog from '@/components/document/DocumentUploadDialog.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useDocumentStore } from '@/stores/documentStore'
import { useToastStore } from '@/stores/toastStore'
import type { ProjectDocument } from '@/types/Document'
import type { Project } from '@/types/Project'

const props = defineProps<{
  project: Project
  mode: 'documents' | 'design'
}>()

const router = useRouter()
const documentStore = useDocumentStore()
const toastStore = useToastStore()

const isUploadOpen = ref(false)

const projectDocuments = computed(() => documentStore.documentsByProject(props.project.id))
const visibleDocuments = computed(() =>
  props.mode === 'documents'
    ? projectDocuments.value
    : projectDocuments.value.filter((document) => document.type === 'Drawing'),
)

function handleUpload(document: ProjectDocument): void {
  toastStore.show('success', 'Document uploaded', `${document.title} was added to the repository.`)
  isUploadOpen.value = false
}

function openDocument(documentId: string): void {
  router.push({ name: ROUTE_NAMES.DOCUMENT_VIEWER, params: { documentId } })
}
</script>

<template>
  <div class="flex items-center justify-end">
    <BaseButton
      v-if="mode === 'documents'"
      variant="secondary"
      size="sm"
      :icon="Upload"
      class="no-print"
      @click="isUploadOpen = true"
    >
      Upload Document
    </BaseButton>
  </div>

  <div v-if="documentStore.isLoading" class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
    <div v-for="placeholder in 3" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="5" />
    </div>
  </div>

  <ErrorState v-else-if="documentStore.error" :description="documentStore.error" @retry="documentStore.loadDocuments" />

  <EmptyState
    v-else-if="visibleDocuments.length === 0"
    title="No documents yet"
    :description="
      mode === 'documents'
        ? 'Documents uploaded for this project will appear here.'
        : 'Design drawings uploaded for this project will appear here.'
    "
  />

  <div v-else class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
    <DocumentCard
      v-for="document in visibleDocuments"
      :key="document.id"
      :document="document"
      :project="project"
      @open="openDocument"
    />
  </div>

  <DocumentUploadDialog v-model="isUploadOpen" :projects="[project]" @upload="handleUpload" />
</template>
