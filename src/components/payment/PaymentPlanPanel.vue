<script setup lang="ts">
import { ArrowRight, CheckCircle2, Pencil, Trash2, Wallet } from '@lucide/vue'
import { ref } from 'vue'

import AgreementFormDialog from '@/components/payment/AgreementFormDialog.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PaymentHistoryPanel from '@/components/payment/PaymentHistoryPanel.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { usePaymentAgreements } from '@/composables/usePaymentAgreements'
import { usePaymentStore } from '@/stores/paymentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { getAgreementStreamLabel } from '@/utils/paymentHelpers'
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

const anyAgreementMissing = () => visibleStreams.value.some((stream) => !agreementForStream(stream))

const planExplainer = () => {
  const parts: string[] = []
  if (visibleStreams.value.includes('Design')) {
    parts.push('a one-time Design & Permit fee, paid in full or split into up to 5 installments you control')
  }
  if (visibleStreams.value.includes('Supervision')) {
    parts.push('a monthly Supervision fee, billed pro-rata for partial months')
  }
  if (parts.length === 2) return `This project's payment plan has two parts: ${parts[0]}, and ${parts[1]}.`
  if (parts.length === 1) return `This project's payment plan is ${parts[0]}.`
  return ''
}

const SCHEDULE_COLUMNS: SmartTableColumn<{ id: string; sequenceNumber: number; description: string; amountDue: number; dueDate: string }>[] = [
  { key: 'sequenceNumber', label: '#', width: '48px' },
  { key: 'description', label: 'Installment' },
  { key: 'amountDue', label: 'Amount', align: 'right' },
  { key: 'dueDate', label: 'Due Date' },
]

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
      title="No billable services selected"
      description="This project has no Design or Supervision work selected, so there's no payment plan to create yet."
    />

    <div class="flex flex-col gap-1">
      <h2 class="text-base font-semibold text-text-primary">Project Payment Plan</h2>
      <p v-if="anyAgreementMissing()" class="text-sm text-text-muted">{{ planExplainer() }} Every part has to be approved here before this project can move to Contract.</p>
    </div>

    <div
      v-if="allRequiredAgreementsApproved()"
      class="flex flex-col items-start justify-between gap-3 rounded-lg border border-success-100 bg-success-50 px-4 py-3 tablet:flex-row tablet:items-center no-print"
    >
      <p class="text-sm text-success-700">Every required payment plan is approved -- this project is ready for Contract.</p>
      <BaseButton size="sm" :icon="ArrowRight" @click="handleAdvanceToContract">Advance to Contract</BaseButton>
    </div>

    <div v-for="stream in visibleStreams" :key="stream" class="flex flex-col gap-4">
      <div v-if="visibleStreams.length > 1" class="flex items-center gap-2">
        <h3 class="text-sm font-semibold uppercase tracking-wide text-text-muted">{{ getAgreementStreamLabel(stream) }}</h3>
        <StatusBadge
          v-if="agreementForStream(stream)"
          :label="agreementForStream(stream)!.status"
          :variant="agreementForStream(stream)!.status === 'Approved' ? 'success' : 'warning'"
        />
      </div>

      <EmptyState
        v-if="!agreementForStream(stream)"
        :icon="Wallet"
        title="No payment plan yet"
        :description="
          stream === 'Supervision'
            ? 'Create a payment plan to generate its day-prorated monthly schedule for this project.'
            : 'Create a one-time payment plan for this project -- paid in full, or split into up to 5 installments you control.'
        "
        action-label="Create Payment Plan"
        @action="openCreateAgreement(stream)"
      />

      <template v-else>
        <Card>
          <div class="flex flex-col gap-4">
            <div class="flex items-center justify-between gap-3">
              <div v-if="visibleStreams.length === 1">
                <StatusBadge
                  :label="agreementForStream(stream)!.status"
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
                  Approve Payment Plan
                </BaseButton>
                <BaseButton
                  v-if="agreementForStream(stream)!.status === 'Draft'"
                  variant="secondary"
                  size="sm"
                  :icon="Pencil"
                  @click="openEditAgreement(agreementForStream(stream)!)"
                >
                  Edit
                </BaseButton>
                <BaseButton
                  v-if="agreementForStream(stream)!.status === 'Draft'"
                  variant="ghost"
                  size="sm"
                  :icon="Trash2"
                  @click="requestDeleteAgreement(agreementForStream(stream)!)"
                >
                  Delete
                </BaseButton>
              </div>
            </div>

            <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-4">
              <div>
                <p class="text-xs font-medium uppercase text-text-muted">Total Amount</p>
                <p class="text-sm font-semibold text-text-primary">{{ formatCurrency(agreementForStream(stream)!.contractAmount, agreementForStream(stream)!.currency) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium uppercase text-text-muted">Payment Mode</p>
                <p class="text-sm text-text-primary">{{ agreementForStream(stream)!.paymentMode }}</p>
              </div>
              <div>
                <p class="text-xs font-medium uppercase text-text-muted">Agreement Date</p>
                <p class="text-sm text-text-primary">{{ formatDate(agreementForStream(stream)!.agreementDate) }}</p>
              </div>
              <div>
                <p class="text-xs font-medium uppercase text-text-muted">Start Date</p>
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
