<script setup lang="ts">
import { BarChart3, TrendingUp, Users } from '@lucide/vue'
import { useRouter } from 'vue-router'
import Card from '@/components/common/Card.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'

const router = useRouter()

const reports = [
  {
    id: 'executive',
    title: 'Executive Summary Report',
    description: 'High-level KPIs, project status distribution, delivery trends, and resource allocation overview.',
    icon: TrendingUp,
    color: 'primary',
    metrics: ['5 Active Projects', '87% Completion Rate', '82% Team Utilization'],
    action: () => router.push({ name: ROUTE_NAMES.REPORT_EXECUTIVE }),
  },
  {
    id: 'project',
    title: 'Project Performance Report',
    description: 'Detailed analysis of a specific project including progress, budget tracking, task status, and risk assessment.',
    icon: BarChart3,
    color: 'info',
    metrics: ['Marina Bay Hotel Renovation', '42% Complete', 'On Schedule'],
    action: () => router.push({ name: ROUTE_NAMES.REPORT_PROJECT }),
  },
  {
    id: 'workload',
    title: 'Team Workload Summary',
    description: 'Team capacity analysis, member allocation details, department utilization, and rebalancing recommendations.',
    icon: Users,
    color: 'success',
    metrics: ['3 Team Members', '82% Avg Utilization', '18% Capacity Free'],
    action: () => router.push({ name: ROUTE_NAMES.REPORT_WORKLOAD }),
  },
]
</script>

<template>
  <div class="space-y-8 pb-12">
    <!-- Page Header -->
    <div>
      <h1 class="text-4xl font-bold text-neutral-900">Reports</h1>
      <p class="text-neutral-600 mt-2">Access executive summaries, project performance analytics, and team workload insights.</p>
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
            <h3 class="text-lg font-semibold text-neutral-900">{{ report.title }}</h3>
            <p class="text-sm text-neutral-600 mt-2">{{ report.description }}</p>
          </div>

          <!-- Metrics -->
          <div class="space-y-1 pt-2 border-t border-border-light">
            <div v-for="metric in report.metrics" :key="metric" class="text-xs text-neutral-500">
              <span class="inline-block w-1.5 h-1.5 rounded-full mr-2" :class="report.color === 'primary' ? 'bg-primary-300' : report.color === 'info' ? 'bg-info-300' : 'bg-success-300'" />
              {{ metric }}
            </div>
          </div>

          <!-- CTA -->
          <div class="pt-2">
            <button class="text-sm font-medium transition-colors" :class="report.color === 'primary' ? 'text-primary-600 hover:text-primary-700' : report.color === 'info' ? 'text-info-600 hover:text-info-700' : 'text-success-600 hover:text-success-700'">
              View Report →
            </button>
          </div>
        </div>
      </Card>
    </div>

    <!-- Info Section -->
    <Card class="bg-gradient-to-r from-primary-50 to-info-50 border border-primary-200">
      <div class="space-y-3">
        <h3 class="text-lg font-semibold text-neutral-900">📊 About Reports</h3>
        <div class="space-y-2 text-sm text-neutral-700">
          <p>
            <strong>Executive Summary:</strong> Get a quick overview of overall organizational performance, project status, and team capacity in one comprehensive dashboard.
          </p>
          <p>
            <strong>Project Performance:</strong> Deep-dive into specific project metrics, track progress against timelines, and identify risks early.
          </p>
          <p>
            <strong>Team Workload:</strong> Monitor individual and department-level capacity, identify overallocation issues, and optimize resource distribution.
          </p>
        </div>
        <p class="text-xs text-neutral-500 pt-2">💡 Tip: All reports are printable and can be exported for sharing with stakeholders.</p>
      </div>
    </Card>
  </div>
</template>
