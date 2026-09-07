<script setup lang="ts">
import { ArrowLeftRight, Download, Lock, LockOpen, Mail, Plus, Printer, ShieldCheck } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import OtpVerificationDialog from '@/components/common/OtpVerificationDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import NewQuotationDialog from '@/components/project/NewQuotationDialog.vue'
import QuotationList from '@/components/project/QuotationList.vue'
import QuotationPreview from '@/components/project/QuotationPreview.vue'
import QuotationRevisionHistory from '@/components/project/QuotationRevisionHistory.vue'
import StatusTransitionDialog from '@/components/project/StatusTransitionDialog.vue'
import PaymentPlanPanel from '@/components/payment/PaymentPlanPanel.vue'
import { QUOTATION_ALLOWED_TRANSITIONS, isQuotationReasonRequired } from '@/constants/quotationContractOptions'
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
const isStatusDialogOpen = ref(false)
const isStatusSaving = ref(false)

// Approved is a dead end (no further transitions) -- hide the button
// entirely rather than open a dialog with nothing to pick.
const hasStatusOptions = computed(
  () => (QUOTATION_ALLOWED_TRANSITIONS[quotationStore.selectedQuotation?.status ?? ''] ?? []).length > 0,
)

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

const isEmailDialogOpen = ref(false)
const isSendingEmail = ref(false)
const emailTo = ref('')

const isOtpDialogOpen = ref(false)
const isOtpSaving = ref(false)
const otpStep = ref<'send' | 'enter-code'>('send')

// Draft + finalized -- content locked, ready for a decision -- and not
// already awaiting a status the OTP path doesn't apply to. Mirrors
// hasStatusOptions' own "must be finalized" gate.
const canSendOtp = computed(
  () => quotationStore.selectedQuotation?.status === 'Draft' && Boolean(quotationStore.selectedQuotation?.finalizedAt),
)

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

function handleOpenOtpDialog(): void {
  otpStep.value = quotationStore.selectedQuotation?.otpSentAt ? 'enter-code' : 'send'
  isOtpDialogOpen.value = true
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
    // "sync the shared store's cached copy" reasoning as handleStatusConfirm
    // below.
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
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('project.quotationTab.failedToUpdateQuotation'), detail)
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
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('project.quotationTab.failedToFinalizeQuotation'), detail)
  } finally {
    isFinalizing.value = false
  }
}

// Draft -> Rejected/Expired, and back to Draft from either. "Approved"
// is deliberately not offered here (see QUOTATION_ALLOWED_TRANSITIONS'
// own comment) -- the only path to it is a confirmed client email OTP,
// handled by handleConfirmOtp above.
async function handleStatusConfirm(payload: { value: string; reason?: string }): Promise<void> {
  const quotation = quotationStore.selectedQuotation
  if (!quotation) return
  isStatusSaving.value = true
  try {
    await quotationStore.setQuotationStatus(quotation.id, payload.value, payload.reason)
    isStatusDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('common.failedToChangeStatus'), detail)
  } finally {
    isStatusSaving.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-between">
    <BaseButton size="sm" :icon="Plus" class="no-print" @click="isCreateDialogOpen = true">{{ t('project.quotationTab.newQuotation') }}</BaseButton>
    <div class="no-print flex items-center gap-2">
      <BaseButton
        v-if="canSendOtp"
        size="sm"
        :icon="ShieldCheck"
        :loading="isOtpSaving"
        @click="handleOpenOtpDialog"
      >
        {{ t('project.quotationTab.sendVerificationCode') }}
      </BaseButton>
      <BaseButton
        v-if="quotationStore.selectedQuotation && hasStatusOptions"
        variant="secondary"
        size="sm"
        :icon="ArrowLeftRight"
        @click="isStatusDialogOpen = true"
      >
        {{ t('project.quotationTab.changeStatus') }}
      </BaseButton>
      <BaseButton
        v-if="quotationStore.selectedQuotation?.status === 'Draft'"
        variant="secondary"
        size="sm"
        :icon="quotationStore.selectedQuotation.finalizedAt ? LockOpen : Lock"
        :loading="isFinalizing"
        @click="handleFinalizeToggle"
      >
        {{ quotationStore.selectedQuotation.finalizedAt ? t('project.quotationTab.reopenForEditing') : t('project.quotationTab.saveAsFinal') }}
      </BaseButton>
      <SelectBox v-if="quotationStore.selectedQuotation" v-model="documentLanguage" :options="LANGUAGE_OPTIONS" class="w-28" />
      <BaseButton
        v-if="quotationStore.selectedQuotation"
        variant="secondary"
        size="sm"
        :icon="Printer"
        :loading="isPrinting"
        @click="handlePrint"
      >
        {{ t('project.quotationTab.printQuotation') }}
      </BaseButton>
      <BaseButton
        v-if="quotationStore.selectedQuotation"
        variant="secondary"
        size="sm"
        :icon="Download"
        :loading="isDownloadingDocument"
        @click="handleDownloadDocument"
      >
        {{ t('project.quotationTab.downloadDocument') }}
      </BaseButton>
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

