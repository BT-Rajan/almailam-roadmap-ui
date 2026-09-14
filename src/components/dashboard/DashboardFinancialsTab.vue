<script setup lang="ts">
import { AlertOctagon, Banknote } from '@lucide/vue'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import KPIWidget from '@/components/dashboard/KPIWidget.vue'
import StatisticsCard from '@/components/dashboard/StatisticsCard.vue'
import OverdueAgreementsWidget from '@/components/dashboard/OverdueAgreementsWidget.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { usePaymentStore } from '@/stores/paymentStore'
import type { KPI, StatisticItem, OverdueAgreement } from '@/types/Dashboard'
import { formatCurrency } from '@/utils/currencyFormatter'

const router = useRouter()
const { t } = useI18n()
const paymentStore = usePaymentStore()

// loadAll() also ensures projectStore/clientStore/quotationStore are
// populated (see paymentStore.ts) -- deliberately not fetched until this
// tab is actually opened, since it's the heaviest of the four loads and
// most dashboard visits won't need it.
onMounted(() => {
  if (paymentStore.agreements.length === 0 && !paymentStore.isLoading) void paymentStore.loadAll()
})

// Same portfolioSummary getter the Payments page's own totals use -- one
// definition of "received"/"pending"/"overdue," not a second copy that
// could drift from it.
const kpis = computed<KPI[]>(() => [
  { id: 'contract', label: t('dashboard.totalContractValue'), value: formatCurrency(paymentStore.portfolioSummary.contractAmount) },
  { id: 'received', label: t('dashboard.totalReceived'), value: formatCurrency(paymentStore.portfolioSummary.totalReceived) },
])

const statistics = computed<StatisticItem[]>(() => [
  {
    id: 'pending',
    label: t('dashboard.totalPending'),
    value: formatCurrency(paymentStore.portfolioSummary.totalPending),
    icon: Banknote,
    color: 'info',
  },
  {
    id: 'overdue',
    label: t('dashboard.totalOverdue'),
    value: formatCurrency(paymentStore.portfolioSummary.totalOverdue),
    icon: AlertOctagon,
    color: 'danger',
  },
])

const overdueAgreements = computed<OverdueAgreement[]>(() =>
  paymentStore.agreementRows
    .filter((row) => row.summary.totalOverdue > 0)
    .map((row) => ({
      id: row.agreement.id,
      projectId: row.agreement.projectId,
      project: row.project?.projectName ?? 'Unknown Project',
      client: row.client?.companyName ?? 'Unknown Client',
      overdueAmount: row.summary.totalOverdue,
      currency: row.agreement.currency,
    })),
)

function handleKpiClick(): void {
  router.push({ name: ROUTE_NAMES.PAYMENTS })
}

function handleAgreementClick(projectId: string): void {
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId } })
}
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-4 gap-4">
      <KPIWidget v-for="kpi in kpis" :key="kpi.id" :kpi="kpi" @click="handleKpiClick" />
      <StatisticsCard v-for="stat in statistics" :key="stat.id" :statistic="stat" @click="handleKpiClick" />
    </div>

    <OverdueAgreementsWidget :agreements="overdueAgreements" @agreement-click="handleAgreementClick" />
  </div>
</template>
