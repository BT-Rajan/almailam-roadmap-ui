<script setup lang="ts">
import { AlertOctagon, Banknote, TrendingUp, Wallet } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import StatisticsCard from '@/components/dashboard/StatisticsCard.vue'
import OverdueAgreementsWidget from '@/components/dashboard/OverdueAgreementsWidget.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { reportService } from '@/services/reportService'
import { usePaymentStore } from '@/stores/paymentStore'
import { currentMonthRange } from '@/utils/dateFormatter'
import type { FinancialPeriodSummary } from '@/types/Report'
import type { StatisticItem, OverdueAgreement } from '@/types/Dashboard'
import { formatCurrency } from '@/utils/currencyFormatter'

const router = useRouter()
const { t } = useI18n()
const paymentStore = usePaymentStore()

// Real, period-scoped figures from the same backend aggregation the
// Monthly Financials report uses (report_service.py's
// financial_period_summary) -- not derived/estimated client-side, and
// not the all-time portfolio totals this tab used to show under
// 'Total Contract Value'/'Total Received' labels that didn't actually
// say they were all-time.
const monthSummary = ref<FinancialPeriodSummary>()
const isLoadingMonthSummary = ref(false)

// loadAll() also ensures projectStore/clientStore/quotationStore are
// populated (see paymentStore.ts) -- deliberately not fetched until this
// tab is actually opened, since it's the heaviest of the four loads and
// most dashboard visits won't need it.
onMounted(async () => {
  if (paymentStore.agreements.length === 0 && !paymentStore.isLoading) void paymentStore.loadAll()
  isLoadingMonthSummary.value = true
  try {
    const { start, end } = currentMonthRange()
    monthSummary.value = await reportService.getFinancialSummary(start, end)
  } finally {
    isLoadingMonthSummary.value = false
  }
})

// One consistent card (StatisticsCard) for every figure here -- this
// tab previously mixed StatisticsCard with a second, differently-styled
// KPIWidget for no functional reason, so the row read as two unrelated
// sets of cards rather than one summary.
const statistics = computed<StatisticItem[]>(() => [
  {
    id: 'earned',
    label: t('dashboard.totalEarnedThisMonth'),
    value: monthSummary.value ? formatCurrency(monthSummary.value.totalDue) : '\u2014',
    icon: TrendingUp,
    color: 'primary',
  },
  {
    id: 'collected',
    label: t('dashboard.totalCollectedThisMonth'),
    value: monthSummary.value ? formatCurrency(monthSummary.value.totalReceived) : '\u2014',
    icon: Wallet,
    color: 'success',
  },
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

function handleStatisticClick(): void {
  router.push({ name: ROUTE_NAMES.PAYMENTS })
}

function handleAgreementClick(projectId: string): void {
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId } })
}
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-4 gap-4">
      <StatisticsCard v-for="stat in statistics" :key="stat.id" :statistic="stat" @click="handleStatisticClick" />
    </div>

    <OverdueAgreementsWidget :agreements="overdueAgreements" @agreement-click="handleAgreementClick" />
  </div>
</template>
