<script setup lang="ts">
import { AlertOctagon, Banknote, TrendingUp, Wallet } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import StatisticsCard from '@/components/dashboard/StatisticsCard.vue'
import OverdueAgreementsWidget from '@/components/dashboard/OverdueAgreementsWidget.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { reportService } from '@/services/reportService'
import ErrorState from '@/components/common/ErrorState.vue'
import { useDashboardData } from '@/composables/useDashboardData'
import { dashboardService } from '@/services/dashboardService'
import { currentMonthRange } from '@/utils/dateFormatter'
import type { FinancialPeriodSummary } from '@/types/Report'
import type { StatisticItem, OverdueAgreement } from '@/types/Dashboard'
import { formatCurrency } from '@/utils/currencyFormatter'

const router = useRouter()
const { t } = useI18n()
// Portfolio pending/overdue totals and the agreements with anything
// overdue, computed server-side with the same rule the Payments page uses
// -- this tab no longer downloads every agreement, instalment, project and
// client in the company.
const { data, error, isStale, reload } = useDashboardData('financials', dashboardService.getFinancials)

// Real, period-scoped figures from the same backend aggregation the
// Monthly Financials report uses (report_service.py's
// financial_period_summary) -- not derived/estimated client-side, and
// not the all-time portfolio totals this tab used to show under
// 'Total Contract Value'/'Total Received' labels that didn't actually
// say they were all-time.
const monthSummary = ref<FinancialPeriodSummary>()
const isLoadingMonthSummary = ref(false)

// financial_period_summary splits every total by currency (a project's
// Design and Supervision agreements can be priced differently -- see
// that function's own comment) rather than summing them, which a
// compact 4-card dashboard tile has no room to show broken out. Picks
// the currency with the largest amount billed this period as the one
// "primary" figure to show -- correct and clearly labeled for the
// common single-currency case, and a reasonable single representative
// figure on the rare month a company bills in more than one.
const primaryCurrencyEntry = computed(() => {
  const entries = monthSummary.value?.byCurrency ?? []
  if (entries.length === 0) return undefined
  return entries.reduce((largest, entry) => (entry.totalDue > largest.totalDue ? entry : largest), entries[0])
})

onMounted(async () => {
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
    value: primaryCurrencyEntry.value ? formatCurrency(primaryCurrencyEntry.value.totalDue, primaryCurrencyEntry.value.currency) : '\u2014',
    icon: TrendingUp,
    color: 'primary',
  },
  {
    id: 'collected',
    label: t('dashboard.totalCollectedThisMonth'),
    value: primaryCurrencyEntry.value ? formatCurrency(primaryCurrencyEntry.value.totalReceived, primaryCurrencyEntry.value.currency) : '\u2014',
    icon: Wallet,
    color: 'success',
  },
  {
    id: 'pending',
    label: t('dashboard.totalPending'),
    value: formatCurrency(data.value?.totalPending ?? 0),
    icon: Banknote,
    color: 'info',
  },
  {
    id: 'overdue',
    label: t('dashboard.totalOverdue'),
    value: formatCurrency(data.value?.totalOverdue ?? 0),
    icon: AlertOctagon,
    color: 'danger',
  },
])

// Largest overdue amount first.
const overdueAgreements = computed<OverdueAgreement[]>(() => data.value?.overdueAgreements ?? [])

function handleStatisticClick(): void {
  router.push({ name: ROUTE_NAMES.PAYMENTS })
}

function handleAgreementClick(projectId: string): void {
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId } })
}
</script>

<template>
  <ErrorState v-if="error" :description="error" @retry="reload" />
  <div v-else class="space-y-6">
    <p v-if="isStale" class="flex flex-wrap items-center gap-2 text-xs text-text-muted" role="status">
      {{ t('dashboard.staleNotice') }}
      <button type="button" class="font-medium text-primary-600 hover:text-primary-700" @click="reload">{{ t('dashboard.retry') }}</button>
    </p>
    <div class="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-4 gap-4">
      <StatisticsCard v-for="stat in statistics" :key="stat.id" :statistic="stat" @click="handleStatisticClick" />
    </div>

    <OverdueAgreementsWidget :agreements="overdueAgreements" @agreement-click="handleAgreementClick" />
  </div>
</template>
