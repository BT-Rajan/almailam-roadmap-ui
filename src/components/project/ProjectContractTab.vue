<script setup lang="ts">
import { ArrowLeftRight, Lock, LockOpen, Plus, Printer } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import AIResponseCard from '@/components/ai/AIResponseCard.vue'
import AISuggestionCard from '@/components/ai/AISuggestionCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import ContractList from '@/components/project/ContractList.vue'
import NewContractDialog from '@/components/project/NewContractDialog.vue'
import ContractPreview from '@/components/project/ContractPreview.vue'
import ContractRevisionHistory from '@/components/project/ContractRevisionHistory.vue'
import StatusTransitionDialog from '@/components/project/StatusTransitionDialog.vue'
import { CONTRACT_ALLOWED_TRANSITIONS, isContractReasonRequired } from '@/constants/quotationContractOptions'
import { useContractStore } from '@/stores/contractStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { ContractCreateInput } from '@/services/contractService'
import type { Client } from '@/types/Client'
import type { Contract } from '@/types/Contract'
import type { Project, ProjectWorkspaceTabKey } from '@/types/Project'

const props = defineProps<{
  project: Project
  client: Client | undefined
}>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
}>()

const contractStore = useContractStore()
const quotationStore = useQuotationStore()
const projectStore = useProjectStore()
const resultDialogStore = useResultDialogStore()

const isCreateDialogOpen = ref(false)
const isCreating = ref(false)
const isFinalizing = ref(false)
const isStatusDialogOpen = ref(false)
const isStatusSaving = ref(false)

// Terminated is a dead end (no further transitions) -- hide the button
// entirely rather than open a dialog with nothing to pick.
const hasStatusOptions = computed(
  () => (CONTRACT_ALLOWED_TRANSITIONS[contractStore.selectedContract?.status ?? ''] ?? []).length > 0,
)

// A contract must come from a specific quotation that's Approved and
// Final (see contract_service.create_contract) -- this is that
// quotation, whichever the quotation tab currently has selected.
// "New Contract" stays disabled without one so staff can't even open a
// dialog that the backend would just reject.
const eligibleQuotation = () => {
  const quotation = quotationStore.selectedQuotation ?? quotationStore.latestQuotation
  return quotation && quotation.status === 'Approved' && quotation.finalizedAt ? quotation : undefined
}

function openCreateDialog(): void {
  if (!eligibleQuotation()) {
    resultDialogStore.showError(
      'No eligible quotation',
      'A contract can only be generated from a quotation that has been Approved and saved as Final. ' +
        'Finalize and approve a quotation on the Quotation tab first.',
    )
    return
  }
  isCreateDialogOpen.value = true
}

// Picked up when the user clicks "Advance to Contract" on the quotation
// tab -- selects that quotation here too (in case a different one was
// selected on this tab) and opens the dialog straight away.
onMounted(() => {
  const pendingId = quotationStore.consumePendingContractRequest()
  if (pendingId) {
    quotationStore.selectQuotation(pendingId)
    isCreateDialogOpen.value = true
  }
})

async function handleCreateContract(payload: ContractCreateInput): Promise<void> {
  const quotation = eligibleQuotation()
  if (!quotation) {
    resultDialogStore.showError(
      'No eligible quotation',
      'A contract can only be generated from a quotation that has been Approved and saved as Final.',
    )
    return
  }
  isCreating.value = true
  try {
    const contract = await contractStore.createContract({
      ...payload,
      projectId: props.project.id,
      quotationId: quotation.id,
    })
    // A contract's mere existence is one of the things "Quotation" ->
    // "Contract" waits on (project_service._assert_stage_exit_criteria)
    // -- the shared project store's cached stage is what the header
    // badge and Workflow Progress stepper read, and creating a contract
    // through contractStore never touches it on its own.
    await projectStore.refreshProject(props.project.id)
    resultDialogStore.showSuccess('Contract created', `${contract.contractNo} was created successfully.`)
    isCreateDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to create contract', detail)
  } finally {
    isCreating.value = false
  }
}

function handlePrint(): void {
  window.print()
}

async function handlePatch(patch: Partial<Contract>): Promise<void> {
  const contract = contractStore.selectedContract
  if (!contract) return
  try {
    await contractStore.updateContract(contract.id, patch)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to save changes', detail)
  }
}

async function handleFinalizeToggle(): Promise<void> {
  const contract = contractStore.selectedContract
  if (!contract) return
  isFinalizing.value = true
  try {
    if (contract.finalizedAt) {
      await contractStore.reopenContract(contract.id)
    } else {
      await contractStore.finalizeContract(contract.id)
    }
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to update contract', detail)
  } finally {
    isFinalizing.value = false
  }
}

// Save-as-Final from inside the edit view: persist whatever was changed,
// then finalize -- sequential, not parallel, so finalize can't land
// before the content it's supposed to lock in has actually been saved.
async function handleSaveAsFinal(patch: Partial<Contract>): Promise<void> {
  const contract = contractStore.selectedContract
  if (!contract) return
  isFinalizing.value = true
  try {
    await contractStore.updateContract(contract.id, patch)
    await contractStore.finalizeContract(contract.id)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to finalize contract', detail)
  } finally {
    isFinalizing.value = false
  }
}

// Draft -> Signed -> Active -> Expired/Terminated, and back to Draft
// from Expired. The backend refuses moving out of Draft unless the
// contract is already saved as Final (see contract_service.
// set_status). Marking a contract Signed is what payment configuration
// is waiting on next, so jump straight to the Payments tab rather than
// leaving staff to find it themselves.
async function handleStatusConfirm(payload: { value: string; reason?: string }): Promise<void> {
  const contract = contractStore.selectedContract
  if (!contract) return
  isStatusSaving.value = true
  try {
    await contractStore.setContractStatus(contract.id, payload.value, payload.reason)
    isStatusDialogOpen.value = false
    if (payload.value === 'Signed') {
      // Marking a contract Signed can itself be the last thing "Contract"
      // -> "Design" was waiting on (e.g. a financial agreement already
      // exists) -- refresh the shared project store so the header/
      // stepper reflect it immediately rather than only on next reload.
      await projectStore.refreshProject(props.project.id)
      emit('navigate-tab', 'payments')
    }
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to change status', detail)
  } finally {
    isStatusSaving.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-between no-print">
    <BaseButton size="sm" :icon="Plus" @click="openCreateDialog">New Contract</BaseButton>
    <div class="flex items-center gap-2">
      <BaseButton
        v-if="contractStore.selectedContract && hasStatusOptions"
        variant="secondary"
        size="sm"
        :icon="ArrowLeftRight"
        @click="isStatusDialogOpen = true"
      >
        Change Status
      </BaseButton>
      <BaseButton
        v-if="contractStore.selectedContract?.status === 'Draft'"
        variant="secondary"
        size="sm"
        :icon="contractStore.selectedContract.finalizedAt ? LockOpen : Lock"
        :loading="isFinalizing"
        @click="handleFinalizeToggle"
      >
        {{ contractStore.selectedContract.finalizedAt ? 'Reopen for Editing' : 'Save as Final' }}
      </BaseButton>
      <BaseButton
        v-if="contractStore.selectedContract"
        variant="secondary"
        size="sm"
        :icon="Printer"
        @click="handlePrint"
      >
        Print Contract
      </BaseButton>
    </div>
  </div>

  <EmptyState
    v-if="!contractStore.selectedContract"
    title="No contract selected"
    :description="contractStore.contracts.length === 0 ? 'Create the first contract for this project.' : 'Select a contract from the list to preview it.'"
    :action-label="contractStore.contracts.length === 0 ? 'New Contract' : undefined"
    @action="openCreateDialog"
  />

  <div v-else class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
    <div class="flex flex-col gap-6 laptop:col-span-2 print:col-span-3">
      <ContractPreview
        :contract="contractStore.selectedContract"
        :project="project"
        :client="client"
        @patch="handlePatch"
        @save-as-final="handleSaveAsFinal"
      />

      <div class="no-print">
        <AIResponseCard
          v-if="contractStore.aiSummary"
          title="AI Contract Summary"
          :summary="contractStore.aiSummary.summary"
          :details="contractStore.aiSummary.details"
          :confidence="contractStore.aiSummary.confidence"
        />
        <div v-else-if="contractStore.isAiSummaryLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="3" />
        </div>
      </div>

      <AISuggestionCard
        v-if="contractStore.aiSummary?.suggestions.length"
        class="no-print"
        :suggestions="contractStore.aiSummary.suggestions"
      />
    </div>

    <div class="flex flex-col gap-6 no-print">
      <ContractList
        :contracts="contractStore.contracts"
        :selected-contract-id="contractStore.selectedContractId"
        @select="contractStore.selectContract($event)"
      />
      <ContractRevisionHistory :revisions="contractStore.selectedContract.revisions" />
    </div>
  </div>

  <NewContractDialog
    v-model="isCreateDialogOpen"
    :project="project"
    :quotation="eligibleQuotation()"
    :default-client-representative="client?.contactPerson"
    :loading="isCreating"
    @confirm="handleCreateContract"
  />
  <StatusTransitionDialog
    v-if="contractStore.selectedContract"
    v-model="isStatusDialogOpen"
    title="Change Contract Status"
    :current-value="contractStore.selectedContract.status"
    :allowed-transitions="CONTRACT_ALLOWED_TRANSITIONS"
    :is-reason-required="isContractReasonRequired"
    :loading="isStatusSaving"
    @confirm="handleStatusConfirm"
  />
</template>
