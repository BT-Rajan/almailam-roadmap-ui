<script setup lang="ts">
import { Plus, FileUp, Zap } from '@lucide/vue'
import { useRouter } from 'vue-router'
import { ROUTE_NAMES } from '@/constants/routeNames'
import KPIWidget from '@/components/dashboard/KPIWidget.vue'
import StatisticsCard from '@/components/dashboard/StatisticsCard.vue'
import QuickActionCard from '@/components/dashboard/QuickActionCard.vue'
import ProjectSummaryCard from '@/components/dashboard/ProjectSummaryCard.vue'
import ActivityWidget from '@/components/dashboard/ActivityWidget.vue'
import PendingTasksWidget from '@/components/dashboard/PendingTasksWidget.vue'
import UpcomingDeadlinesWidget from '@/components/dashboard/UpcomingDeadlinesWidget.vue'
import RecentDocumentsWidget from '@/components/dashboard/RecentDocumentsWidget.vue'
import AIInsightWidget from '@/components/dashboard/AIInsightWidget.vue'
import type { KPI, StatisticItem, ProjectSummary, Task, Activity, Deadline, DocumentItem, AIInsight } from '@/types/Dashboard'

const router = useRouter()

// Mock data
const kpis: KPI[] = [
  {
    id: '1',
    label: 'Total Projects',
    value: 5,
    trend: { direction: 'up', percentage: 15, period: 'vs last month' },
  },
  {
    id: '2',
    label: 'Active Submissions',
    value: 3,
    trend: { direction: 'stable', percentage: 0, period: 'vs last month' },
  },
  {
    id: '3',
    label: 'Documents',
    value: 47,
    trend: { direction: 'up', percentage: 23, period: 'vs last month' },
  },
  {
    id: '4',
    label: 'Team Members',
    value: 3,
    trend: { direction: 'up', percentage: 8, period: 'vs last month' },
  },
]

const statistics: StatisticItem[] = [
  {
    id: '1',
    label: 'On Time',
    value: '92%',
    icon: '✓',
    color: 'success',
  },
  {
    id: '2',
    label: 'Pending Review',
    value: 2,
    icon: '⏱',
    color: 'warning',
  },
  {
    id: '3',
    label: 'Completed This Month',
    value: 1,
    icon: '📊',
    color: 'info',
  },
]

const projects: ProjectSummary[] = [
  {
    id: 'PRJ-2026-001',
    name: 'Al Reem Residential Tower',
    client: 'Al Reem Real Estate Development',
    status: 'active',
    progress: 8,
    dueDate: '2026-12-18',
  },
  {
    id: 'PRJ-2026-002',
    name: 'Falcon Heights Warehouse Expansion',
    client: 'Falcon Heights Contracting LLC',
    status: 'active',
    progress: 18,
    dueDate: '2026-11-30',
  },
  {
    id: 'PRJ-2026-003',
    name: 'Marina Bay Hotel Renovation',
    client: 'Marina Bay Hospitality Group',
    status: 'active',
    progress: 42,
    dueDate: '2026-10-05',
  },
  {
    id: 'PRJ-2026-004',
    name: 'Sharjah Industrial Facility',
    client: 'Sharjah Industrial Holdings',
    status: 'pending',
    progress: 68,
    dueDate: '2026-08-15',
  },
]

const tasks: Task[] = [
  {
    id: '1',
    title: 'Review soil investigation report',
    project: 'Al Reem Residential Tower',
    priority: 'high',
    assignee: 'Layla Haddad',
    dueDate: '2026-07-24',
    status: 'in-progress',
  },
  {
    id: '2',
    title: 'Prepare civil defence submission',
    project: 'Sharjah Industrial Facility',
    priority: 'urgent',
    assignee: 'Mohammed Iqbal',
    dueDate: '2026-07-22',
    status: 'review',
  },
  {
    id: '3',
    title: 'Update project timeline',
    project: 'Marina Bay Hotel Renovation',
    priority: 'medium',
    assignee: 'Layla Haddad',
    dueDate: '2026-07-28',
    status: 'todo',
  },
  {
    id: '4',
    title: 'Client presentation materials',
    project: 'Falcon Heights Warehouse Expansion',
    priority: 'medium',
    assignee: 'You',
    dueDate: '2026-07-25',
    status: 'todo',
  },
]

const activities: Activity[] = [
  {
    id: '1',
    type: 'project',
    title: 'Al Reem Residential Tower updated',
    description: 'Project status changed to active',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    user: 'Layla Haddad',
    icon: '📁',
  },
  {
    id: '2',
    type: 'document',
    title: 'New document uploaded',
    description: 'Soil Investigation Report added to Al Reem Residential Tower',
    timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    user: 'Layla Haddad',
    icon: '📄',
  },
  {
    id: '3',
    type: 'submission',
    title: 'Government submission approved',
    description: 'Fire Suppression System Report approved by Fire Department',
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    user: 'Fire Department',
    icon: '✓',
  },
  {
    id: '4',
    type: 'ai',
    title: 'AI analysis completed',
    description: 'Document review for Sharjah Industrial Facility ready',
    timestamp: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
    user: 'Claude AI',
    icon: '🤖',
  },
  {
    id: '5',
    type: 'task',
    title: 'Task assigned to you',
    description: 'Review client presentation materials',
    timestamp: new Date(Date.now() - 72 * 60 * 60 * 1000).toISOString(),
    user: 'Mohammed Iqbal',
    icon: '✋',
  },
]

const deadlines: Deadline[] = [
  {
    id: '1',
    title: 'Falcon Heights - Quotation Follow-up',
    project: 'Falcon Heights Warehouse Expansion',
    dueDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
    priority: 'high',
    type: 'submission',
  },
  {
    id: '2',
    title: 'Sharjah Industrial - Final Approval',
    project: 'Sharjah Industrial Facility',
    dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    priority: 'medium',
    type: 'approval',
  },
  {
    id: '3',
    title: 'Marina Bay Hotel - Progress Report Due',
    project: 'Marina Bay Hotel Renovation',
    dueDate: new Date(Date.now() + 12 * 24 * 60 * 60 * 1000).toISOString(),
    priority: 'medium',
    type: 'delivery',
  },
]

const documents: DocumentItem[] = [
  {
    id: '1',
    name: 'Soil Investigation Report',
    project: 'Al Reem Residential Tower',
    type: 'PDF',
    uploadedAt: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    uploadedBy: 'Layla Haddad',
    size: '2.8 MB',
  },
  {
    id: '2',
    name: 'MEP Design Services Agreement',
    project: 'Falcon Heights Warehouse Expansion',
    type: 'PDF',
    uploadedAt: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
    uploadedBy: 'Ahmed Rashid',
    size: '1.1 MB',
  },
  {
    id: '3',
    name: 'HVAC Load Calculation Sheet',
    project: 'Marina Bay Hotel Renovation',
    type: 'DOCX',
    uploadedAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    uploadedBy: 'Mohammed Iqbal',
    size: '890 KB',
  },
  {
    id: '4',
    name: 'Fire Safety Municipality Submission Form',
    project: 'Sharjah Industrial Facility',
    type: 'PDF',
    uploadedAt: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
    uploadedBy: 'Mohammed Iqbal',
    size: '1.4 MB',
  },
  {
    id: '5',
    name: 'Budget Report - Monthly',
    project: 'All Projects',
    type: 'XLSX',
    uploadedAt: new Date(Date.now() - 72 * 60 * 60 * 1000).toISOString(),
    uploadedBy: 'Finance Team',
    size: '568 KB',
  },
]

const insights: AIInsight[] = [
  {
    id: '1',
    title: 'Schedule Risk Detected',
    description: 'Falcon Heights Warehouse Expansion project may face 3-4 week delay based on current submission timelines.',
    confidence: 'high',
    action: 'View Analysis',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: '2',
    title: 'Document Compliance Alert',
    description: 'Sharjah Industrial Facility documents require additional certifications per latest authority guidelines.',
    confidence: 'high',
    action: 'View Details',
    timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: '3',
    title: 'Resource Optimization Opportunity',
    description: 'Team member availability suggests opportunity to accelerate Marina Bay Hotel Renovation deliverables.',
    confidence: 'medium',
    action: 'Explore',
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
  },
]

const handleQuickAction = (action: string) => {
  switch (action) {
    case 'new-project':
      router.push({ name: ROUTE_NAMES.PROJECT_NEW })
      break
    case 'new-task':
      router.push({ name: ROUTE_NAMES.TASKS })
      break
    case 'upload-document':
      router.push({ name: ROUTE_NAMES.DOCUMENTS })
      break
    case 'submit-form':
      router.push({ name: ROUTE_NAMES.GOVERNMENT_SUBMISSIONS })
      break
  }
}

const handleProjectClick = (projectId: string) => {
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId } })
}

const handleTaskClick = () => {
  router.push({ name: ROUTE_NAMES.MY_TASKS })
}
</script>

<template>
  <div class="space-y-8 pb-8">
    <!-- Page Header -->
    <div>
      <h1 class="text-3xl font-bold text-neutral-900">Executive Dashboard</h1>
      <p class="text-neutral-500 mt-1">Welcome back. Here's your project overview.</p>
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-4 gap-4">
      <KPIWidget v-for="kpi in kpis" :key="kpi.id" :kpi="kpi" />
    </div>

    <!-- Statistics Row -->
    <div class="grid grid-cols-1 tablet:grid-cols-3 gap-4">
      <StatisticsCard v-for="stat in statistics" :key="stat.id" :statistic="stat" />
    </div>

    <!-- Quick Actions -->
    <div>
      <h2 class="text-lg font-semibold text-neutral-900 mb-4">Quick Actions</h2>
      <div class="grid grid-cols-2 tablet:grid-cols-4 gap-4">
        <QuickActionCard label="New Project" :icon="Plus" @click="handleQuickAction('new-project')" />
        <QuickActionCard label="New Task" :icon="Plus" color="success" @click="handleQuickAction('new-task')" />
        <QuickActionCard label="Upload Document" :icon="FileUp" color="info" @click="handleQuickAction('upload-document')" />
        <QuickActionCard label="Submit Form" :icon="Zap" color="warning" @click="handleQuickAction('submit-form')" />
      </div>
    </div>

    <!-- Projects Grid -->
    <div>
      <h2 class="text-lg font-semibold text-neutral-900 mb-4">Recent Projects</h2>
      <div class="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-4 gap-4">
        <ProjectSummaryCard v-for="project in projects" :key="project.id" :project="project" @click="handleProjectClick(project.id)" />
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 laptop:grid-cols-3 gap-6">
      <!-- Left Column: Activity and Tasks -->
      <div class="laptop:col-span-2 space-y-6">
        <ActivityWidget :activities="activities" />
        <PendingTasksWidget :tasks="tasks" @task-click="handleTaskClick" />
      </div>

      <!-- Right Column: Deadlines, Documents, and AI -->
      <div class="space-y-6">
        <UpcomingDeadlinesWidget :deadlines="deadlines" />
        <RecentDocumentsWidget :documents="documents" />
        <AIInsightWidget :insights="insights" />
      </div>
    </div>
  </div>
</template>
