<script setup lang="ts">
import { Upload } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import DocumentCard from '@/components/document/DocumentCard.vue'
import DocumentEditDialog from '@/components/document/DocumentEditDialog.vue'
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

const isEditDialogOpen = ref(false)
const isEditSaving = ref(false)
const editTarget = ref<ProjectDocument | null>(null)

const isDeleteDialogOpen = ref(false)
const isDeleteSaving = ref(false)
const deleteTarget = ref<ProjectDocument | null>(null)

function openEditDialog(document: ProjectDocument): void {
  editTarget.value = document
  isEditDialogOpen.value = true
}

async function handleConfirmEdit(payload: { title: string }): Promise<void> {
  if (!editTarget.value) return
  isEditSaving.value = true
  try {
    await documentStore.updateDocument(editTarget.value.id, payload.title)
    toastStore.show('success', 'Document updated', 'Changes were saved successfully.')
    isEditDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to update document', detail)
  } finally {
    isEditSaving.value = false
  }
}

function requestDelete(document: ProjectDocument): void {
  deleteTarget.value = document
  isDeleteDialogOpen.value = true
}

async function handleConfirmDelete(): Promise<void> {
  if (!deleteTarget.value) return
  isDeleteSaving.value = true
  try {
    await documentStore.deleteDocument(deleteTarget.value.id)
    toastStore.show('success', 'Document deleted', `${deleteTarget.value.title} was removed.`)
    isDeleteDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to delete document', detail)
  } finally {
    isDeleteSaving.value = false
  }
}

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
      @edit="openEditDialog"
      @delete="requestDelete"
    />
  </div>

  <DocumentUploadDialog v-model="isUploadOpen" :projects="[project]" @upload="handleUpload" />
  <DocumentEditDialog
    v-model="isEditDialogOpen"
    :document="editTarget"
    :loading="isEditSaving"
    @confirm="handleConfirmEdit"
  />
  <ConfirmationDialog
    v-model="isDeleteDialogOpen"
    title="Delete document"
    :message="deleteTarget ? `Delete ${deleteTarget.title}? This cannot be undone from the app.` : ''"
    confirm-label="Delete"
    confirm-variant="danger"
    :loading="isDeleteSaving"
    @confirm="handleConfirmDelete"
  />
</template>
