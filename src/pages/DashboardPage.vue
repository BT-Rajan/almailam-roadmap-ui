<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRbac } from '@/composables/useRbac'
import { useAuthStore } from '@/stores/authStore'
import DashboardTabs from '@/components/dashboard/DashboardTabs.vue'
import type { DashboardTab, DashboardTabKey } from '@/components/dashboard/DashboardTabs.vue'
import DashboardClientsTab from '@/components/dashboard/DashboardClientsTab.vue'
import DashboardProjectsTab from '@/components/dashboard/DashboardProjectsTab.vue'
import DashboardDeadlinesTab from '@/components/dashboard/DashboardDeadlinesTab.vue'
import DashboardFinancialsTab from '@/components/dashboard/DashboardFinancialsTab.vue'

const { t } = useI18n()
const { can } = useRbac()
const authStore = useAuthStore()

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

// Browser-local time of day is fine for a greeting (unlike the
// Kuwait-anchored "today" business logic elsewhere in the app -- see
// serverTimeStore.ts -- this has no financial/reporting consequence,
// it's purely which of three friendly phrases to show).
const greetingKey = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'dashboard.greetingMorning'
  if (hour < 18) return 'dashboard.greetingAfternoon'
  return 'dashboard.greetingEvening'
})

const firstName = computed(() => authStore.user?.name.split(' ')[0] ?? '')
// Pre-formatted so the "Good morning{name}" string works whether or not
// a name is available yet (before the user profile has loaded) without
// a locale needing two near-duplicate variants or risking an awkward
// trailing ", " with nothing after it.
const greetingName = computed(() => (firstName.value ? `, ${firstName.value}` : ''))
const avatarInitial = computed(() => authStore.user?.name.trim().charAt(0).toUpperCase() ?? '')
</script>

<template>
  <div class="flex flex-col gap-6 pb-8">
    <!-- Hero -->
    <div class="gradient-luxe-accent relative overflow-hidden rounded-3xl px-6 py-7 sm:px-8 sm:py-9">
      <div class="pointer-events-none absolute -right-8 -top-16 h-48 w-48 rounded-full bg-white/10 blur-2xl" />
      <div class="pointer-events-none absolute -bottom-20 -left-10 h-56 w-56 rounded-full bg-black/10 blur-3xl" />
      <div class="relative flex items-center justify-between gap-4">
        <div class="flex flex-col gap-1">
          <p class="text-sm font-medium text-white/75">{{ t(greetingKey, { name: greetingName }) }}</p>
          <h1 class="font-display text-3xl font-semibold text-white">{{ t('dashboard.title') }}</h1>
          <p class="text-sm text-white/80">{{ t('dashboard.welcomeSubtitle') }}</p>
        </div>
        <span
          v-if="avatarInitial"
          class="hidden h-14 w-14 shrink-0 items-center justify-center rounded-full bg-white/15 text-xl font-semibold text-white ring-1 ring-inset ring-white/30 backdrop-blur-sm sm:flex"
        >
          {{ avatarInitial }}
        </span>
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
    <div v-else-if="activeTab === 'financials' && can('dashboard.financials')" id="dashboard-tabpanel-financials" role="tabpanel" aria-labelledby="dashboard-tab-financials">
      <DashboardFinancialsTab />
    </div>
  </div>
</template>
