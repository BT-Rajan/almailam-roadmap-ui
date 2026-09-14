<script setup lang="ts">
import { Plus, FileUp, Zap } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ROUTE_NAMES } from '@/constants/routeNames'
import QuickActionCard from '@/components/dashboard/QuickActionCard.vue'
import DashboardTabs from '@/components/dashboard/DashboardTabs.vue'
import type { DashboardTab, DashboardTabKey } from '@/components/dashboard/DashboardTabs.vue'
import DashboardClientsTab from '@/components/dashboard/DashboardClientsTab.vue'
import DashboardProjectsTab from '@/components/dashboard/DashboardProjectsTab.vue'
import DashboardDeadlinesTab from '@/components/dashboard/DashboardDeadlinesTab.vue'
import DashboardFinancialsTab from '@/components/dashboard/DashboardFinancialsTab.vue'

const router = useRouter()
const { t } = useI18n()

// Each tab panel below owns its own store loading, guarded so a store
// already populated (or already mid-fetch) is never fetched twice --
// see DashboardProjectsTab.vue etc. Combined with the v-if chain in the
// template (which fully unmounts the inactive panels rather than hiding
// them), only the active tab's widgets are ever mounted and reactive at
// once. That's the fix for "too many widgets refreshing": the old single-
// page dashboard fired projects + tasks + documents + clients + payment
// agreements/obligations (which itself cascades into project/client/
// quotation loads) all on first mount, every time. Now a visit that only
// ever opens the Projects tab, say, issues a fraction of those requests,
// and switching tabs re-triggers nothing for data that's already loaded.
const activeTab = ref<DashboardTabKey>('projects')

const TABS = computed<DashboardTab[]>(() => [
  { key: 'clients', label: t('dashboard.clientsTab') },
  { key: 'projects', label: t('dashboard.projectsTab') },
  { key: 'deadlines', label: t('dashboard.deadlinesTab') },
  { key: 'financials', label: t('dashboard.financialsTab') },
])

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
</script>

<template>
  <div class="space-y-8 pb-8">
    <!-- Page Header -->
    <div>
      <h1 class="font-display text-3xl font-semibold text-text-primary">
        <span class="text-gradient-accent">{{ t('dashboard.title') }}</span>
      </h1>
      <p class="text-text-muted mt-1">{{ t('dashboard.welcomeSubtitle') }}</p>
    </div>

    <!-- Quick Actions -->
    <div>
      <h2 class="text-lg font-semibold text-text-primary mb-4">{{ t('dashboard.quickActions') }}</h2>
      <div class="grid grid-cols-2 tablet:grid-cols-4 gap-4">
        <QuickActionCard :label="t('dashboard.newProject')" :icon="Plus" @click="handleQuickAction('new-project')" />
        <QuickActionCard :label="t('dashboard.newTask')" :icon="Plus" color="success" @click="handleQuickAction('new-task')" />
        <QuickActionCard :label="t('dashboard.uploadDocument')" :icon="FileUp" color="info" @click="handleQuickAction('upload-document')" />
        <QuickActionCard :label="t('dashboard.submitForm')" :icon="Zap" color="warning" @click="handleQuickAction('submit-form')" />
      </div>
    </div>

    <DashboardTabs :tabs="TABS" :active-tab="activeTab" @select="activeTab = $event" />

    <div v-if="activeTab === 'clients'" id="dashboard-tabpanel-clients" role="tabpanel" aria-labelledby="dashboard-tab-clients">
      <DashboardClientsTab />
    </div>
    <div v-else-if="activeTab === 'projects'" id="dashboard-tabpanel-projects" role="tabpanel" aria-labelledby="dashboard-tab-projects">
      <DashboardProjectsTab />
    </div>
    <div v-else-if="activeTab === 'deadlines'" id="dashboard-tabpanel-deadlines" role="tabpanel" aria-labelledby="dashboard-tab-deadlines">
      <DashboardDeadlinesTab />
    </div>
    <div v-else-if="activeTab === 'financials'" id="dashboard-tabpanel-financials" role="tabpanel" aria-labelledby="dashboard-tab-financials">
      <DashboardFinancialsTab />
    </div>
  </div>
</template>
