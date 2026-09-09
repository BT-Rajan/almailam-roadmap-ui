<script setup lang="ts">
import { ArrowLeft, ArrowRight, ChevronDown, Download, Mail, Pencil, Plus, Printer, ShieldCheck, Trash2, Wallet } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AgreementFormDialog from '@/components/payment/AgreementFormDialog.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import Card from '@/components/common/Card.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PaymentHistoryPanel from '@/components/payment/PaymentHistoryPanel.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useLocale } from '@/composables/useLocale'
import { usePaymentAgreements } from '@/composables/usePaymentAgreements'
import { documentTemplateService } from '@/services/documentTemplateService'
import { useCompanyStore } from '@/stores/companyStore'
import { usePaymentStore } from '@/stores/paymentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { getAgreementStreamLabel } from '@/utils/paymentHelpers'
import { getWorkflowStageLabelKey, getWorkflowStageTabKey, hasProjectPassedStage } from '@/utils/projectHelpers'
import { openBlobInWindow, triggerBlobDownload } from '@/utils/fileDownload'
import type { AgreementStream, CreateAgreementInput, FinancialAgreement } from '@/types/Payment'
import type { Client } from '@/types/Client'
import type { AppLanguage } from '@/types/CompanySettings'
import type { Project, ProjectWorkspaceTabKey } from '@/types/Project'
import type { SelectOption } from '@/types/Ui'
import type { SmartTableColumn } from '@/types/Table'

interface Props {
  projectId: string
  project: Project
  client: Client | undefined
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
  'add-service': []
}>()

const { visibleStreams, agreementForStream, obligationsForStream } = usePaymentAgreements(
  () => props.projectId,
  () => props.project,
)

const store = usePaymentStore()
const projectStore = useProjectStore()
const quotationStore = useQuotationStore()
const companyStore = useCompanyStore()
// Matches every other create/edit/delete-style action in the app
// (Clients, Projects, Quotations, Contracts, Government Submissions) --
// an explicit acknowledgment dialog for actions that change money on
// record, not a toast that could be missed.
const resultDialogStore = useResultDialogStore()
const { t } = useI18n()
const { isRtl } = useLocale()

// Points the way this action advances the project, which flips with
// reading direction.
const advanceIcon = computed(() => (isRtl.value ? ArrowLeft : ArrowRight))

const AGREEMENT_STATUS_LABEL_KEYS: Record<string, string> = {
  Draft: 'payment.agreementStatus.draft',
  Approved: 'payment.agreementStatus.approved',
}
function agreementStatusLabel(status: string): string {
  return t(AGREEMENT_STATUS_LABEL_KEYS[status] ?? status)
}

const PAYMENT_MODE_LABEL_KEYS: Record<string, string> = {
  Cash: 'payment.paymentMode.cash',
  'Bank Transfer': 'payment.paymentMode.bankTransfer',
  'Credit Card': 'payment.paymentMode.creditCard',
  'Debit Card': 'payment.paymentMode.debitCard',
  'Online Payment': 'payment.paymentMode.onlinePayment',
  Cheque: 'payment.paymentMode.cheque',
  Other: 'payment.paymentMode.other',
}
function paymentModeLabel(mode: string): string {
  return t(PAYMENT_MODE_LABEL_KEYS[mode] ?? mode)
}

const AGREEMENT_STREAM_LABEL_KEYS: Record<string, string> = {
  Design: 'payment.agreementStream.design',
  Supervision: 'payment.agreementStream.supervision',
}
function agreementStreamLabel(stream: string): string {
  return t(AGREEMENT_STREAM_LABEL_KEYS[stream] ?? getAgreementStreamLabel(stream as AgreementStream))
}

// Section headings -- distinct from agreementStreamLabel above, which
// names just the billing stream ("Design"). These name what the
// section itself covers ("Design and Permit Plan"), since Design also
// bundles licensing/permit fees into its one agreement (see
// explainerDesign below).
const SECTION_LABEL_KEYS: Record<AgreementStream, string> = {
  Design: 'payment.planPanel.designAndPermitSection',
  Supervision: 'payment.planPanel.supervisionSection',
}
function sectionLabel(stream: AgreementStream): string {
  return t(SECTION_LABEL_KEYS[stream])
}

// One page, one set of controls -- no more per-stream sub-tabs. Every
// visible stream's plan (and the read-only Permits summary below) is
// shown as its own stacked section instead, same "everything on one
// screen" shape as ProjectQuotationTab.vue/ProjectContractTab.vue.
type PlanSection = { kind: 'stream'; stream: AgreementStream } | { kind: 'permits' }

const selectedPermits = computed(() => props.project.selectedPermits ?? [])
const hasPermits = computed(() => selectedPermits.value.length > 0)
const permitsTotal = computed(() => selectedPermits.value.reduce((sum, permit) => sum + (permit.permitPrice ?? 0), 0))

// Design, Permits, Supervision -- in that order, and only the ones
// this project's scope actually includes.
const sections = computed<PlanSection[]>(() => {
  const list: PlanSection[] = []
  if (visibleStreams.value.includes('Design')) list.push({ kind: 'stream', stream: 'Design' })
  if (hasPermits.value) list.push({ kind: 'permits' })
  if (visibleStreams.value.includes('Supervision')) list.push({ kind: 'stream', stream: 'Supervision' })
  return list
})

const hasAnyScope = computed(() => visibleStreams.value.length > 0 || hasPermits.value)

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

const hasAnyAgreement = computed(() => visibleStreams.value.some((stream) => agreementForStream(stream)))

// Same "New X" toolbar button as ProjectQuotationTab.vue/
// ProjectContractTab.vue -- whichever visible stream doesn't have an
// agreement yet is next up; once every stream has one, there's nothing
// left to create and the button disappears. A project needing both
// Design and Supervision plans just gets this pointed at Supervision
// once Design's is created.
const nextMissingStream = computed(() => visibleStreams.value.find((stream) => !agreementForStream(stream)))

const isAgreementFormOpen = ref(false)
const agreementFormMode = ref<'create' | 'edit'>('create')
const agreementFormStream = ref<AgreementStream>('Design')
const agreementBeingEdited = ref<FinancialAgreement | undefined>(undefined)
const isApprovingStream = ref<AgreementStream | undefined>(undefined)
const isDeleteConfirmOpen = ref(false)
const isDeleting = ref(false)
const agreementPendingDelete = ref<FinancialAgreement | undefined>(undefined)

// The project's Approved quotation, if any -- used to pre-fill Total
// Amount and Currency on the "Create Payment Plan" form instead of
// leaving them blank for staff to re-type from the quotation that was
// just approved. Sourced from the quotation, not a signed contract: the
// Payment Plan stage (where a plan actually gets created) comes
// *before* Contract now -- see project_service._assert_stage_exit_
// criteria's Payment Plan entry criterion, which requires exactly this
// same fact.
//
// Reads straight from quotationStore.quotations without loading it
// here -- ProjectWorkspacePage.vue's own loadData() already fetches
// this project's quotations before any tab (this one included) ever
// mounts.
const approvedQuotation = () => quotationStore.quotations.find((quotation) => quotation.status === 'Approved')

const allRequiredAgreementsApproved = () =>
  visibleStreams.value.length > 0 && visibleStreams.value.every((stream) => agreementForStream(stream)?.status === 'Approved')

// The stepper (WorkflowProgress.vue) lets staff jump back to this tab
// from a project that's already moved past it (e.g. reviewing the
// approved plan while the project now sits at Design) -- see
// stageContext in ProjectWorkspacePage.vue. Once that's happened, the
// banner above correctly stops showing (it's not relevant anymore),
// but nothing was left in its place saying where the project actually
// is now or how to get back there -- the tab just went quiet, reading
// as a dead end. This replaces it with a pointer to wherever
// current_stage really is.
const projectHasMovedOn = () => hasProjectPassedStage(props.project.currentStage, 'Contract')
const currentStageLabel = () => t(getWorkflowStageLabelKey(props.project.currentStage))
function goToCurrentStage(): void {
  emit('navigate-tab', getWorkflowStageTabKey(props.project.currentStage))
}

const SCHEDULE_COLUMNS = computed<SmartTableColumn<{ id: string; sequenceNumber: number; description: string; amountDue: number; dueDate: string }>[]>(() => [
  { key: 'sequenceNumber', label: t('payment.planPanel.columns.number'), width: '48px' },
  { key: 'description', label: t('payment.planPanel.columns.installment') },
  { key: 'amountDue', label: t('payment.planPanel.columns.amount'), align: 'right' },
  { key: 'dueDate', label: t('payment.planPanel.columns.dueDate') },
])

function scheduleRows(stream: AgreementStream) {
  return obligationsForStream(stream)
    .slice()
    .sort((a, b) => a.sequenceNumber - b.sequenceNumber)
    .map((o) => ({ id: o.id, sequenceNumber: o.sequenceNumber, description: o.description, amountDue: o.amountDue, dueDate: formatDate(o.dueDate) }))
}

function openCreateAgreement(stream: AgreementStream): void {
  agreementFormMode.value = 'create'
  agreementFormStream.value = stream
  agreementBeingEdited.value = undefined
  isAgreementFormOpen.value = true
}

function openEditAgreement(agreement: FinancialAgreement): void {
  agreementFormMode.value = 'edit'
  agreementFormStream.value = agreement.stream
  agreementBeingEdited.value = agreement
  isAgreementFormOpen.value = true
}

// Once this approval was the last one a project needs (every visible
// stream now Approved), there's nothing left to decide on this tab --
// same "decision made -> move straight on" shape as the Quotation tab's
// own Approve (handleConfirmApproval navigates to Payment Plan the
// instant the quotation is Approved, with no separate "Advance" step in
// between). This replaces the old manual "Advance to Contract" banner:
// approving the last stream now takes staff straight to Contract with
// its New Contract dialog already open on the approved quotation (see
// handleAdvanceToContract).
async function handleApproveAgreement(agreement: FinancialAgreement): Promise<void> {
  isApprovingStream.value = agreement.stream
  try {
    await store.approveAgreement(agreement.id)
    await projectStore.refreshProject(props.projectId)
    resultDialogStore.showSuccess(t('payment.planPanel.streamPlanApprovedTitle', { stream: agreementStreamLabel(agreement.stream) }), t('payment.planPanel.planApprovedDescription'))
    if (allRequiredAgreementsApproved() && !hasProjectPassedStage(props.project.currentStage, 'Contract')) {
      handleAdvanceToContract()
    }
  } catch (error) {
    resultDialogStore.showError(t('payment.planPanel.couldNotApprove'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isApprovingStream.value = undefined
  }
}

// Hands the already-approved quotation off via the store and switches
// to the Contract tab, which picks up the pending request and opens its
// New Contract dialog prefilled from it -- same mechanism
// ProjectQuotationTab.vue used to trigger itself before this hop moved
// here (see quotationStore.requestAdvanceToContract).
function handleAdvanceToContract(): void {
  const quotation = approvedQuotation()
  if (!quotation) return
  quotationStore.requestAdvanceToContract(quotation.id)
  emit('navigate-tab', 'contract')
}

async function handleSubmitAgreement(input: CreateAgreementInput): Promise<void> {
  try {
    if (agreementFormMode.value === 'edit' && agreementBeingEdited.value) {
      await store.updateAgreement(agreementBeingEdited.value.id, input)
      resultDialogStore.showSuccess(t('payment.planPanel.planUpdatedTitle'), t('payment.planPanel.planUpdatedDescription'))
    } else {
      await store.createAgreement(input, 'Rajan Kumar')
      resultDialogStore.showSuccess(t('payment.planPanel.planCreatedTitle'), t('payment.planPanel.planCreatedDescription'))
    }
    isAgreementFormOpen.value = false
  } catch (error) {
    resultDialogStore.showError(t('payment.planPanel.couldNotSave'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  }
}

function requestDeleteAgreement(agreement: FinancialAgreement): void {
  agreementPendingDelete.value = agreement
  isDeleteConfirmOpen.value = true
}

async function handleConfirmDelete(): Promise<void> {
  if (!agreementPendingDelete.value) return
  isDeleting.value = true
  try {
    await store.deleteAgreement(agreementPendingDelete.value.id)
    resultDialogStore.showSuccess(t('payment.planPanel.planDeletedTitle'))
    isDeleteConfirmOpen.value = false
  } catch (error) {
    resultDialogStore.showError(t('payment.planPanel.couldNotDelete'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isDeleting.value = false
  }
}

// Same merged-trigger toolbar pattern as ProjectQuotationTab.vue/
// ProjectContractTab.vue: one "Decision" dropdown and one "Print/
// Download" dropdown instead of a button per action. The generated
// document always covers every visible stream's plan in one PDF (see
// document_template_service.render_payment_plan_document).
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

// Every visible stream still in Draft gets its own menu item -- e.g.
// "Approve Design and Permit Plan" and "Approve Supervision Plan" can
// both show at once, same as Quotation's Decision menu offering
// Approve/Reject/Expire together.
const draftStreams = computed(() => visibleStreams.value.filter((stream) => agreementForStream(stream)?.status === 'Draft'))
const hasDecisionOptions = computed(() => draftStreams.value.length > 0)

async function handleApproveFromMenu(stream: AgreementStream): Promise<void> {
  closeDecisionMenu()
  const agreement = agreementForStream(stream)
  if (agreement) await handleApproveAgreement(agreement)
}

const isPrinting = ref(false)
async function handlePrint(): Promise<void> {
  const printWindow = window.open('', '_blank')
  isPrinting.value = true
  try {
    const blob = await documentTemplateService.getPaymentPlanDocumentPdf(props.project.projectNo, documentLanguage.value)
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
  isDownloadingDocument.value = true
  try {
    const blob = await documentTemplateService.downloadPaymentPlanDocument(props.project.projectNo, documentLanguage.value)
    triggerBlobDownload(blob, `${props.project.projectNo}-Payment-Plan.docx`)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('common.failedToGenerateDocument'), detail)
  } finally {
    isDownloadingDocument.value = false
  }
}

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

function openEmailDialog(): void {
  emailTo.value = props.client?.email ?? ''
  isEmailDialogOpen.value = true
}

async function handleSendEmail(): Promise<void> {
  if (!emailTo.value.trim()) return
  isSendingEmail.value = true
  try {
    await documentTemplateService.emailPaymentPlanDocument(props.project.projectNo, emailTo.value.trim(), documentLanguage.value)
    resultDialogStore.showSuccess(t('payment.planPanel.paymentPlanEmailedTitle'), t('common.sentTo', { email: emailTo.value.trim() }))
    isEmailDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('common.failedToSendEmail'), detail)
  } finally {
    isSendingEmail.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <EmptyState
      v-if="!hasAnyScope"
      :icon="Wallet"
      :title="t('payment.planPanel.noBillableTitle')"
      :description="t('payment.planPanel.noBillableDescription')"
      :action-label="t('payment.planPanel.addService')"
      @action="emit('add-service')"
    />

    <div class="flex flex-col gap-1">
      <h2 class="text-base font-semibold text-text-primary">{{ t('payment.planPanel.title') }}</h2>
    </div>

    <div
      v-if="projectHasMovedOn()"
      class="flex flex-col items-start justify-between gap-3 rounded-lg border border-info-100 bg-info-50 px-4 py-3 tablet:flex-row tablet:items-center no-print"
    >
      <p class="text-sm text-info-700">{{ t('payment.planPanel.projectMovedOn', { stage: currentStageLabel() }) }}</p>
      <BaseButton size="sm" :icon="advanceIcon" @click="goToCurrentStage">{{ t('payment.planPanel.goToStage', { stage: currentStageLabel() }) }}</BaseButton>
    </div>

    <div v-if="hasAnyScope" class="flex flex-wrap items-center justify-between gap-2">
      <BaseButton
        size="sm"
        :icon="Plus"
        :disabled="!nextMissingStream"
        class="no-print"
        @click="nextMissingStream && openCreateAgreement(nextMissingStream)"
      >
        {{ t('payment.planPanel.createPaymentPlan') }}
      </BaseButton>
      <div class="no-print flex flex-wrap items-center gap-2">
        <div v-if="hasDecisionOptions" ref="decisionMenuRef" class="relative">
          <BaseButton size="sm" :icon="ShieldCheck" :loading="isApprovingStream !== undefined" @click="toggleDecisionMenu">
            {{ t('payment.planPanel.decision') }}
            <ChevronDown class="ms-1 h-3.5 w-3.5" />
          </BaseButton>
          <div
            v-if="isDecisionMenuOpen"
            role="menu"
            class="absolute end-0 z-dropdown mt-1 w-64 rounded-lg border border-border-light bg-bg-card py-1.5 shadow-elevated"
          >
            <button
              v-for="stream in draftStreams"
              :key="stream"
              type="button"
              role="menuitem"
              class="flex w-full items-center gap-2.5 px-3.5 py-2 text-start text-sm text-text-primary transition-colors duration-fast hover:bg-bg-hover"
              @click="handleApproveFromMenu(stream)"
            >
              <ShieldCheck class="h-4 w-4 text-success-600" />
              <span>{{ t('payment.planPanel.approveStreamPlan', { stream: sectionLabel(stream) }) }}</span>
            </button>
          </div>
        </div>
        <SelectBox v-if="hasAnyAgreement" v-model="documentLanguage" :options="LANGUAGE_OPTIONS" class="w-28" />
        <div v-if="hasAnyAgreement" ref="documentMenuRef" class="relative">
          <BaseButton variant="secondary" size="sm" :icon="Printer" :loading="isPrinting || isDownloadingDocument" @click="toggleDocumentMenu">
            {{ t('payment.planPanel.printOrDownload') }}
            <ChevronDown class="ms-1 h-3.5 w-3.5" />
          </BaseButton>
          <div
            v-if="isDocumentMenuOpen"
            role="menu"
            class="absolute end-0 z-dropdown mt-1 w-56 rounded-lg border border-border-light bg-bg-card py-1.5 shadow-elevated"
          >
            <button
              type="button"
              role="menuitem"
              class="flex w-full items-center gap-2.5 px-3.5 py-2 text-start text-sm text-text-primary transition-colors duration-fast hover:bg-bg-hover"
              @click="handlePrintFromMenu"
            >
              <Printer class="h-4 w-4 text-text-muted" />
              <span>{{ t('payment.planPanel.printPaymentPlan') }}</span>
            </button>
            <button
              type="button"
              role="menuitem"
              class="flex w-full items-center gap-2.5 px-3.5 py-2 text-start text-sm text-text-primary transition-colors duration-fast hover:bg-bg-hover"
              @click="handleDownloadFromMenu"
            >
              <Download class="h-4 w-4 text-text-muted" />
              <span>{{ t('payment.planPanel.downloadDocument') }}</span>
            </button>
          </div>
        </div>
        <BaseButton v-if="hasAnyAgreement" variant="secondary" size="sm" :icon="Mail" @click="openEmailDialog">
          {{ t('payment.planPanel.emailPaymentPlan') }}
        </BaseButton>
      </div>
    </div>

    <template v-for="section in sections" :key="section.kind === 'stream' ? section.stream : 'permits'">
      <div v-if="section.kind === 'stream'" class="flex flex-col gap-4">
        <div class="flex items-center gap-2">
          <h3 class="text-sm font-semibold uppercase tracking-wide text-text-muted">{{ sectionLabel(section.stream) }}</h3>
          <StatusBadge
            v-if="agreementForStream(section.stream)"
            :label="agreementStatusLabel(agreementForStream(section.stream)!.status)"
            :variant="agreementForStream(section.stream)!.status === 'Approved' ? 'success' : 'warning'"
          />
        </div>

        <EmptyState
          v-if="!agreementForStream(section.stream)"
          :icon="Wallet"
          :title="t('payment.planPanel.noPlanYetTitle')"
          :description="
            section.stream === 'Supervision'
              ? t('payment.planPanel.noPlanSupervisionDescription')
              : t('payment.planPanel.noPlanDesignDescription')
          "
          :action-label="t('payment.planPanel.createPaymentPlan')"
          @action="openCreateAgreement(section.stream)"
        />

        <template v-else>
          <Card>
            <div class="flex flex-col gap-4">
              <div class="flex items-center justify-end gap-2 no-print">
                <BaseButton
                  v-if="agreementForStream(section.stream)!.status === 'Draft'"
                  variant="secondary"
                  size="sm"
                  :icon="Pencil"
                  @click="openEditAgreement(agreementForStream(section.stream)!)"
                >
                  {{ t('payment.planPanel.edit') }}
                </BaseButton>
                <BaseButton
                  v-if="agreementForStream(section.stream)!.status === 'Draft'"
                  variant="ghost"
                  size="sm"
                  :icon="Trash2"
                  @click="requestDeleteAgreement(agreementForStream(section.stream)!)"
                >
                  {{ t('payment.planPanel.delete') }}
                </BaseButton>
              </div>

              <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-4">
                <div>
                  <p class="text-xs font-medium uppercase text-text-muted">{{ t('payment.planPanel.totalAmount') }}</p>
                  <p class="text-sm font-semibold text-text-primary">{{ formatCurrency(agreementForStream(section.stream)!.contractAmount, agreementForStream(section.stream)!.currency) }}</p>
                </div>
                <div>
                  <p class="text-xs font-medium uppercase text-text-muted">{{ t('payment.planPanel.paymentMode') }}</p>
                  <p class="text-sm text-text-primary">{{ paymentModeLabel(agreementForStream(section.stream)!.paymentMode) }}</p>
                </div>
                <div>
                  <p class="text-xs font-medium uppercase text-text-muted">{{ t('payment.planPanel.agreementDate') }}</p>
                  <p class="text-sm text-text-primary">{{ formatDate(agreementForStream(section.stream)!.agreementDate) }}</p>
                </div>
                <div>
                  <p class="text-xs font-medium uppercase text-text-muted">{{ t('payment.planPanel.startDate') }}</p>
                  <p class="text-sm text-text-primary">{{ formatDate(agreementForStream(section.stream)!.contractStartDate) }}</p>
                </div>
              </div>

              <SmartTable :columns="SCHEDULE_COLUMNS" :rows="scheduleRows(section.stream)" row-key="id" :searchable="false">
                <template #cell-amountDue="{ value }">
                  {{ formatCurrency(value as number, agreementForStream(section.stream)!.currency) }}
                </template>
              </SmartTable>
            </div>
          </Card>

          <PaymentHistoryPanel :events="store.auditEventsByAgreement[agreementForStream(section.stream)!.id] ?? []" />
        </template>
      </div>

      <div v-else class="flex flex-col gap-4">
        <h3 class="text-sm font-semibold uppercase tracking-wide text-text-muted">{{ t('payment.planPanel.permitsTitle') }}</h3>
        <Card :padded="false">
          <ul class="flex flex-col divide-y divide-border-light">
            <li v-for="permit in selectedPermits" :key="permit.id" class="flex items-center justify-between gap-3 px-5 py-3">
              <span class="text-sm text-text-secondary">{{ permit.permitName }}</span>
              <span class="shrink-0 text-sm font-medium text-text-primary">
                {{ permit.permitPrice != null ? formatCurrency(permit.permitPrice) : '—' }}
              </span>
            </li>
            <li class="flex items-center justify-between gap-3 bg-bg-secondary px-5 py-3">
              <span class="text-sm font-semibold text-text-primary">{{ t('payment.planPanel.totalPermitFees') }}</span>
              <span class="shrink-0 text-sm font-semibold text-text-primary">{{ formatCurrency(permitsTotal) }}</span>
            </li>
          </ul>
        </Card>
      </div>
    </template>

    <BaseDialog v-model="isEmailDialogOpen" :title="t('payment.planPanel.emailPaymentPlan')" size="sm">
      <TextInput v-model="emailTo" :label="t('payment.planPanel.recipientEmail')" type="email" required placeholder="client@example.com" />
      <template #footer>
        <BaseButton variant="secondary" @click="isEmailDialogOpen = false">{{ t('common.cancel') }}</BaseButton>
        <BaseButton :loading="isSendingEmail" :disabled="!emailTo.trim()" @click="handleSendEmail">{{ t('payment.planPanel.send') }}</BaseButton>
      </template>
    </BaseDialog>

    <AgreementFormDialog
      v-model="isAgreementFormOpen"
      :project-id="projectId"
      :stream="agreementFormStream"
      :mode="agreementFormMode"
      :existing-agreement="agreementBeingEdited"
      :existing-obligations="agreementBeingEdited ? obligationsForStream(agreementBeingEdited.stream) : []"
      :approved-contract="
        approvedQuotation()
          ? { quotationNo: approvedQuotation()!.quotationNo, contractValue: approvedQuotation()!.amount, currency: approvedQuotation()!.currency }
          : undefined
      "
      :is-submitting="store.isSubmitting"
      @submit="handleSubmitAgreement"
    />

    <ConfirmationDialog
      v-model="isDeleteConfirmOpen"
      :title="t('payment.planPanel.deletePaymentPlanConfirmTitle')"
      :message="t('payment.planPanel.deletePaymentPlanConfirmMessage', { stream: agreementPendingDelete ? agreementStreamLabel(agreementPendingDelete.stream) : '' })"
      :confirm-label="t('common.delete')"
      confirm-variant="danger"
      :loading="isDeleting"
      @confirm="handleConfirmDelete"
    />
  </div>
</template>
