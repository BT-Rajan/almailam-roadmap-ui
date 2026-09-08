<script setup lang="ts">
import { Ban, ChevronDown, Clock, Download, LockOpen, Mail, Plus, Printer, ShieldCheck, Undo2 } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import OtpVerificationDialog from '@/components/common/OtpVerificationDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import NewQuotationDialog from '@/components/project/NewQuotationDialog.vue'
import QuotationList from '@/components/project/QuotationList.vue'
import QuotationPreview from '@/components/project/QuotationPreview.vue'
import QuotationRevisionHistory from '@/components/project/QuotationRevisionHistory.vue'
import PaymentPlanPanel from '@/components/payment/PaymentPlanPanel.vue'
import { documentTemplateService } from '@/services/documentTemplateService'
import type { QuotationCreateInput } from '@/services/quotationService'
import { useCompanyStore } from '@/stores/companyStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { Client } from '@/types/Client'
import type { AppLanguage } from '@/types/CompanySettings'
import type { Project, ProjectWorkspaceTabKey } from '@/types/Project'
import type { Quotation } from '@/types/Quotation'
import type { SelectOption } from '@/types/Ui'
import { openBlobInWindow, triggerBlobDownload } from '@/utils/fileDownload'

const props = defineProps<{
  project: Project
  client: Client | undefined
}>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
  'add-service': []
}>()

const quotationStore = useQuotationStore()
const projectStore = useProjectStore()
const companyStore = useCompanyStore()
const resultDialogStore = useResultDialogStore()
const { t } = useI18n()

const LANGUAGE_OPTIONS = computed<SelectOption[]>(() => [
  { label: t('governmentFormOptions.language.english'), value: 'English' },
  { label: t('governmentFormOptions.language.arabic'), value: 'Arabic' },
])
// Which of the two per-type default templates (English/Arabic) Print/
// Download/Email use -- seeded from the company-wide default language
// once it loads, but overridable per document afterward without
// changing that company setting.
const documentLanguage = ref<AppLanguage>(companyStore.settings?.defaultLanguage ?? 'English')
onMounted(() => {
  if (companyStore.settings === undefined) companyStore.loadSettings()
})
const stopSeedingDocumentLanguage = watch(
  () => companyStore.settings,
  (settings) => {
    // Only a one-time seed, whether settings were already loaded (fires
    // immediately) or load later (fires on that change) -- once applied,
    // this stops so it never overwrites a language the user picked here.
    if (!settings) return
    documentLanguage.value = settings.defaultLanguage
    stopSeedingDocumentLanguage()
  },
  { immediate: true },
)

const isCreateDialogOpen = ref(false)
const isCreating = ref(false)
const isFinalizing = ref(false)

// Opens the same admin-uploaded/field-mapped template Download Document
// merges, as a PDF, in a new tab -- so Print reflects that template
// instead of the separate hardcoded on-screen preview below. The blank
// window has to open synchronously, before the async PDF fetch, or most
// browsers treat it as an unrequested pop-up and block it (see
// openBlobInWindow's docstring).
const isPrinting = ref(false)

async function handlePrint(): Promise<void> {
  const quotation = quotationStore.selectedQuotation
  if (!quotation) return
  const printWindow = window.open('', '_blank')
  isPrinting.value = true
  try {
    const blob = await documentTemplateService.getQuotationDocumentPdf(quotation.id, documentLanguage.value)
    openBlobInWindow(blob, printWindow)
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
  const quotation = quotationStore.selectedQuotation
  if (!quotation) return
  isDownloadingDocument.value = true
  try {
    const blob = await documentTemplateService.downloadQuotationDocument(quotation.id, documentLanguage.value)
    triggerBlobDownload(blob, `${quotation.id}.docx`)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('common.failedToGenerateDocument'), detail)
  } finally {
    isDownloadingDocument.value = false
  }
}

// Print and Download used to be two separate buttons -- merged into one
// trigger with a small menu underneath so the toolbar reads as "produce
// a document, pick the format" instead of two competing top-level
// actions. Plain click-toggle + outside-click/Escape close; this
// toolbar isn't nested inside anything that clips or scrolls
// independently, so it doesn't need the teleported-to-body positioning
// UserMenu.vue's own dropdown needs for the top nav.
const isDocumentMenuOpen = ref(false)
const documentMenuRef = ref<HTMLElement>()

function toggleDocumentMenu(): void {
  isDocumentMenuOpen.value = !isDocumentMenuOpen.value
}

function closeDocumentMenu(): void {
  isDocumentMenuOpen.value = false
}

function handleClickOutsideDocumentMenu(event: MouseEvent): void {
  if (isDocumentMenuOpen.value && !documentMenuRef.value?.contains(event.target as Node)) closeDocumentMenu()
}

function handleKeydownDocumentMenu(event: KeyboardEvent): void {
  if (event.key === 'Escape' && isDocumentMenuOpen.value) closeDocumentMenu()
}

window.addEventListener('mousedown', handleClickOutsideDocumentMenu)
window.addEventListener('keydown', handleKeydownDocumentMenu)
onBeforeUnmount(() => {
  window.removeEventListener('mousedown', handleClickOutsideDocumentMenu)
  window.removeEventListener('keydown', handleKeydownDocumentMenu)
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

const isOtpDialogOpen = ref(false)
const isOtpSaving = ref(false)
const otpStep = ref<'send' | 'enter-code'>('send')

function openEmailDialog(): void {
  emailTo.value = props.client?.email ?? ''
  isEmailDialogOpen.value = true
}

async function handleSendEmail(): Promise<void> {
  const quotation = quotationStore.selectedQuotation
  if (!quotation || !emailTo.value.trim()) return
  isSendingEmail.value = true
  try {
    await documentTemplateService.emailQuotationDocument(quotation.id, emailTo.value.trim(), documentLanguage.value)
    resultDialogStore.showSuccess(t('project.quotationTab.quotationEmailedTitle'), t('common.sentTo', { email: emailTo.value.trim() }))
    isEmailDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('common.failedToSendEmail'), detail)
  } finally {
    isSendingEmail.value = false
  }
}

// A quotation has to be finalized (content locked) before it can be
// sent for a decision -- previously a separate "Save as Final" button
// the user finalized before deciding, this now happens transparently
// as the first step of Approve/Reject/Expire instead, since there's no
// longer a standalone finalize action in the UI. No-ops (and doesn't
// re-finalize) if it already is.
async function ensureFinalized(): Promise<boolean> {
  const quotation = quotationStore.selectedQuotation
  if (!quotation) return false
  if (quotation.finalizedAt) return true
  try {
    await quotationStore.finalizeQuotation(quotation.id)
    return true
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('project.quotationTab.failedToFinalizeQuotation'), detail)
    return false
  }
}

function openOtpDialog(): void {
  otpStep.value = quotationStore.selectedQuotation?.otpSentAt ? 'enter-code' : 'send'
  isOtpDialogOpen.value = true
}

async function handleApprove(): Promise<void> {
  if (!(await ensureFinalized())) return
  openOtpDialog()
}

async function handleSendOtp(): Promise<void> {
  const quotation = quotationStore.selectedQuotation
  if (!quotation) return
  isOtpSaving.value = true
  try {
    await quotationStore.sendQuotationOtp(quotation.id)
    otpStep.value = 'enter-code'
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('project.quotationTab.otpDialog.failedToSend'), detail)
  } finally {
    isOtpSaving.value = false
  }
}

async function handleConfirmOtp(payload: { code: string }): Promise<void> {
  const quotation = quotationStore.selectedQuotation
  if (!quotation) return
  isOtpSaving.value = true
  try {
    await quotationStore.verifyQuotationOtp(quotation.id, payload.code)
    // verifyQuotationOtp can move current_stage server-side (see
    // quotation_service.set_status -> try_auto_advance_stage) -- same
    // "sync the shared store's cached copy" reasoning as
    // handleConfirmReject/handleConfirmExpire below.
    await projectStore.refreshProject(props.project.id)
    isOtpDialogOpen.value = false
    resultDialogStore.showSuccess(t('project.quotationTab.otpDialog.approvedTitle'), t('project.quotationTab.otpDialog.approvedDescription'))
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('project.quotationTab.otpDialog.failedToVerify'), detail)
  } finally {
    isOtpSaving.value = false
  }
}

async function handleCreateQuotation(payload: QuotationCreateInput): Promise<void> {
  isCreating.value = true
  try {
    const quotation = await quotationStore.createQuotation({ ...payload, projectId: props.project.id })
    resultDialogStore.showSuccess(t('project.quotationTab.quotationCreatedTitle'), t('common.createdSuccessfully', { no: quotation.quotationNo }))
    isCreateDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('project.quotationTab.failedToCreateQuotation'), detail)
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
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('common.failedToSaveChanges'), detail)
  }
}

// Escape hatch for a quotation that got finalized (by Approve/Reject/
// Expire above) but never actually left Draft -- e.g. the OTP was sent
// but never confirmed, or the Reject/Expire call itself failed after
// finalizing. Without this there'd be no way back into editing at all,
// since the inline Edit button only shows while unfinalized.
async function handleReopenForEditing(): Promise<void> {
  const quotation = quotationStore.selectedQuotation
  if (!quotation) return
  isFinalizing.value = true
  try {
    await quotationStore.reopenQuotation(quotation.id)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('project.quotationTab.failedToUpdateQuotation'), detail)
  } finally {
    isFinalizing.value = false
  }
}

const isRejectDialogOpen = ref(false)
const isRejecting = ref(false)
const rejectReason = ref('')

function openRejectDialog(): void {
  rejectReason.value = ''
  isRejectDialogOpen.value = true
}

async function handleConfirmReject(): Promise<void> {
  const quotation = quotationStore.selectedQuotation
  if (!quotation || !rejectReason.value.trim()) return
  isRejecting.value = true
  try {
    if (!(await ensureFinalized())) return
    await quotationStore.setQuotationStatus(quotation.id, 'Rejected', rejectReason.value.trim())
    isRejectDialogOpen.value = false
    resultDialogStore.showSuccess(
      t('project.quotationTab.rejectDialog.rejectedTitle'),
      t('project.quotationTab.rejectDialog.rejectedDescription', { no: quotation.quotationNo }),
    )
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('project.quotationTab.rejectDialog.failedToReject'), detail)
  } finally {
    isRejecting.value = false
  }
}

const isExpireDialogOpen = ref(false)
const isExpiring = ref(false)

async function handleConfirmExpire(): Promise<void> {
  const quotation = quotationStore.selectedQuotation
  if (!quotation) return
  isExpiring.value = true
  try {
    if (!(await ensureFinalized())) return
    await quotationStore.setQuotationStatus(quotation.id, 'Expired')
    isExpireDialogOpen.value = false
    resultDialogStore.showSuccess(
      t('project.quotationTab.expireDialog.expiredTitle'),
      t('project.quotationTab.expireDialog.expiredDescription', { no: quotation.quotationNo }),
    )
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('project.quotationTab.expireDialog.failedToExpire'), detail)
  } finally {
    isExpiring.value = false
  }
}

// Rejected/Expired -> Draft -- reopens the content for editing
// automatically (see quotation_service.set_status), so this is the one
// transition that needs neither a reason nor a finalize step first.
const isRevertingToDraft = ref(false)

async function handleRevertToDraft(): Promise<void> {
  const quotation = quotationStore.selectedQuotation
  if (!quotation) return
  isRevertingToDraft.value = true
  try {
    await quotationStore.setQuotationStatus(quotation.id, 'Draft')
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('project.quotationTab.failedToRevertToDraft'), detail)
  } finally {
    isRevertingToDraft.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-between">
    <BaseButton size="sm" :icon="Plus" class="no-print" @click="isCreateDialogOpen = true">{{ t('project.quotationTab.newQuotation') }}</BaseButton>
    <div class="no-print flex items-center gap-2">
      <template v-if="quotationStore.selectedQuotation?.status === 'Draft'">
        <BaseButton size="sm" :icon="ShieldCheck" :loading="isOtpSaving || isFinalizing" @click="handleApprove">
          {{ t('project.quotationTab.approve') }}
        </BaseButton>
        <BaseButton variant="secondary" size="sm" :icon="Ban" @click="openRejectDialog">
          {{ t('project.quotationTab.reject') }}
        </BaseButton>
        <BaseButton variant="secondary" size="sm" :icon="Clock" @click="isExpireDialogOpen = true">
          {{ t('project.quotationTab.expire') }}
        </BaseButton>
      </template>
      <BaseButton
        v-if="quotationStore.selectedQuotation?.status === 'Rejected' || quotationStore.selectedQuotation?.status === 'Expired'"
        variant="secondary"
        size="sm"
        :icon="Undo2"
        :loading="isRevertingToDraft"
        @click="handleRevertToDraft"
      >
        {{ t('project.quotationTab.moveToDraft') }}
      </BaseButton>
      <BaseButton
        v-if="quotationStore.selectedQuotation?.status === 'Draft' && quotationStore.selectedQuotation.finalizedAt"
        variant="secondary"
        size="sm"
        :icon="LockOpen"
        :loading="isFinalizing"
        @click="handleReopenForEditing"
      >
        {{ t('project.quotationTab.reopenForEditing') }}
      </BaseButton>
      <SelectBox v-if="quotationStore.selectedQuotation" v-model="documentLanguage" :options="LANGUAGE_OPTIONS" class="w-28" />
      <div v-if="quotationStore.selectedQuotation" ref="documentMenuRef" class="relative">
        <BaseButton variant="secondary" size="sm" :icon="Printer" :loading="isPrinting || isDownloadingDocument" @click="toggleDocumentMenu">
          {{ t('project.quotationTab.printOrDownload') }}
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
            <span>{{ t('project.quotationTab.printQuotation') }}</span>
          </button>
          <button
            type="button"
            role="menuitem"
            class="flex w-full items-center gap-2.5 px-3.5 py-2 text-start text-sm text-text-primary transition-colors duration-fast hover:bg-bg-hover"
            @click="handleDownloadFromMenu"
          >
            <Download class="h-4 w-4 text-text-muted" />
            <span>{{ t('project.quotationTab.downloadDocument') }}</span>
          </button>
        </div>
      </div>
      <BaseButton
        v-if="quotationStore.selectedQuotation"
        variant="secondary"
        size="sm"
        :icon="Mail"
        @click="openEmailDialog"
      >
        {{ t('project.quotationTab.emailQuotation') }}
      </BaseButton>
    </div>
  </div>

  <BaseDialog v-model="isEmailDialogOpen" :title="t('project.quotationTab.emailQuotation')" size="sm">
    <TextInput v-model="emailTo" :label="t('project.quotationTab.recipientEmail')" type="email" required placeholder="client@example.com" />
    <template #footer>
      <BaseButton variant="secondary" @click="isEmailDialogOpen = false">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="isSendingEmail" :disabled="!emailTo.trim()" @click="handleSendEmail">{{ t('project.quotationTab.send') }}</BaseButton>
    </template>
  </BaseDialog>

  <OtpVerificationDialog
    v-if="client"
    v-model="isOtpDialogOpen"
    :email="client.email"
    :step="otpStep"
    :loading="isOtpSaving"
    :title="t('project.quotationTab.otpDialog.title')"
    :send-step-description="t('project.quotationTab.otpDialog.sendStepDescription', { email: client.email })"
    @send="handleSendOtp"
    @confirm="handleConfirmOtp"
  />

  <BaseDialog v-if="quotationStore.selectedQuotation" v-model="isRejectDialogOpen" :title="t('project.quotationTab.rejectDialog.title')" size="sm">
    <div class="flex flex-col gap-4">
      <p class="text-sm text-text-secondary">{{ t('project.quotationTab.rejectDialog.message', { no: quotationStore.selectedQuotation.quotationNo }) }}</p>
      <TextArea
        v-model="rejectReason"
        :label="t('project.quotationTab.rejectDialog.reasonLabel')"
        :placeholder="t('project.quotationTab.rejectDialog.reasonPlaceholder')"
        required
        :rows="3"
      />
    </div>
    <template #footer>
      <BaseButton variant="secondary" :disabled="isRejecting" @click="isRejectDialogOpen = false">{{ t('common.cancel') }}</BaseButton>
      <BaseButton variant="danger" :loading="isRejecting" :disabled="!rejectReason.trim()" @click="handleConfirmReject">
        {{ t('project.quotationTab.rejectDialog.confirmLabel') }}
      </BaseButton>
    </template>
  </BaseDialog>

  <ConfirmationDialog
    v-if="quotationStore.selectedQuotation"
    v-model="isExpireDialogOpen"
    :title="t('project.quotationTab.expireDialog.title')"
    :message="t('project.quotationTab.expireDialog.message', { no: quotationStore.selectedQuotation.quotationNo })"
    :confirm-label="t('project.quotationTab.expireDialog.confirmLabel')"
    confirm-variant="danger"
    :loading="isExpiring"
    @confirm="handleConfirmExpire"
  />

  <div class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
    <div class="laptop:col-span-2 print:col-span-3">
      <EmptyState
        v-if="!quotationStore.selectedQuotation"
        :title="t('project.quotationTab.noQuotationSelectedTitle')"
        :description="t('project.quotationTab.noQuotationSelectedDescription')"
        :action-label="t('project.quotationTab.newQuotation')"
        @action="isCreateDialogOpen = true"
      />
      <QuotationPreview
        v-else
        :quotation="quotationStore.selectedQuotation"
        :project="project"
        :client="client"
        @patch="handlePatch"
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

  <div class="no-print">
    <h3 class="mb-4 text-sm font-semibold text-text-primary">{{ t('project.quotationTab.paymentPlanTitle') }}</h3>
    <PaymentPlanPanel
      :project-id="project.id"
      :project="project"
      @navigate-tab="emit('navigate-tab', $event)"
      @add-service="emit('add-service')"
    />
  </div>
</template>

