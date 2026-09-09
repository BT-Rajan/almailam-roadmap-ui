<script setup lang="ts">
import { ChevronDown, Download, LockOpen, Mail, Plus, Printer, ShieldCheck, Undo2 } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SignedDocumentUploadDialog from '@/components/common/SignedDocumentUploadDialog.vue'
import TextInput from '@/components/common/TextInput.vue'
import NewContractDialog from '@/components/project/NewContractDialog.vue'
import ContractPreview from '@/components/project/ContractPreview.vue'
import ContractRevisionHistory from '@/components/project/ContractRevisionHistory.vue'
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

// Keeps the "download / email / signed time" activity in the Revision
// History panel current -- reloaded whenever a different contract is
// selected, and again after any action below that adds a new audit
// event (print, download, email, sign). Mirrors
// ProjectQuotationTab.vue's own copy of this exactly.
watch(
  () => contractStore.selectedContractId,
  (contractId) => {
    if (contractId) contractStore.loadAuditEvents(contractId)
  },
  { immediate: true },
)

// Same toolbar shape as ProjectQuotationTab.vue: one "Decision" dropdown
// with a single item ("Sign", where Quotation has "Approve"), shown
// only while the contract is still Draft -- exactly Quotation's own
// v-if condition, not a status-dependent set of items. Once signed,
// this dropdown is gone for good, same as Quotation's Decision dropdown
// never comes back once a quotation is Approved.
const hasDecisionOptions = computed(() => contractStore.selectedContract?.status === 'Draft')

// Once any contract for this project has ever been signed, its terms
// are locked in -- "New Contract" is disabled the same way Quotation's
// "New Quotation" is disabled once one's Approved (see
// ProjectQuotationTab.vue's hasApprovedQuotation).
const hasSignedContract = computed(() => contractStore.contracts.some((contract) => contract.status !== 'Draft'))

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
      t('project.contractTab.noEligibleQuotationTitle'),
      t('project.contractTab.noEligibleQuotationDescriptionLong'),
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
      t('project.contractTab.noEligibleQuotationTitle'),
      t('project.contractTab.noEligibleQuotationDescriptionShort'),
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
    resultDialogStore.showSuccess(t('project.contractTab.contractCreatedTitle'), t('common.createdSuccessfully', { no: contract.contractNo }))
    isCreateDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('project.contractTab.failedToCreateContract'), detail)
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
    contractStore.loadAuditEvents(contract.id)
  } catch (error) {
    printWindow?.close()
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('common.failedToGenerateDocument'), detail)
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
    contractStore.loadAuditEvents(contract.id)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('common.failedToGenerateDocument'), detail)
  } finally {
    isDownloadingDocument.value = false
  }
}

// Same merged-trigger toolbar pattern as ProjectQuotationTab.vue: one
// "Print/Download" dropdown instead of two competing top-level buttons,
// and one "Decision" dropdown instead of one button per possible status
// action. Plain click-toggle + outside-click/Escape close -- see
// ProjectQuotationTab.vue's own copy of this for why it doesn't need
// UserMenu.vue's teleported-to-body positioning.
const isDocumentMenuOpen = ref(false)
const documentMenuRef = ref<HTMLElement>()
const isDecisionMenuOpen = ref(false)
const decisionMenuRef = ref<HTMLElement>()

function toggleDocumentMenu(): void {
  isDocumentMenuOpen.value = !isDocumentMenuOpen.value
}

function closeDocumentMenu(): void {
  isDocumentMenuOpen.value = false
}

function toggleDecisionMenu(): void {
  isDecisionMenuOpen.value = !isDecisionMenuOpen.value
}

function closeDecisionMenu(): void {
  isDecisionMenuOpen.value = false
}

function handleClickOutsideMenus(event: MouseEvent): void {
  const target = event.target as Node
  if (isDocumentMenuOpen.value && !documentMenuRef.value?.contains(target)) closeDocumentMenu()
  if (isDecisionMenuOpen.value && !decisionMenuRef.value?.contains(target)) closeDecisionMenu()
}

function handleKeydownMenus(event: KeyboardEvent): void {
  if (event.key !== 'Escape') return
  if (isDocumentMenuOpen.value) closeDocumentMenu()
  if (isDecisionMenuOpen.value) closeDecisionMenu()
}

window.addEventListener('mousedown', handleClickOutsideMenus)
window.addEventListener('keydown', handleKeydownMenus)
onBeforeUnmount(() => {
  window.removeEventListener('mousedown', handleClickOutsideMenus)
  window.removeEventListener('keydown', handleKeydownMenus)
})

async function handlePrintFromMenu(): Promise<void> {
  closeDocumentMenu()
  await handlePrint()
}

async function handleDownloadFromMenu(): Promise<void> {
  closeDocumentMenu()
  await handleDownloadDocument()
}

const isEmailDialogOpen = ref(false)
const isSendingEmail = ref(false)
const emailTo = ref('')

const isSigningDialogOpen = ref(false)
const isSigningSaving = ref(false)

// A contract has to be finalized (content locked) before it can be
// signed -- mirrors ProjectQuotationTab.vue's ensureFinalized, which
// this replaces the manual "Save as Final" toolbar toggle with. No-op
// (and doesn't re-finalize) if it already is.
async function ensureFinalized(): Promise<boolean> {
  const contract = contractStore.selectedContract
  if (!contract) return false
  if (contract.finalizedAt) return true
  try {
    await contractStore.finalizeContract(contract.id)
    return true
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('project.contractTab.failedToFinalizeContract'), detail)
    return false
  }
}

async function handleSignFromMenu(): Promise<void> {
  closeDecisionMenu()
  if (!(await ensureFinalized())) return
  isSigningDialogOpen.value = true
}

async function handleConfirmSigning(payload: { file: File }): Promise<void> {
  const contract = contractStore.selectedContract
  if (!contract) return
  isSigningSaving.value = true
  try {
    const signed = await contractStore.confirmContractSigning(contract.id, payload.file)
    await contractStore.loadAuditEvents(contract.id)
    // confirmContractSigning can move current_stage server-side (see
    // contract_service.set_status -> try_auto_advance_stage) -- same
    // "sync the shared store's cached copy" reasoning as
    // handleCreateContract above.
    await projectStore.refreshProject(props.project.id)
    isSigningDialogOpen.value = false
    const description = signed.confirmationEmailSent === false
      ? t('project.contractTab.signingDialog.signedDescriptionEmailFailed')
      : t('project.contractTab.signingDialog.signedDescription')
    resultDialogStore.showSuccess(t('project.contractTab.signingDialog.signedTitle'), description)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('project.contractTab.signingDialog.failedToConfirm'), detail)
  } finally {
    isSigningSaving.value = false
  }
}

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
    resultDialogStore.showSuccess(t('project.contractTab.contractEmailedTitle'), t('common.sentTo', { email: emailTo.value.trim() }))
    isEmailDialogOpen.value = false
    contractStore.loadAuditEvents(contract.id)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('common.failedToSendEmail'), detail)
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
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('common.failedToSaveChanges'), detail)
  }
}

// Escape hatch for a contract that got finalized (by a Decision action
// above) but never actually left Draft -- e.g. the signing dialog was
// opened but no file was ever confirmed. Mirrors
// ProjectQuotationTab.vue's handleReopenForEditing exactly.
async function handleReopenForEditing(): Promise<void> {
  const contract = contractStore.selectedContract
  if (!contract) return
  isFinalizing.value = true
  try {
    await contractStore.reopenContract(contract.id)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('project.contractTab.failedToUpdateContract'), detail)
  } finally {
    isFinalizing.value = false
  }
}

// Expired -> Draft -- reopens the content for editing automatically
// (see contract_service.set_status), so this is the one transition
// that needs neither a reason nor a finalize step first. Mirrors
// ProjectQuotationTab.vue's handleRevertToDraft exactly.
const isRevertingToDraft = ref(false)

async function handleRevertToDraft(): Promise<void> {
  const contract = contractStore.selectedContract
  if (!contract) return
  isRevertingToDraft.value = true
  try {
    await contractStore.setContractStatus(contract.id, 'Draft')
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('project.contractTab.failedToRevertToDraft'), detail)
  } finally {
    isRevertingToDraft.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-between">
    <BaseButton size="sm" :icon="Plus" :disabled="hasSignedContract" class="no-print" @click="openCreateDialog">{{ t('project.contractTab.newContract') }}</BaseButton>
    <div class="no-print flex items-center gap-2">
      <div v-if="hasDecisionOptions" ref="decisionMenuRef" class="relative">
        <BaseButton size="sm" :icon="ShieldCheck" :loading="isSigningSaving || isFinalizing" @click="toggleDecisionMenu">
          {{ t('project.contractTab.decision') }}
          <ChevronDown class="ms-1 h-3.5 w-3.5" />
        </BaseButton>
        <div
          v-if="isDecisionMenuOpen"
          role="menu"
          class="absolute start-0 z-dropdown mt-1 w-52 rounded-lg border border-border-light bg-bg-card py-1.5 shadow-elevated"
        >
          <button
            type="button"
            role="menuitem"
            class="flex w-full items-center gap-2.5 px-3.5 py-2 text-start text-sm text-text-primary transition-colors duration-fast hover:bg-bg-hover"
            @click="handleSignFromMenu"
          >
            <ShieldCheck class="h-4 w-4 text-success-600" />
            <span>{{ t('project.contractTab.signContract') }}</span>
          </button>
        </div>
      </div>
      <BaseButton
        v-if="contractStore.selectedContract?.status === 'Expired'"
        variant="secondary"
        size="sm"
        :icon="Undo2"
        :loading="isRevertingToDraft"
        @click="handleRevertToDraft"
      >
        {{ t('project.contractTab.moveToDraft') }}
      </BaseButton>
      <BaseButton
        v-if="contractStore.selectedContract?.status === 'Draft' && contractStore.selectedContract.finalizedAt"
        variant="secondary"
        size="sm"
        :icon="LockOpen"
        :loading="isFinalizing"
        @click="handleReopenForEditing"
      >
        {{ t('project.contractTab.reopenForEditing') }}
      </BaseButton>
      <SelectBox v-if="contractStore.selectedContract" v-model="documentLanguage" :options="LANGUAGE_OPTIONS" class="w-28" />
      <div v-if="contractStore.selectedContract" ref="documentMenuRef" class="relative">
        <BaseButton variant="secondary" size="sm" :icon="Printer" :loading="isPrinting || isDownloadingDocument" @click="toggleDocumentMenu">
          {{ t('project.contractTab.printOrDownload') }}
          <ChevronDown class="ms-1 h-3.5 w-3.5" />
        </BaseButton>
        <div
          v-if="isDocumentMenuOpen"
          role="menu"
          class="absolute end-0 z-dropdown mt-1 w-52 rounded-lg border border-border-light bg-bg-card py-1.5 shadow-elevated"
        >
          <button
            type="button"
            role="menuitem"
            class="flex w-full items-center gap-2.5 px-3.5 py-2 text-start text-sm text-text-primary transition-colors duration-fast hover:bg-bg-hover"
            @click="handlePrintFromMenu"
          >
            <Printer class="h-4 w-4 text-text-muted" />
            <span>{{ t('project.contractTab.printContract') }}</span>
          </button>
          <button
            type="button"
            role="menuitem"
            class="flex w-full items-center gap-2.5 px-3.5 py-2 text-start text-sm text-text-primary transition-colors duration-fast hover:bg-bg-hover"
            @click="handleDownloadFromMenu"
          >
            <Download class="h-4 w-4 text-text-muted" />
            <span>{{ t('project.contractTab.downloadDocument') }}</span>
          </button>
        </div>
      </div>
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

  <BaseDialog v-model="isEmailDialogOpen" :title="t('project.contractTab.emailContract')" size="sm">
    <TextInput v-model="emailTo" :label="t('project.contractTab.recipientEmail')" type="email" required placeholder="client@example.com" />
    <template #footer>
      <BaseButton variant="secondary" @click="isEmailDialogOpen = false">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="isSendingEmail" :disabled="!emailTo.trim()" @click="handleSendEmail">{{ t('project.contractTab.send') }}</BaseButton>
    </template>
  </BaseDialog>

  <SignedDocumentUploadDialog
    v-model="isSigningDialogOpen"
    :loading="isSigningSaving"
    :title="t('project.contractTab.signingDialog.title')"
    :description="t('project.contractTab.signingDialog.description')"
    @confirm="handleConfirmSigning"
  />

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
      />
    </div>

    <div class="flex flex-col gap-6 no-print">
      <ContractRevisionHistory
        :revisions="contractStore.selectedContract.revisions"
        :audit-events="contractStore.auditEventsByContract[contractStore.selectedContract.id] ?? []"
      />
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
</template>
