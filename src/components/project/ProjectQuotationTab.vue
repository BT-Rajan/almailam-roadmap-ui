<script setup lang="ts">
import { ArrowLeftRight, ArrowRight, Download, Lock, LockOpen, Plus, Printer } from '@lucide/vue'
import { computed, ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import NewQuotationDialog from '@/components/project/NewQuotationDialog.vue'
import QuotationList from '@/components/project/QuotationList.vue'
import QuotationPreview from '@/components/project/QuotationPreview.vue'
import QuotationRevisionHistory from '@/components/project/QuotationRevisionHistory.vue'
import StatusTransitionDialog from '@/components/project/StatusTransitionDialog.vue'
import { QUOTATION_ALLOWED_TRANSITIONS, isQuotationReasonRequired } from '@/constants/quotationContractOptions'
import { documentTemplateService } from '@/services/documentTemplateService'
import type { QuotationCreateInput } from '@/services/quotationService'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { Client } from '@/types/Client'
import type { Project, ProjectWorkspaceTabKey } from '@/types/Project'
import type { Quotation } from '@/types/Quotation'
import { triggerBlobDownload } from '@/utils/fileDownload'

const props = defineProps<{
  project: Project
  client: Client | undefined
}>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
}>()

const quotationStore = useQuotationStore()
const projectStore = useProjectStore()
const resultDialogStore = useResultDialogStore()

const isCreateDialogOpen = ref(false)
const isCreating = ref(false)
const isFinalizing = ref(false)
const isStatusDialogOpen = ref(false)
const isStatusSaving = ref(false)

// Approved is a dead end (no further transitions) -- hide the button
// entirely rather than open a dialog with nothing to pick.
const hasStatusOptions = computed(
  () => (QUOTATION_ALLOWED_TRANSITIONS[quotationStore.selectedQuotation?.status ?? ''] ?? []).length > 0,
)

function handlePrint(): void {
  window.print()
}

const isDownloadingDocument = ref(false)

async function handleDownloadDocument(): Promise<void> {
  const quotation = quotationStore.selectedQuotation
  if (!quotation) return
  isDownloadingDocument.value = true
  try {
    const blob = await documentTemplateService.downloadQuotationDocument(quotation.id)
    triggerBlobDownload(blob, `${quotation.id}.docx`)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to generate document', detail)
  } finally {
    isDownloadingDocument.value = false
  }
}

async function handleCreateQuotation(payload: QuotationCreateInput): Promise<void> {
  isCreating.value = true
  try {
    const quotation = await quotationStore.createQuotation({ ...payload, projectId: props.project.id })
    resultDialogStore.showSuccess('Quotation created', `${quotation.quotationNo} was created successfully.`)
    isCreateDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to create quotation', detail)
  } finally {
    isCreating.value = false
  }
}

async function handlePatch(patch: Partial<Quotation>): Promise<void> {
  const quotation = quotationStore.selectedQuotation
  if (!quotation) return
  try {
    await quotationStore.updateQuotation(quotation.id, patch)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to save changes', detail)
  }
}

async function handleFinalizeToggle(): Promise<void> {
  const quotation = quotationStore.selectedQuotation
  if (!quotation) return
  isFinalizing.value = true
  try {
    if (quotation.finalizedAt) {
      await quotationStore.reopenQuotation(quotation.id)
    } else {
      await quotationStore.finalizeQuotation(quotation.id)
    }
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to update quotation', detail)
  } finally {
    isFinalizing.value = false
  }
}

// Save-as-Final from inside the edit view: persist whatever was changed,
// then finalize -- sequential, not parallel, so finalize can't land
// before the content it's supposed to lock in has actually been saved.
async function handleSaveAsFinal(patch: Partial<Quotation>): Promise<void> {
  const quotation = quotationStore.selectedQuotation
  if (!quotation) return
  isFinalizing.value = true
  try {
    await quotationStore.updateQuotation(quotation.id, patch)
    await quotationStore.finalizeQuotation(quotation.id)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to finalize quotation', detail)
  } finally {
    isFinalizing.value = false
  }
}

// Draft -> Approved/Rejected/Expired, and back to Draft from either of
// the latter two. The backend refuses moving out of Draft unless the
// quotation is already saved as Final (see quotation_service.
// set_status), so this is the only path to "Approved" -- there's no
// separate approve action, moving status IS the approval.
async function handleStatusConfirm(payload: { value: string; reason?: string }): Promise<void> {
  const quotation = quotationStore.selectedQuotation
  if (!quotation) return
  isStatusSaving.value = true
  try {
    await quotationStore.setQuotationStatus(quotation.id, payload.value, payload.reason)
    // Approving a quotation is the sole thing "Quotation" -> "Contract"
    // waits on (project_service._assert_stage_exit_criteria) -- refresh
    // the shared project store so the header badge and Workflow
    // Progress stepper reflect an auto-advance immediately.
    if (payload.value === 'Approved') await projectStore.refreshProject(props.project.id)
    isStatusDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to change status', detail)
  } finally {
    isStatusSaving.value = false
  }
}

// Only an Approved, Final quotation can become a contract -- mirrors the
// backend check in contract_service.create_contract. Hands the chosen
// quotation off via the store and switches to the Contract tab, which
// picks up the pending request and opens its New Contract dialog
// prefilled from it.
function handleAdvanceToContract(): void {
  const quotation = quotationStore.selectedQuotation
  if (!quotation) return
  quotationStore.requestAdvanceToContract(quotation.id)
  emit('navigate-tab', 'contract')
}
</script>

<template>
  <div class="flex items-center justify-between">
    <BaseButton size="sm" :icon="Plus" class="no-print" @click="isCreateDialogOpen = true">New Quotation</BaseButton>
    <div class="no-print flex items-center gap-2">
      <BaseButton
        v-if="quotationStore.selectedQuotation?.status === 'Approved' && quotationStore.selectedQuotation?.finalizedAt"
        size="sm"
        :icon="ArrowRight"
        @click="handleAdvanceToContract"
      >
        Advance to Contract
      </BaseButton>
      <BaseButton
        v-if="quotationStore.selectedQuotation && hasStatusOptions"
        variant="secondary"
        size="sm"
        :icon="ArrowLeftRight"
        @click="isStatusDialogOpen = true"
      >
        Change Status
      </BaseButton>
      <BaseButton
        v-if="quotationStore.selectedQuotation?.status === 'Draft'"
        variant="secondary"
        size="sm"
        :icon="quotationStore.selectedQuotation.finalizedAt ? LockOpen : Lock"
        :loading="isFinalizing"
        @click="handleFinalizeToggle"
      >
        {{ quotationStore.selectedQuotation.finalizedAt ? 'Reopen for Editing' : 'Save as Final' }}
      </BaseButton>
      <BaseButton
        v-if="quotationStore.selectedQuotation"
        variant="secondary"
        size="sm"
        :icon="Printer"
        @click="handlePrint"
      >
        Print Quotation
      </BaseButton>
      <BaseButton
        v-if="quotationStore.selectedQuotation"
        variant="secondary"
        size="sm"
        :icon="Download"
        :loading="isDownloadingDocument"
        @click="handleDownloadDocument"
      >
        Download Document
      </BaseButton>
    </div>
  </div>

  <div class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
    <div class="laptop:col-span-2 print:col-span-3">
      <EmptyState
        v-if="!quotationStore.selectedQuotation"
        title="No quotation selected"
        description="Select a quotation from the list to preview it, or create a new one."
        action-label="New Quotation"
        @action="isCreateDialogOpen = true"
      />
      <QuotationPreview
        v-else
        :quotation="quotationStore.selectedQuotation"
        :project="project"
        :client="client"
        @patch="handlePatch"
        @save-as-final="handleSaveAsFinal"
      />
    </div>

    <div class="no-print flex flex-col gap-6">
      <QuotationList
        :quotations="quotationStore.quotations"
        :selected-quotation-id="quotationStore.selectedQuotationId"
        @select="quotationStore.selectQuotation($event)"
      />
      <QuotationRevisionHistory v-if="quotationStore.selectedQuotation" :revisions="quotationStore.selectedQuotation.revisions" />
    </div>
  </div>

  <NewQuotationDialog v-model="isCreateDialogOpen" :project="project" :loading="isCreating" @confirm="handleCreateQuotation" />
  <StatusTransitionDialog
    v-if="quotationStore.selectedQuotation"
    v-model="isStatusDialogOpen"
    title="Change Quotation Status"
    :current-value="quotationStore.selectedQuotation.status"
    :allowed-transitions="QUOTATION_ALLOWED_TRANSITIONS"
    :is-reason-required="isQuotationReasonRequired"
    :loading="isStatusSaving"
    @confirm="handleStatusConfirm"
  />
</template>

