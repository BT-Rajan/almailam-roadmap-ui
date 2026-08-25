<script setup lang="ts">
import { Download, MessageSquare, Plus, RefreshCw, Sparkles, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import IconButton from '@/components/common/IconButton.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import AddVersionDialog from '@/components/document/AddVersionDialog.vue'
import DocumentStatusDialog from '@/components/document/DocumentStatusDialog.vue'
import MetadataPanel from '@/components/document/MetadataPanel.vue'
import PDFViewer from '@/components/document/PDFViewer.vue'
import VersionHistory from '@/components/document/VersionHistory.vue'
import { PROCESS_STAGES } from '@/constants/processStages'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { approvalProcessService } from '@/services/approvalProcessService'
import { documentService } from '@/services/documentService'
import { useDocumentStore } from '@/stores/documentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useToastStore } from '@/stores/toastStore'
import type { DocumentStatus, DocumentVersion } from '@/types/Document'

const route = useRoute()
const router = useRouter()
const documentStore = useDocumentStore()
const projectStore = useProjectStore()
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

const isStatusDialogOpen = ref(false)
const isStatusSaving = ref(false)

// After a document tagged to one of the 5 Project Approval Process
// stages (see constants/processStages.ts) is marked Approved, offer
// to confirm that stage complete -- whether every document tagged to
// it is now Approved or only some are ("either way" a confirmation is
// asked; approving one doc doesn't silently complete the stage on its
// own). Skipped entirely if the stage is already complete via either
// path (gate document uploaded, or a prior document-approval
// confirmation), so this doesn't re-prompt every time.
interface StageCompletionContext {
  projectId: string
  stageKey: string
  stageLabel: string
  approvedCount: number
  totalCount: number
}

const isStageCompleteDialogOpen = ref(false)
const isCompletingStage = ref(false)
const stageCompletionContext = ref<StageCompletionContext>()

const stageCompletionMessage = computed(() => {
  const ctx = stageCompletionContext.value
  if (!ctx) return ''
  return ctx.approvedCount === ctx.totalCount
    ? `All ${ctx.totalCount} document(s) tagged to "${ctx.stageLabel}" are now Approved. Mark this stage as complete?`
    : `${ctx.approvedCount} of ${ctx.totalCount} document(s) tagged to "${ctx.stageLabel}" are Approved. Mark this stage as complete anyway?`
})

async function maybePromptStageCompletion(): Promise<void> {
  const doc = documentStore.currentDocument
  if (!doc?.stageKey) return

  try {
    const [steps, stageDocuments] = await Promise.all([
      approvalProcessService.getProjectSteps(doc.projectId),
      documentService.getDocumentsByProject(doc.projectId),
    ])
    const step = steps.find((s) => s.stageKey === doc.stageKey)
    if (step?.isComplete) return

    const tagged = stageDocuments.filter((d) => d.stageKey === doc.stageKey)
    if (tagged.length === 0) return

    stageCompletionContext.value = {
      projectId: doc.projectId,
      stageKey: doc.stageKey,
      stageLabel: PROCESS_STAGES.find((s) => s.key === doc.stageKey)?.label ?? doc.stageKey,
      approvedCount: tagged.filter((d) => d.status === 'Approved').length,
      totalCount: tagged.length,
    }
    isStageCompleteDialogOpen.value = true
  } catch {
    // Non-critical -- the status change the user already confirmed
    // already succeeded; skip the prompt silently rather than
    // blocking on this secondary check.
  }
}

async function handleConfirmStageCompletion(): Promise<void> {
  const ctx = stageCompletionContext.value
  if (!ctx) return
  isCompletingStage.value = true
  try {
    await approvalProcessService.completeStageFromDocuments(ctx.projectId, ctx.stageKey)
    // Stage gates can move project.currentStage (and its progress) on
    // the backend -- refresh the cached project so the workflow stepper
    // and progress bar reflect it immediately instead of on next reload.
    await projectStore.refreshProject(ctx.projectId)
    toastStore.show('success', 'Stage marked complete', `"${ctx.stageLabel}" is now marked complete.`)
    isStageCompleteDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to mark stage complete', detail)
  } finally {
    isCompletingStage.value = false
  }
}

async function handleStatusConfirm(payload: { status: DocumentStatus; reason?: string }): Promise<void> {
  isStatusSaving.value = true
  try {
    await documentStore.setCurrentDocumentStatus(payload.status, payload.reason)
    toastStore.show('success', 'Status updated', `Document marked as ${payload.status}.`)
    isStatusDialogOpen.value = false
    if (payload.status === 'Approved') {
      await maybePromptStageCompletion()
    }
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to update status', detail)
  } finally {
    isStatusSaving.value = false
  }
}

const isAddVersionOpen = ref(false)
const isAddingVersion = ref(false)

async function handleAddVersion(payload: { file: File; notes?: string }): Promise<void> {
  isAddingVersion.value = true
  try {
    await documentStore.addCurrentDocumentVersion(payload.file, payload.notes)
    toastStore.show('success', 'New version added', 'The document was updated to a new revision.')
    isAddVersionOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to add new version', detail)
  } finally {
    isAddingVersion.value = false
  }
}

const isDeleteDialogOpen = ref(false)
const isDeleting = ref(false)

async function handleDelete(): Promise<void> {
  isDeleting.value = true
  try {
    await documentStore.deleteCurrentDocument()
    toastStore.show('success', 'Document deleted', 'The document was removed.')
    router.push({ name: ROUTE_NAMES.DOCUMENTS })
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to delete document', detail)
  } finally {
    isDeleting.value = false
    isDeleteDialogOpen.value = false
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
        <BaseButton :icon="RefreshCw" variant="secondary" @click="isStatusDialogOpen = true">Status</BaseButton>
        <BaseButton :icon="Plus" variant="secondary" @click="isAddVersionOpen = true">Add Version</BaseButton>
        <BaseButton :icon="Sparkles" variant="secondary" @click="openReview">AI Review</BaseButton>
        <IconButton :icon="Trash2" label="Delete document" @click="isDeleteDialogOpen = true" />
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
            <h3 class="text-sm font-semibold text-text-primary">Comments</h3>
          </template>
          <EmptyState :icon="MessageSquare" title="No comments yet" description="Comment threads for this document will appear here." />
        </Card>
      </div>

      <div class="flex flex-col gap-6">
        <MetadataPanel :document="documentStore.currentDocument" :project-name="projectName" />
        <VersionHistory :versions="documentStore.currentVersions" @download="handleDownloadVersion" />
      </div>
    </div>

    <DocumentStatusDialog
      v-if="documentStore.currentDocument"
      v-model="isStatusDialogOpen"
      :current-status="documentStore.currentDocument.status"
      :loading="isStatusSaving"
      @confirm="handleStatusConfirm"
    />
    <AddVersionDialog v-model="isAddVersionOpen" :loading="isAddingVersion" @confirm="handleAddVersion" />
    <ConfirmationDialog
      v-model="isStageCompleteDialogOpen"
      title="Mark stage complete?"
      :message="stageCompletionMessage"
      confirm-label="Mark Complete"
      :loading="isCompletingStage"
      @confirm="handleConfirmStageCompletion"
    />
    <ConfirmationDialog
      v-model="isDeleteDialogOpen"
      title="Delete document"
      :message="`Delete ${documentStore.currentDocument?.title}? This cannot be undone from the app.`"
      confirm-label="Delete"
      confirm-variant="danger"
      :loading="isDeleting"
      @confirm="handleDelete"
    />
  </div>
</template>
