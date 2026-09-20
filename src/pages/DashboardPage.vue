<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRbac } from '@/composables/useRbac'
import DashboardTabs from '@/components/dashboard/DashboardTabs.vue'
import type { DashboardTab, DashboardTabKey } from '@/components/dashboard/DashboardTabs.vue'
import DashboardClientsTab from '@/components/dashboard/DashboardClientsTab.vue'
import DashboardProjectsTab from '@/components/dashboard/DashboardProjectsTab.vue'
import DashboardDeadlinesTab from '@/components/dashboard/DashboardDeadlinesTab.vue'
import DashboardFinancialsTab from '@/components/dashboard/DashboardFinancialsTab.vue'

const { t } = useI18n()
const { can } = useRbac()

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

// Financials shows real company-wide revenue/collection figures, not
// just this user's own projects -- restricted to Administrator (see
// useRbac.ts's 'dashboard.financials' permission), same as the rest of
// the app already restricts financial visibility (payments.view etc).
const TABS = computed<DashboardTab[]>(() => [
  { key: 'clients', label: t('dashboard.clientsTab') },
  { key: 'projects', label: t('dashboard.projectsTab') },
  { key: 'deadlines', label: t('dashboard.deadlinesTab') },
  ...(can('dashboard.financials') ? [{ key: 'financials' as const, label: t('dashboard.financialsTab') }] : []),
])
</script>

<template>
  <div class="flex flex-col gap-6 pb-8">
    <!-- Page Header -->
    <div>
      <h1 class="font-display text-3xl font-semibold text-text-primary">
        <span class="text-gradient-accent">{{ t('dashboard.title') }}</span>
      </h1>
      <p class="text-text-muted mt-1">{{ t('dashboard.welcomeSubtitle') }}</p>
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
    <div v-else-if="activeTab === 'financials' && can('dashboard.financials')" id="dashboard-tabpanel-financials" role="tabpanel" aria-labelledby="dashboard-tab-financials">
      <DashboardFinancialsTab />
    </div>
  </div>
</template>
