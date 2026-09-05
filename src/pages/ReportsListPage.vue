<script setup lang="ts">
import { BarChart3, TrendingUp, Users } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import Card from '@/components/common/Card.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'

const router = useRouter()
const { t } = useI18n()

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
    <div class="grid grid-cols-1 tablet:grid-cols-3 gap-6">
      <Card
        v-for="report in reports"
        :key="report.id"
        hoverable
        class="cursor-pointer transition-all hover:shadow-medium"
        @click="report.action"
      >
        <div class="space-y-4">
          <!-- Icon -->
          <div :class="['w-12 h-12 rounded-lg flex items-center justify-center', report.color === 'primary' ? 'bg-primary-50' : report.color === 'info' ? 'bg-info-50' : 'bg-success-50']">
            <component :is="report.icon" :class="['h-6 w-6', report.color === 'primary' ? 'text-primary-600' : report.color === 'info' ? 'text-info-600' : 'text-success-600']" />
          </div>

          <!-- Content -->
          <div>
            <h3 class="text-lg font-semibold text-text-primary">{{ report.title }}</h3>
            <p class="text-sm text-text-secondary mt-2">{{ report.description }}</p>
          </div>

          <!-- Metrics -->
          <div class="space-y-1 pt-2 border-t border-border-light">
            <div v-for="metric in report.metrics" :key="metric" class="text-xs text-text-muted">
              <span class="inline-block w-1.5 h-1.5 rounded-full me-2" :class="report.color === 'primary' ? 'bg-primary-300' : report.color === 'info' ? 'bg-info-300' : 'bg-success-300'" />
              {{ metric }}
            </div>
          </div>

          <!-- CTA -->
          <div class="pt-2">
            <button class="text-sm font-medium transition-colors" :class="report.color === 'primary' ? 'text-primary-600 hover:text-primary-700' : report.color === 'info' ? 'text-info-600 hover:text-info-700' : 'text-success-600 hover:text-success-700'">
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
