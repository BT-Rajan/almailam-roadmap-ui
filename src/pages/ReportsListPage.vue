<script setup lang="ts">
import { BarChart3, Building2, GitBranch, ListTree, Receipt, TrendingUp, Users } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import Card from '@/components/common/Card.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'

const router = useRouter()
const { t } = useI18n()

// One lookup per Tailwind-color-driven class set below, keyed by the same
// `color` string each report entry already carries -- previously three
// nested ternaries per class list, which silently fell through to
// success-* for any color beyond primary/info/success. Extending the grid
// with more reports (warning/danger accents included) is now just adding
// a key here instead of a fourth ternary branch in every template spot.
const COLOR_CLASSES: Record<string, { bg: string; icon: string; dot: string; link: string }> = {
  primary: { bg: 'bg-primary-50', icon: 'text-primary-600', dot: 'bg-primary-300', link: 'text-primary-600 hover:text-primary-700' },
  info: { bg: 'bg-info-50', icon: 'text-info-600', dot: 'bg-info-300', link: 'text-info-600 hover:text-info-700' },
  success: { bg: 'bg-success-50', icon: 'text-success-600', dot: 'bg-success-300', link: 'text-success-600 hover:text-success-700' },
  warning: { bg: 'bg-warning-50', icon: 'text-warning-600', dot: 'bg-warning-300', link: 'text-warning-600 hover:text-warning-700' },
}
function colorClasses(color: string) {
  return COLOR_CLASSES[color] ?? COLOR_CLASSES.success
}

const reports = computed(() => [
  {
    id: 'executive',
    title: t('report.listPage.executiveTitle'),
    description: t('report.listPage.executiveDescription'),
    icon: TrendingUp,
    color: 'primary',
    metrics: [
      t('report.listPage.executiveMetric1', { count: 5 }),
      t('report.listPage.executiveMetric2', { percent: 87 }),
      t('report.listPage.executiveMetric3', { percent: 82 }),
    ],
    action: () => router.push({ name: ROUTE_NAMES.REPORT_EXECUTIVE }),
  },
  {
    id: 'project',
    title: t('report.listPage.projectTitle'),
    description: t('report.listPage.projectDescription'),
    icon: BarChart3,
    color: 'info',
    metrics: [
      'Marina Bay Hotel Renovation',
      t('report.listPage.projectMetric2', { percent: 42 }),
      t('report.listPage.projectMetric3'),
    ],
    action: () => router.push({ name: ROUTE_NAMES.REPORT_PROJECT }),
  },
  {
    id: 'workload',
    title: t('report.listPage.workloadTitle'),
    description: t('report.listPage.workloadDescription'),
    icon: Users,
    color: 'success',
    metrics: [
      t('report.listPage.workloadMetric1', { count: 3 }),
      t('report.listPage.workloadMetric2', { percent: 82 }),
      t('report.listPage.workloadMetric3', { percent: 18 }),
    ],
    action: () => router.push({ name: ROUTE_NAMES.REPORT_WORKLOAD }),
  },
  {
    id: 'employee-activity',
    title: t('report.listPage.employeeActivityTitle'),
    description: t('report.listPage.employeeActivityDescription'),
    icon: ListTree,
    color: 'warning',
    metrics: [
      t('report.listPage.employeeActivityMetric1'),
      t('report.listPage.employeeActivityMetric2'),
      t('report.listPage.employeeActivityMetric3'),
    ],
    action: () => router.push({ name: ROUTE_NAMES.REPORT_EMPLOYEE_ACTIVITY }),
  },
  {
    id: 'project-tree',
    title: t('report.listPage.projectTreeTitle'),
    description: t('report.listPage.projectTreeDescription'),
    icon: GitBranch,
    color: 'info',
    metrics: [
      t('report.listPage.projectTreeMetric1'),
      t('report.listPage.projectTreeMetric2'),
      t('report.listPage.projectTreeMetric3'),
    ],
    action: () => router.push({ name: ROUTE_NAMES.REPORT_PROJECT_TREE }),
  },
  {
    id: 'client-projects',
    title: t('report.listPage.clientProjectsTitle'),
    description: t('report.listPage.clientProjectsDescription'),
    icon: Building2,
    color: 'success',
    metrics: [
      t('report.listPage.clientProjectsMetric1'),
      t('report.listPage.clientProjectsMetric2'),
      t('report.listPage.clientProjectsMetric3'),
    ],
    action: () => router.push({ name: ROUTE_NAMES.REPORT_CLIENT_PROJECTS }),
  },
  {
    id: 'payment-ledger',
    title: t('report.listPage.paymentLedgerTitle'),
    description: t('report.listPage.paymentLedgerDescription'),
    icon: Receipt,
    color: 'primary',
    metrics: [
      t('report.listPage.paymentLedgerMetric1'),
      t('report.listPage.paymentLedgerMetric2'),
      t('report.listPage.paymentLedgerMetric3'),
    ],
    action: () => router.push({ name: ROUTE_NAMES.REPORT_PAYMENT_LEDGER }),
  },
])
</script>

<template>
  <div class="space-y-8 pb-12">
    <!-- Page Header -->
    <div>
      <h1 class="text-4xl font-bold text-text-primary">{{ t('report.listPage.pageTitle') }}</h1>
      <p class="text-text-secondary mt-2">{{ t('report.listPage.pageSubtitle') }}</p>
    </div>

    <!-- Reports Grid -->
    <div class="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-3 gap-6">
      <Card
        v-for="report in reports"
        :key="report.id"
        hoverable
        class="cursor-pointer transition-all hover:shadow-medium"
        @click="report.action"
      >
        <div class="space-y-4">
          <!-- Icon -->
          <div :class="['w-12 h-12 rounded-lg flex items-center justify-center', colorClasses(report.color).bg]">
            <component :is="report.icon" :class="['h-6 w-6', colorClasses(report.color).icon]" />
          </div>

          <!-- Content -->
          <div>
            <h3 class="text-lg font-semibold text-text-primary">{{ report.title }}</h3>
            <p class="text-sm text-text-secondary mt-2">{{ report.description }}</p>
          </div>

          <!-- Metrics -->
          <div class="space-y-1 pt-2 border-t border-border-light">
            <div v-for="metric in report.metrics" :key="metric" class="text-xs text-text-muted">
              <span class="inline-block w-1.5 h-1.5 rounded-full me-2" :class="colorClasses(report.color).dot" />
              {{ metric }}
            </div>
          </div>

          <!-- CTA -->
          <div class="pt-2">
            <button class="text-sm font-medium transition-colors" :class="colorClasses(report.color).link">
              {{ t('report.listPage.viewReport') }} →
            </button>
          </div>
        </div>
      </Card>
    </div>

    <!-- Info Section -->
    <Card class="bg-gradient-to-r from-primary-50 to-info-50 border border-primary-200">
      <div class="space-y-3">
        <h3 class="text-lg font-semibold text-text-primary">📊 {{ t('report.listPage.aboutReports') }}</h3>
        <div class="space-y-2 text-sm text-text-secondary">
          <p>
            <strong>{{ t('report.listPage.aboutExecutiveLabel') }}</strong> {{ t('report.listPage.aboutExecutiveText') }}
          </p>
          <p>
            <strong>{{ t('report.listPage.aboutProjectLabel') }}</strong> {{ t('report.listPage.aboutProjectText') }}
          </p>
          <p>
            <strong>{{ t('report.listPage.aboutWorkloadLabel') }}</strong> {{ t('report.listPage.aboutWorkloadText') }}
          </p>
        </div>
        <p class="text-xs text-text-muted pt-2">💡 {{ t('report.listPage.tip') }}</p>
      </div>
    </Card>
  </div>
</template>
