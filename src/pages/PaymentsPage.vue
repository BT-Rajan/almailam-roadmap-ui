<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import ErrorState from '@/components/common/ErrorState.vue'
import InfoPanel from '@/components/common/InfoPanel.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { usePaymentStore } from '@/stores/paymentStore'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { getObligationStatusVariant } from '@/utils/paymentHelpers'
import type { AgreementStream, ObligationStatus } from '@/types/Payment'
import type { SmartTableColumn } from '@/types/Table'

const router = useRouter()
const store = usePaymentStore()
const { t } = useI18n()

interface AgreementTableRow {
  [key: string]: unknown
  id: string
  projectId: string
  projectName: string
  stream: AgreementStream
  clientName: string
  contractAmount: number
  totalReceived: number
  totalPending: number
  totalOverdue: number
  nextPaymentAmount: string
  nextPaymentDate: string
  nextPaymentStatus: string
}

const COLUMNS = computed<SmartTableColumn<AgreementTableRow>[]>(() => [
  { key: 'projectName', label: t('payment.paymentsPage.columns.project'), sortable: true },
  { key: 'stream', label: t('payment.paymentsPage.columns.stream'), sortable: true },
  { key: 'clientName', label: t('payment.paymentsPage.columns.client'), sortable: true },
  { key: 'contractAmount', label: t('payment.paymentsPage.columns.contractValue'), align: 'right', sortable: true },
  { key: 'totalReceived', label: t('payment.paymentsPage.columns.received'), align: 'right', sortable: true },
  { key: 'totalPending', label: t('payment.paymentsPage.columns.pending'), align: 'right', sortable: true },
  { key: 'totalOverdue', label: t('payment.paymentsPage.columns.overdue'), align: 'right', sortable: true },
  { key: 'nextPaymentAmount', label: t('payment.paymentsPage.columns.nextPayment'), align: 'right' },
  { key: 'nextPaymentDate', label: t('payment.paymentsPage.columns.nextPaymentDate') },
  { key: 'nextPaymentStatus', label: t('payment.paymentsPage.columns.status') },
])

const rows = computed<AgreementTableRow[]>(() =>
  store.filteredAgreementRows.map(({ agreement, project, client, summary }) => {
    const nextPaymentStatus: ObligationStatus = !summary.nextPaymentObligation ? 'Paid' : summary.nextPaymentIsOverdue ? 'Overdue' : 'Scheduled'
    return {
      id: agreement.id,
      projectId: agreement.projectId,
      projectName: project?.projectName ?? t('project.unknownProject'),
      stream: agreement.stream,
      clientName: client?.companyName ?? t('project.unknownClient'),
      contractAmount: summary.contractAmount,
      totalReceived: summary.totalReceived,
      totalPending: summary.totalPending,
      totalOverdue: summary.totalOverdue,
      nextPaymentAmount: summary.nextPaymentObligation
        ? formatCurrency(summary.nextPaymentObligation.amountDue - summary.nextPaymentObligation.amountReceived, agreement.currency)
        : '—',
      nextPaymentDate: summary.nextPaymentObligation ? formatDate(summary.nextPaymentObligation.dueDate) : '—',
      nextPaymentStatus,
    }
  }),
)

function goToProjectPayments(row: AgreementTableRow): void {
  // This table is about collections (received/pending/overdue), so a
  // row click lands on Payment Status -- the plan itself (create/edit/
  // approve) lives one tab over, at Payment Plan.
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: row.projectId }, query: { tab: 'payment-status' } })
}

function loadData(): void {
  void store.loadAll()
}

const AGREEMENT_STREAM_LABEL_KEYS: Record<string, string> = {
  Design: 'payment.agreementStream.design',
  Supervision: 'payment.agreementStream.supervision',
}
function streamLabel(stream: string): string {
  return t(AGREEMENT_STREAM_LABEL_KEYS[stream] ?? stream)
}

const OBLIGATION_STATUS_LABEL_KEYS: Record<string, string> = {
  Scheduled: 'payment.obligationStatus.scheduled',
  Due: 'payment.obligationStatus.due',
  'Partially Paid': 'payment.obligationStatus.partiallyPaid',
  Paid: 'payment.obligationStatus.paid',
  Overdue: 'payment.obligationStatus.overdue',
  'Partially Overdue': 'payment.obligationStatus.partiallyOverdue',
  Cancelled: 'payment.obligationStatus.cancelled',
  Waived: 'payment.obligationStatus.waived',
}
function obligationStatusLabel(status: string): string {
  return t(OBLIGATION_STATUS_LABEL_KEYS[status] ?? status)
}

onMounted(loadData)
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader :title="t('payment.paymentsPage.title')" :subtitle="t('payment.paymentsPage.subtitle')" />

    <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-4">
      <InfoPanel :label="t('payment.paymentsPage.totalContractValue')" :value="formatCurrency(store.portfolioSummary.contractAmount, 'KWD')" color="primary" />
      <InfoPanel :label="t('payment.paymentsPage.totalReceived')" :value="formatCurrency(store.portfolioSummary.totalReceived, 'KWD')" color="success" />
      <InfoPanel :label="t('payment.paymentsPage.totalPending')" :value="formatCurrency(store.portfolioSummary.totalPending, 'KWD')" color="warning" />
      <InfoPanel :label="t('payment.paymentsPage.totalOverdue')" :value="formatCurrency(store.portfolioSummary.totalOverdue, 'KWD')" :color="store.portfolioSummary.totalOverdue > 0 ? 'danger' : 'neutral'" />
    </div>

    <ErrorState v-if="store.error" :description="store.error" @retry="loadData" />

    <SmartTable
      v-else
      :columns="COLUMNS"
      :rows="rows"
      row-key="id"
      :loading="store.isLoading"
      :searchable="false"
      :empty-title="t('payment.paymentsPage.emptyTitle')"
      :empty-description="t('payment.paymentsPage.emptyDescription')"
      @row-click="goToProjectPayments"
    >
      <template #cell-stream="{ value }">
        <StatusBadge :label="streamLabel(value as string)" :variant="(value as string) === 'Supervision' ? 'info' : 'neutral'" />
      </template>
      <template #cell-contractAmount="{ row, value }">
        {{ formatCurrency(value as number, store.getAgreementByProject((row as AgreementTableRow).projectId, (row as AgreementTableRow).stream)?.currency ?? 'KWD') }}
      </template>
      <template #cell-totalReceived="{ row, value }">
        {{ formatCurrency(value as number, store.getAgreementByProject((row as AgreementTableRow).projectId, (row as AgreementTableRow).stream)?.currency ?? 'KWD') }}
      </template>
      <template #cell-totalPending="{ row, value }">
        {{ formatCurrency(value as number, store.getAgreementByProject((row as AgreementTableRow).projectId, (row as AgreementTableRow).stream)?.currency ?? 'KWD') }}
      </template>
      <template #cell-totalOverdue="{ row, value }">
        <span :class="(value as number) > 0 ? 'font-semibold text-danger-600' : ''">
          {{ formatCurrency(value as number, store.getAgreementByProject((row as AgreementTableRow).projectId, (row as AgreementTableRow).stream)?.currency ?? 'KWD') }}
        </span>
      </template>
      <template #cell-nextPaymentAmount="{ row }">
        <span :class="(row as AgreementTableRow).nextPaymentStatus === 'Overdue' ? 'font-semibold text-danger-600' : ''">
          {{ (row as AgreementTableRow).nextPaymentAmount }}
        </span>
      </template>
      <template #cell-nextPaymentDate="{ row }">
        <span :class="(row as AgreementTableRow).nextPaymentStatus === 'Overdue' ? 'font-semibold text-danger-600' : ''">
          {{ (row as AgreementTableRow).nextPaymentDate }}
        </span>
      </template>
      <template #cell-nextPaymentStatus="{ value }">
        <StatusBadge :label="obligationStatusLabel(value as string)" :variant="getObligationStatusVariant(value as ObligationStatus)" />
      </template>
    </SmartTable>
  </div>
</template>
