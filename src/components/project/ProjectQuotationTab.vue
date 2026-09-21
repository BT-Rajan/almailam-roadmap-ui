<script setup lang="ts">
import { Ban, ChevronDown, Clock, Download, LockOpen, Mail, Plus, Printer, ShieldCheck, Undo2 } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SignedDocumentUploadDialog from '@/components/common/SignedDocumentUploadDialog.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import QuotationPreview from '@/components/project/QuotationPreview.vue'
import QuotationRevisionHistory from '@/components/project/QuotationRevisionHistory.vue'
import { documentTemplateService } from '@/services/documentTemplateService'
import { ROUTE_NAMES } from '@/constants/routeNames'
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
}>()

const quotationStore = useQuotationStore()
const projectStore = useProjectStore()
const companyStore = useCompanyStore()
const resultDialogStore = useResultDialogStore()
const router = useRouter()
const { t } = useI18n()

// A Draft or Approved quotation counts as active, so New Quotation
// stays disabled until it's Rejected or Expired -- matches
// isScopeLocked's own check on the Scope card in ProjectOverviewTab.vue.
const hasActiveQuotation = computed(() =>
  quotationStore.quotations.some((quotation) => quotation.status === 'Draft' || quotation.status === 'Approved'),
)

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
// One-time seed, whether settings were already loaded elsewhere before
// this component ever mounted, or load later. Deliberately NOT a single
// `watch(..., { immediate: true })` that stops itself from inside its own
// callback -- when settings are already loaded, that callback runs
// synchronously during the watch() call itself, before the `const`
// holding its own stop handle has finished initializing, throwing
// "Cannot access '...' before initialization" (confirmed crashing this
// tab whenever another page had already triggered companyStore
// .loadSettings() first). Handling the already-loaded case up front
// avoids ever creating a self-referencing immediate watcher.
if (companyStore.settings) {
  documentLanguage.value = companyStore.settings.defaultLanguage
} else {
  const stopSeedingDocumentLanguage = watch(
    () => companyStore.settings,
    (settings) => {
      if (!settings) return
      documentLanguage.value = settings.defaultLanguage
      stopSeedingDocumentLanguage()
    },
  )
}

const isFinalizing = ref(false)

// Sends straight to the dedicated New Quotation page instead of opening a dialog.
function goToCreateQuotation(): void {
  router.push({ name: ROUTE_NAMES.QUOTATION_CREATE, params: { projectId: props.project.id } })
}

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
    void quotationStore.loadAuditEvents(quotation.id)
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
    void quotationStore.loadAuditEvents(quotation.id)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('common.failedToGenerateDocument'), detail)
  } finally {
    isDownloadingDocument.value = false
  }
}

// One "Print/Download" trigger with a menu underneath, and one
// "Decision" trigger for Approve/Reject/Expire below, instead of
// several competing top-level buttons. Plain click-toggle +
// outside-click/Escape close; this toolbar isn't nested inside
// anything that clips or scrolls independently, so it doesn't need
// the teleported-to-body positioning UserMenu.vue's dropdown needs
// for the top nav.
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

const isApprovalDialogOpen = ref(false)
const isApprovalSaving = ref(false)

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
    void quotationStore.loadAuditEvents(quotation.id)
    resultDialogStore.showSuccess(t('project.quotationTab.quotationEmailedTitle'), t('common.sentTo', { email: emailTo.value.trim() }))
    isEmailDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('common.failedToSendEmail'), detail)
  } finally {
    isSendingEmail.value = false
  }
}

// A quotation is finalized (content locked) automatically as the first
// step of Approve/Reject/Expire, before the decision itself is
// recorded. No-ops (and doesn't re-finalize) if it already is.
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

async function handleApprove(): Promise<void> {
  if (!(await ensureFinalized())) return
  isApprovalDialogOpen.value = true
}

async function handleApproveFromMenu(): Promise<void> {
  closeDecisionMenu()
  await handleApprove()
}

function handleRejectFromMenu(): void {
  closeDecisionMenu()
  openRejectDialog()
}

function handleExpireFromMenu(): void {
  closeDecisionMenu()
  isExpireDialogOpen.value = true
}

async function handleConfirmApproval(payload: { file: File }): Promise<void> {
  const quotation = quotationStore.selectedQuotation
  if (!quotation) return
  isApprovalSaving.value = true
  try {
    await quotationStore.confirmQuotationApproval(quotation.id, payload.file)
    // confirmQuotationApproval can move current_stage server-side (see
    // quotation_service.set_status -> try_auto_advance_stage) -- same
    // "sync the shared store's cached copy" reasoning as
    // handleConfirmReject/handleConfirmExpire below.
    await projectStore.refreshProject(props.project.id)
    isApprovalDialogOpen.value = false
    resultDialogStore.showSuccess(t('project.quotationTab.approvalDialog.approvedTitle'), t('project.quotationTab.approvalDialog.approvedDescription'))
    // An Approved quotation is exactly what unlocks Payment Plan (see
    // hasActiveQuotation above) -- take staff straight there instead
    // of leaving them on the now-locked Quotation tab.
    emit('navigate-tab', 'payment-plan')
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('project.quotationTab.approvalDialog.failedToConfirm'), detail)
  } finally {
    isApprovalSaving.value = false
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
// Expire above) but never actually left Draft -- e.g. the approval
// dialog was opened but no file was ever confirmed, or the Reject/
// Expire call itself failed after finalizing. Without this there'd be
// no way back into editing at all, since the inline Edit button only
// shows while unfinalized.
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
    <BaseButton size="sm" :icon="Plus" :disabled="hasActiveQuotation" class="no-print" @click="goToCreateQuotation">{{ t('project.quotationTab.newQuotation') }}</BaseButton>
    <div class="no-print flex items-center gap-2">
      <div v-if="quotationStore.selectedQuotation?.status === 'Draft'" ref="decisionMenuRef" class="relative">
        <BaseButton size="sm" :icon="ShieldCheck" :loading="isApprovalSaving || isFinalizing" @click="toggleDecisionMenu">
          {{ t('project.quotationTab.decision') }}
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
            @click="handleApproveFromMenu"
          >
            <ShieldCheck class="h-4 w-4 text-success-600" />
            <span>{{ t('project.quotationTab.approve') }}</span>
          </button>
          <button
            type="button"
            role="menuitem"
            class="flex w-full items-center gap-2.5 px-3.5 py-2 text-start text-sm text-text-primary transition-colors duration-fast hover:bg-bg-hover"
            @click="handleRejectFromMenu"
          >
            <Ban class="h-4 w-4 text-danger-600" />
            <span>{{ t('project.quotationTab.reject') }}</span>
          </button>
          <button
            type="button"
            role="menuitem"
            class="flex w-full items-center gap-2.5 px-3.5 py-2 text-start text-sm text-text-primary transition-colors duration-fast hover:bg-bg-hover"
            @click="handleExpireFromMenu"
          >
            <Clock class="h-4 w-4 text-warning-600" />
            <span>{{ t('project.quotationTab.expire') }}</span>
          </button>
        </div>
      </div>
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
    <div class="flex flex-col gap-2">
      <TextInput v-model="emailTo" :label="t('project.quotationTab.recipientEmail')" type="email" required placeholder="client@example.com" />
      <p class="text-xs text-text-muted">{{ t('project.quotationTab.emailDeliveryNotice') }}</p>
    </div>
    <template #footer>
      <BaseButton variant="secondary" @click="isEmailDialogOpen = false">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="isSendingEmail" :disabled="!emailTo.trim()" @click="handleSendEmail">{{ t('project.quotationTab.send') }}</BaseButton>
    </template>
  </BaseDialog>

  <SignedDocumentUploadDialog
    v-model="isApprovalDialogOpen"
    :loading="isApprovalSaving"
    :title="t('project.quotationTab.approvalDialog.title')"
    :description="t('project.quotationTab.approvalDialog.description')"
    @confirm="handleConfirmApproval"
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

  <!-- Full-width empty state, outside the 2/3 + 1/3 grid below -- same
       structure as ProjectContractTab.vue. Inside the grid it only filled
       two of three columns and left the revision-history column as a
       large blank area beside it. -->
  <EmptyState
    v-if="!quotationStore.selectedQuotation"
    :title="t('project.quotationTab.noQuotationSelectedTitle')"
    :description="
      quotationStore.quotations.length === 0
        ? t('project.quotationTab.createFirstQuotation')
        : t('project.quotationTab.noQuotationSelectedDescription')
    "
    :action-label="quotationStore.quotations.length === 0 ? t('project.quotationTab.newQuotation') : undefined"
    @action="goToCreateQuotation"
  />

  <div v-else class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
    <div class="laptop:col-span-2 print:col-span-3">
      <QuotationPreview
        :quotation="quotationStore.selectedQuotation"
        :project="project"
        :client="client"
        @patch="handlePatch"
      />
    </div>

    <div class="no-print flex flex-col gap-6">
      <QuotationRevisionHistory
        :revisions="quotationStore.selectedQuotation.revisions"
        :events="quotationStore.selectedQuotationAuditEvents"
      />
    </div>
  </div>
</template>
