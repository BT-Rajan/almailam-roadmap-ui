<script setup lang="ts">
import { ArrowLeftRight, Download, Lock, LockOpen, Mail, Plus, Printer } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import ContractList from '@/components/project/ContractList.vue'
import NewContractDialog from '@/components/project/NewContractDialog.vue'
import ContractPreview from '@/components/project/ContractPreview.vue'
import ContractRevisionHistory from '@/components/project/ContractRevisionHistory.vue'
import StatusTransitionDialog from '@/components/project/StatusTransitionDialog.vue'
import { CONTRACT_ALLOWED_TRANSITIONS, isContractReasonRequired } from '@/constants/quotationContractOptions'
import { documentTemplateService } from '@/services/documentTemplateService'
import { useCompanyStore } from '@/stores/companyStore'
import { useContractStore } from '@/stores/contractStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { ContractCreateInput } from '@/services/contractService'
import type { Client } from '@/types/Client'
import type { AppLanguage } from '@/types/CompanySettings'
import type { Contract } from '@/types/Contract'
import type { Project } from '@/types/Project'
import type { SelectOption } from '@/types/Ui'
import { openBlobInWindow, triggerBlobDownload } from '@/utils/fileDownload'

const props = defineProps<{
  project: Project
  client: Client | undefined
}>()

const contractStore = useContractStore()
const quotationStore = useQuotationStore()
const projectStore = useProjectStore()
const companyStore = useCompanyStore()
const resultDialogStore = useResultDialogStore()
const { t } = useI18n()

const LANGUAGE_OPTIONS = computed<SelectOption[]>(() => [
  { label: t('governmentFormOptions.language.english'), value: 'English' },
  { label: t('governmentFormOptions.language.arabic'), value: 'Arabic' },
])
// See ProjectQuotationTab.vue's documentLanguage for why this is seeded
// once from the company default and then left alone.
const documentLanguage = ref<AppLanguage>(companyStore.settings?.defaultLanguage ?? 'English')
onMounted(() => {
  if (companyStore.settings === undefined) companyStore.loadSettings()
})
const stopSeedingDocumentLanguage = watch(
  () => companyStore.settings,
  (settings) => {
    if (!settings) return
    documentLanguage.value = settings.defaultLanguage
    stopSeedingDocumentLanguage()
  },
  { immediate: true },
)

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

// Picked up when the user clicks "Advance to Contract" on the Payment
// Plan tab -- selects that quotation here too (in case a different one
// was selected on this tab) and opens the dialog straight away.
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

// See ProjectQuotationTab.vue's handlePrint for why the blank window has
// to open synchronously, before the async PDF fetch.
const isPrinting = ref(false)

async function handlePrint(): Promise<void> {
  const contract = contractStore.selectedContract
  if (!contract) return
  const printWindow = window.open('', '_blank')
  isPrinting.value = true
  try {
    const blob = await documentTemplateService.getContractDocumentPdf(contract.id, documentLanguage.value)
    openBlobInWindow(blob, printWindow)
  } catch (error) {
    printWindow?.close()
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to generate document', detail)
  } finally {
    isPrinting.value = false
  }
}

const isDownloadingDocument = ref(false)

async function handleDownloadDocument(): Promise<void> {
  const contract = contractStore.selectedContract
  if (!contract) return
  isDownloadingDocument.value = true
  try {
    const blob = await documentTemplateService.downloadContractDocument(contract.id, documentLanguage.value)
    triggerBlobDownload(blob, `${contract.id}.docx`)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to generate document', detail)
  } finally {
    isDownloadingDocument.value = false
  }
}

const isEmailDialogOpen = ref(false)
const isSendingEmail = ref(false)
const emailTo = ref('')

function openEmailDialog(): void {
  emailTo.value = props.client?.email ?? ''
  isEmailDialogOpen.value = true
}

async function handleSendEmail(): Promise<void> {
  const contract = contractStore.selectedContract
  if (!contract || !emailTo.value.trim()) return
  isSendingEmail.value = true
  try {
    await documentTemplateService.emailContractDocument(contract.id, emailTo.value.trim(), documentLanguage.value)
    resultDialogStore.showSuccess('Contract emailed', `Sent to ${emailTo.value.trim()}.`)
    isEmailDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to send email', detail)
  } finally {
    isSendingEmail.value = false
  }
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
// set_status).
async function handleStatusConfirm(payload: { value: string; reason?: string }): Promise<void> {
  const contract = contractStore.selectedContract
  if (!contract) return
  isStatusSaving.value = true
  try {
    await contractStore.setContractStatus(contract.id, payload.value, payload.reason)
    isStatusDialogOpen.value = false
    if (payload.value === 'Signed') {
      // Marking a contract Signed can itself be the last thing "Contract"
      // -> "Design" was waiting on (the financial agreement was already
      // created and approved back at the Payment Plan stage) -- refresh
      // the shared project store so the header/stepper reflect it
      // immediately rather than only on next reload.
      await projectStore.refreshProject(props.project.id)
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
    <BaseButton size="sm" :icon="Plus" @click="openCreateDialog">{{ t('project.contractTab.newContract') }}</BaseButton>
    <div class="flex items-center gap-2">
      <BaseButton
        v-if="contractStore.selectedContract && hasStatusOptions"
        variant="secondary"
        size="sm"
        :icon="ArrowLeftRight"
        @click="isStatusDialogOpen = true"
      >
        {{ t('project.contractTab.changeStatus') }}
      </BaseButton>
      <BaseButton
        v-if="contractStore.selectedContract?.status === 'Draft'"
        variant="secondary"
        size="sm"
        :icon="contractStore.selectedContract.finalizedAt ? LockOpen : Lock"
        :loading="isFinalizing"
        @click="handleFinalizeToggle"
      >
        {{ contractStore.selectedContract.finalizedAt ? t('project.contractTab.reopenForEditing') : t('project.contractTab.saveAsFinal') }}
      </BaseButton>
      <SelectBox v-if="contractStore.selectedContract" v-model="documentLanguage" :options="LANGUAGE_OPTIONS" class="w-28" />
      <BaseButton
        v-if="contractStore.selectedContract"
        variant="secondary"
        size="sm"
        :icon="Printer"
        :loading="isPrinting"
        @click="handlePrint"
      >
        {{ t('project.contractTab.printContract') }}
      </BaseButton>
      <BaseButton
        v-if="contractStore.selectedContract"
        variant="secondary"
        size="sm"
        :icon="Download"
        :loading="isDownloadingDocument"
        @click="handleDownloadDocument"
      >
        {{ t('project.contractTab.downloadDocument') }}
      </BaseButton>
      <BaseButton
        v-if="contractStore.selectedContract"
        variant="secondary"
        size="sm"
        :icon="Mail"
        @click="openEmailDialog"
      >
        {{ t('project.contractTab.emailContract') }}
      </BaseButton>
    </div>
  </div>

  <BaseDialog v-model="isEmailDialogOpen" title="Email Contract" size="sm">
    <TextInput v-model="emailTo" label="Recipient Email" type="email" required placeholder="client@example.com" />
    <template #footer>
      <BaseButton variant="secondary" @click="isEmailDialogOpen = false">Cancel</BaseButton>
      <BaseButton :loading="isSendingEmail" :disabled="!emailTo.trim()" @click="handleSendEmail">Send</BaseButton>
    </template>
  </BaseDialog>

  <EmptyState
    v-if="!contractStore.selectedContract"
    :title="t('project.contractTab.noContractSelectedTitle')"
    :description="contractStore.contracts.length === 0 ? t('project.contractTab.createFirstContract') : t('project.contractTab.selectFromList')"
    :action-label="contractStore.contracts.length === 0 ? t('project.contractTab.newContract') : undefined"
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
