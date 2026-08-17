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
  accountManager: string
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
  { key: 'accountManager', label: 'Account Manager', sortable: false },
  { key: 'onboardingState', label: 'Onboarding', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
]

const tableRows = computed<ClientTableRow[]>(() =>
  clientStore.pageItems.map((client) => ({
    id: client.id,
    code: client.code,
    name: getClientDisplayName(client),
    clientType: client.clientType,
    mobile: client.mobile,
    email: client.email,
    city: client.city,
    status: client.status,
    onboardingState: client.onboardingState,
    accountManager: client.accountManagerName ?? '—',
  })),
)

function loadData(): void {
  void clientStore.loadClientsPage()
}

onMounted(loadData)

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
      @search="clientStore.applySearch"
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
        <BaseButton
          size="sm"
          :variant="clientStore.myClientsOnly ? 'primary' : 'secondary'"
          @click="clientStore.setMyClientsOnly(!clientStore.myClientsOnly)"
        >
          My Clients
        </BaseButton>
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
      <div v-if="clientStore.isPageLoading" class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
        <div v-for="placeholder in 6" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="5" />
        </div>
      </div>

      <EmptyState
        v-else-if="clientStore.pageItems.length === 0"
        :title="clientStore.myClientsOnly ? 'No clients assigned to you yet' : 'No clients found'"
        :description="
          clientStore.myClientsOnly
            ? 'You have no clients assigned as their account manager. Turn off \'My Clients\' to see everyone, or assign yourself via Edit Client.'
            : 'Try adjusting your search or filters, or onboard a new client.'
        "
        action-label="New Client"
        @action="createClient"
      />

      <template v-else>
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
          <ClientCard v-for="client in clientStore.pageItems" :key="client.id" :client="client" @open="openClient" />
        </div>
        <div class="rounded-xl border border-border-light bg-bg-card">
          <TablePagination
            :current-page="clientStore.pagination.page"
            :total-pages="clientStore.pagination.totalPages"
            :total-items="clientStore.pagination.total"
            :start-index="(clientStore.pagination.page - 1) * clientStore.pagination.pageSize"
            :end-index="Math.min(clientStore.pagination.page * clientStore.pagination.pageSize, clientStore.pagination.total)"
            :page-size="clientStore.pagination.pageSize"
            :page-size-options="[9, 18, 27]"
            @page-change="clientStore.setPage"
            @page-size-change="clientStore.setPageSize"
          />
        </div>
      </template>
    </template>

    <template v-else>
      <SmartTable
        :columns="TABLE_COLUMNS"
        :rows="tableRows"
        row-key="id"
        :loading="clientStore.isPageLoading"
        :searchable="false"
        :paginated="false"
        :empty-title="clientStore.myClientsOnly ? 'No clients assigned to you yet' : 'No clients found'"
        :empty-description="
          clientStore.myClientsOnly
            ? 'You have no clients assigned as their account manager. Turn off \'My Clients\' to see everyone.'
            : 'Try adjusting your search or filters, or onboard a new client.'
        "
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
      <div class="rounded-xl border border-border-light bg-bg-card">
        <TablePagination
          :current-page="clientStore.pagination.page"
          :total-pages="clientStore.pagination.totalPages"
          :total-items="clientStore.pagination.total"
          :start-index="(clientStore.pagination.page - 1) * clientStore.pagination.pageSize"
          :end-index="Math.min(clientStore.pagination.page * clientStore.pagination.pageSize, clientStore.pagination.total)"
          :page-size="clientStore.pagination.pageSize"
          :page-size-options="[10, 25, 50]"
          @page-change="clientStore.setPage"
          @page-size-change="clientStore.setPageSize"
        />
      </div>
    </template>
  </div>
</template>
