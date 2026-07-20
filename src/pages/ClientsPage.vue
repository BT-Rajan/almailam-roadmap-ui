<script setup lang="ts">
import { LayoutGrid, Plus, TableProperties } from '@lucide/vue'
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import IconButton from '@/components/common/IconButton.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import ClientCard from '@/components/client/ClientCard.vue'
import {
  CLIENT_ONBOARDING_STATE_OPTIONS,
  CLIENT_STATUS_OPTIONS,
  CLIENT_TYPE_OPTIONS,
} from '@/constants/clientOptions'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { usePagination } from '@/composables/usePagination'
import { useClientStore } from '@/stores/clientStore'
import type { ClientOnboardingState, ClientStatus, ClientType } from '@/types/Client'
import type { SmartTableColumn } from '@/types/Table'
import type { SelectOption } from '@/types/Ui'
import { getClientDisplayName, getClientOnboardingStateVariant, getClientStatusVariant } from '@/utils/clientHelpers'

interface ClientTableRow {
  [key: string]: unknown
  id: string
  code: string
  name: string
  clientType: ClientType
  mobile: string
  email: string
  city: string
  status: ClientStatus
  onboardingState: ClientOnboardingState
}

const router = useRouter()
const clientStore = useClientStore()

const TYPE_OPTIONS: SelectOption[] = [{ label: 'All Types', value: 'All' }, ...CLIENT_TYPE_OPTIONS]

const TABLE_COLUMNS: SmartTableColumn<ClientTableRow>[] = [
  { key: 'code', label: 'Code', sortable: true, width: '110px' },
  { key: 'name', label: 'Name', sortable: true },
  { key: 'clientType', label: 'Type', sortable: true },
  { key: 'mobile', label: 'Mobile', sortable: true },
  { key: 'email', label: 'Email', sortable: true },
  { key: 'city', label: 'City', sortable: true },
  { key: 'onboardingState', label: 'Onboarding', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
]

const tableRows = computed<ClientTableRow[]>(() =>
  clientStore.filteredClients.map((client) => ({
    id: client.id,
    code: client.code,
    name: getClientDisplayName(client),
    clientType: client.clientType,
    mobile: client.mobile,
    email: client.email,
    city: client.city,
    status: client.status,
    onboardingState: client.onboardingState,
  })),
)

const { currentPage, pageSize, totalItems, totalPages, startIndex, endIndex, goToPage, setPageSize } = usePagination(
  () => clientStore.filteredClients.length,
  9,
)

const paginatedGridClients = computed(() => clientStore.filteredClients.slice(startIndex.value, endIndex.value))

function loadData(): void {
  clientStore.loadClients()
}

onMounted(() => {
  if (clientStore.clients.length === 0) loadData()
})

function openClient(clientId: string): void {
  router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId } })
}

function createClient(): void {
  router.push({ name: ROUTE_NAMES.CLIENT_NEW })
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader
      title="Clients"
      subtitle="Onboard, verify and reuse individual and organisation client profiles across every project."
    >
      <template #actions>
        <BaseButton :icon="Plus" @click="createClient">New Client</BaseButton>
      </template>
    </PageHeader>

    <FilterBar
      :search-value="clientStore.searchTerm"
      search-placeholder="Search by name, mobile or email"
      :has-active-filters="clientStore.hasActiveFilters"
      @update:search-value="clientStore.setSearchTerm"
      @clear="clientStore.clearFilters"
    >
      <template #filters>
        <div class="w-44">
          <SelectBox
            :model-value="clientStore.typeFilter"
            :options="TYPE_OPTIONS"
            @update:model-value="clientStore.setTypeFilter($event as ClientType | 'All')"
          />
        </div>
        <div class="w-44">
          <SelectBox
            :model-value="clientStore.statusFilter"
            :options="CLIENT_STATUS_OPTIONS"
            @update:model-value="clientStore.setStatusFilter($event as ClientStatus | 'All')"
          />
        </div>
        <div class="w-52">
          <SelectBox
            :model-value="clientStore.onboardingFilter"
            :options="CLIENT_ONBOARDING_STATE_OPTIONS"
            @update:model-value="clientStore.setOnboardingFilter($event as ClientOnboardingState | 'All')"
          />
        </div>
      </template>
      <template #actions>
        <div class="flex items-center gap-1 rounded-lg border border-border-default p-1">
          <IconButton
            :icon="LayoutGrid"
            label="Grid view"
            size="sm"
            :variant="clientStore.viewMode === 'grid' ? 'primary' : 'ghost'"
            @click="clientStore.setViewMode('grid')"
          />
          <IconButton
            :icon="TableProperties"
            label="Table view"
            size="sm"
            :variant="clientStore.viewMode === 'table' ? 'primary' : 'ghost'"
            @click="clientStore.setViewMode('table')"
          />
        </div>
      </template>
    </FilterBar>

    <ErrorState v-if="clientStore.error" :description="clientStore.error" @retry="loadData" />

    <template v-else-if="clientStore.viewMode === 'grid'">
      <div v-if="clientStore.isLoading" class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
        <div v-for="placeholder in 6" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="5" />
        </div>
      </div>

      <EmptyState
        v-else-if="paginatedGridClients.length === 0"
        title="No clients found"
        description="Try adjusting your search or filters, or onboard a new client."
        action-label="New Client"
        @action="createClient"
      />

      <template v-else>
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
          <ClientCard v-for="client in paginatedGridClients" :key="client.id" :client="client" @open="openClient" />
        </div>
        <div class="rounded-xl border border-border-light bg-bg-card">
          <TablePagination
            :current-page="currentPage"
            :total-pages="totalPages"
            :total-items="totalItems"
            :start-index="startIndex"
            :end-index="endIndex"
            :page-size="pageSize"
            :page-size-options="[9, 18, 27]"
            @page-change="goToPage"
            @page-size-change="setPageSize"
          />
        </div>
      </template>
    </template>

    <SmartTable
      v-else
      :columns="TABLE_COLUMNS"
      :rows="tableRows"
      row-key="id"
      :loading="clientStore.isLoading"
      :searchable="false"
      empty-title="No clients found"
      empty-description="Try adjusting your search or filters, or onboard a new client."
      @row-click="openClient($event.id)"
    >
      <template #cell-onboardingState="{ value }">
        <StatusBadge
          :label="value as string"
          :variant="getClientOnboardingStateVariant(value as ClientOnboardingState)"
        />
      </template>
      <template #cell-status="{ value }">
        <StatusBadge :label="value as string" :variant="getClientStatusVariant(value as ClientStatus)" show-dot />
      </template>
    </SmartTable>
  </div>
</template>
