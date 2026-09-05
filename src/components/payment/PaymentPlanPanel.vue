<script setup lang="ts">
import { ArrowLeft, ArrowRight, CheckCircle2, Pencil, Trash2, Wallet } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import AgreementFormDialog from '@/components/payment/AgreementFormDialog.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PaymentHistoryPanel from '@/components/payment/PaymentHistoryPanel.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useLocale } from '@/composables/useLocale'
import { usePaymentAgreements } from '@/composables/usePaymentAgreements'
import { usePaymentStore } from '@/stores/paymentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { getAgreementStreamLabel } from '@/utils/paymentHelpers'
import { hasProjectPassedStage } from '@/utils/projectHelpers'
import type { AgreementStream, CreateAgreementInput, FinancialAgreement } from '@/types/Payment'
import type { Project, ProjectWorkspaceTabKey } from '@/types/Project'
import type { SmartTableColumn } from '@/types/Table'

interface Props {
  projectId: string
  project: Project
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

// Gates the "Advance to Contract" banner specifically -- once the
// project has actually moved past Contract (Design, Government
// Submission, Supervision), every agreement is still permanently
// Approved, so allRequiredAgreementsApproved() alone would keep this
// banner dangling forever on an old Payment Plan tab visit.
const showAdvanceToContractBanner = () => allRequiredAgreementsApproved() && !hasProjectPassedStage(props.project.currentStage, 'Contract')

const anyAgreementMissing = () => visibleStreams.value.some((stream) => !agreementForStream(stream))

const planExplainer = () => {
  const parts: string[] = []
  if (visibleStreams.value.includes('Design')) {
    parts.push(t('payment.planPanel.explainerDesign'))
  }
  if (visibleStreams.value.includes('Supervision')) {
    parts.push(t('payment.planPanel.explainerSupervision'))
  }
  if (parts.length === 2) return t('payment.planPanel.explainerBoth', { design: parts[0], supervision: parts[1] })
  if (parts.length === 1) return t('payment.planPanel.explainerSingle', { part: parts[0] })
  return ''
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

async function handleApproveAgreement(agreement: FinancialAgreement): Promise<void> {
  isApprovingStream.value = agreement.stream
  try {
    await store.approveAgreement(agreement.id)
    await projectStore.refreshProject(props.projectId)
    resultDialogStore.showSuccess(`${getAgreementStreamLabel(agreement.stream)} payment plan approved`, 'The payment plan is now approved.')
  } catch (error) {
    resultDialogStore.showError('Could not approve payment plan', error instanceof Error ? error.message : 'Please try again.')
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
      resultDialogStore.showSuccess('Payment plan updated', 'The installment schedule has been regenerated.')
    } else {
      await store.createAgreement(input, 'Rajan Kumar')
      resultDialogStore.showSuccess('Payment plan created', 'Review the schedule, then approve it to continue.')
    }
    isAgreementFormOpen.value = false
  } catch (error) {
    resultDialogStore.showError('Could not save payment plan', error instanceof Error ? error.message : 'Please try again.')
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
    resultDialogStore.showSuccess('Payment plan deleted')
    isDeleteConfirmOpen.value = false
  } catch (error) {
    resultDialogStore.showError('Could not delete payment plan', error instanceof Error ? error.message : 'Please try again.')
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-8">
    <EmptyState
      v-if="visibleStreams.length === 0"
      :icon="Wallet"
      :title="t('payment.planPanel.noBillableTitle')"
      :description="t('payment.planPanel.noBillableDescription')"
      :action-label="t('payment.planPanel.addService')"
      @action="emit('add-service')"
    />

    <div class="flex flex-col gap-1">
      <h2 class="text-base font-semibold text-text-primary">{{ t('payment.planPanel.title') }}</h2>
      <p v-if="anyAgreementMissing()" class="text-sm text-text-muted">{{ planExplainer() }} {{ t('payment.planPanel.everyPartMustBeApproved') }}</p>
    </div>

    <div
      v-if="showAdvanceToContractBanner()"
      class="flex flex-col items-start justify-between gap-3 rounded-lg border border-success-100 bg-success-50 px-4 py-3 tablet:flex-row tablet:items-center no-print"
    >
      <p class="text-sm text-success-700">{{ t('payment.planPanel.readyForContract') }}</p>
      <BaseButton size="sm" :icon="advanceIcon" @click="handleAdvanceToContract">{{ t('payment.planPanel.advanceToContract') }}</BaseButton>
    </div>

    <div v-for="stream in visibleStreams" :key="stream" class="flex flex-col gap-4">
      <div v-if="visibleStreams.length > 1" class="flex items-center gap-2">
        <h3 class="text-sm font-semibold uppercase tracking-wide text-text-muted">{{ agreementStreamLabel(stream) }}</h3>
        <StatusBadge
          v-if="agreementForStream(stream)"
          :label="agreementStatusLabel(agreementForStream(stream)!.status)"
          :variant="agreementForStream(stream)!.status === 'Approved' ? 'success' : 'warning'"
        />
      </div>

      <EmptyState
        v-if="!agreementForStream(stream)"
        :icon="Wallet"
        :title="t('payment.planPanel.noPlanYetTitle')"
        :description="
          stream === 'Supervision'
            ? t('payment.planPanel.noPlanSupervisionDescription')
            : t('payment.planPanel.noPlanDesignDescription')
        "
        :action-label="t('payment.planPanel.createPaymentPlan')"
        @action="openCreateAgreement(stream)"
      />

      <template v-else>
        <Card>
          <div class="flex flex-col gap-4">
            <div class="flex items-center justify-between gap-3">
              <div v-if="visibleStreams.length === 1">
                <StatusBadge
                  :label="agreementStatusLabel(agreementForStream(stream)!.status)"
                  :variant="agreementForStream(stream)!.status === 'Approved' ? 'success' : 'warning'"
                />
              </div>
              <div v-else />
              <div class="flex flex-wrap items-center justify-end gap-2 no-print">
                <BaseButton
                  v-if="agreementForStream(stream)!.status === 'Draft'"
                  size="sm"
                  :icon="CheckCircle2"
                  :loading="isApprovingStream === stream"
                  @click="handleApproveAgreement(agreementForStream(stream)!)"
                >
                  {{ t('payment.planPanel.approvePaymentPlan') }}
                </BaseButton>
                <BaseButton
                  v-if="agreementForStream(stream)!.status === 'Draft'"
                  variant="secondary"
                  size="sm"
                  :icon="Pencil"
                  @click="openEditAgreement(agreementForStream(stream)!)"
                >
                  {{ t('payment.planPanel.edit') }}
                </BaseButton>
                <BaseButton
                  v-if="agreementForStream(stream)!.status === 'Draft'"
                  variant="ghost"
                  size="sm"
                  :icon="Trash2"
                  @click="requestDeleteAgreement(agreementForStream(stream)!)"
                >
                  {{ t('payment.planPanel.delete') }}
                </BaseButton>
              </div>
            </div>

            <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-4">
              <div>
                <p class="text-xs font-medium uppercase text-text-muted">{{ t('payment.planPanel.totalAmount') }}</p>
                <p class="text-sm font-semibold text-text-primary">{{ formatCurrency(agreementForStream(stream)!.contractAmount, agreementForStream(stream)!.currency) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium uppercase text-text-muted">{{ t('payment.planPanel.paymentMode') }}</p>
                <p class="text-sm text-text-primary">{{ paymentModeLabel(agreementForStream(stream)!.paymentMode) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium uppercase text-text-muted">{{ t('payment.planPanel.agreementDate') }}</p>
                <p class="text-sm text-text-primary">{{ formatDate(agreementForStream(stream)!.agreementDate) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium uppercase text-text-muted">{{ t('payment.planPanel.startDate') }}</p>
                <p class="text-sm text-text-primary">{{ formatDate(agreementForStream(stream)!.contractStartDate) }}</p>
              </div>
            </div>

            <SmartTable :columns="SCHEDULE_COLUMNS" :rows="scheduleRows(stream)" row-key="id" :searchable="false">
              <template #cell-amountDue="{ value }">
                {{ formatCurrency(value as number, agreementForStream(stream)!.currency) }}
              </template>
            </SmartTable>
          </div>
        </Card>

        <PaymentHistoryPanel :events="store.auditEventsByAgreement[agreementForStream(stream)!.id] ?? []" />
      </template>
    </div>

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
      title="Delete payment plan"
      :message="`Delete the ${agreementPendingDelete ? getAgreementStreamLabel(agreementPendingDelete.stream) : ''} payment plan? This removes its installment schedule too. This can't be undone.`"
      confirm-label="Delete"
      confirm-variant="danger"
      :loading="isDeleting"
      @confirm="handleConfirmDelete"
    />
  </div>
</template>
