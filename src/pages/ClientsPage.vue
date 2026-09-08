<script setup lang="ts">
import { LayoutGrid, Plus, RotateCcw, TableProperties, Trash2 } from '@lucide/vue'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
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
import { CLIENT_STATUS_OPTIONS, CLIENT_TYPE_OPTIONS } from '@/constants/clientOptions'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useClientStore } from '@/stores/clientStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import { useToastStore } from '@/stores/toastStore'
import type { ClientStatus, ClientType } from '@/types/Client'
import type { SmartTableColumn } from '@/types/Table'
import type { SelectOption } from '@/types/Ui'
import { getClientDisplayName, getClientStatusVariant } from '@/utils/clientHelpers'

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
  accountManager: string
}

const router = useRouter()
const clientStore = useClientStore()
const resultDialogStore = useResultDialogStore()
const toastStore = useToastStore()
const { t } = useI18n()

const TYPE_OPTIONS = computed<SelectOption[]>(() => [{ label: t('client.clientsPage.allTypes'), value: 'All' }, ...CLIENT_TYPE_OPTIONS])

const TABLE_COLUMNS = computed<SmartTableColumn<ClientTableRow>[]>(() => [
  { key: 'code', label: t('client.clientsPage.columns.code'), sortable: true, width: '110px' },
  { key: 'name', label: t('client.clientsPage.columns.name'), sortable: true },
  { key: 'clientType', label: t('client.clientsPage.columns.type'), sortable: true },
  { key: 'mobile', label: t('client.clientsPage.columns.mobile'), sortable: true },
  { key: 'email', label: t('client.clientsPage.columns.email'), sortable: true },
  { key: 'city', label: t('client.clientsPage.columns.city'), sortable: true },
  { key: 'accountManager', label: t('client.clientsPage.columns.accountManager'), sortable: false },
  { key: 'status', label: t('client.clientsPage.columns.status'), sortable: true },
])

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
    accountManager: client.accountManagerName ?? '—',
  })),
)

function loadData(): void {
  void clientStore.loadClientsPage()
}

onMounted(loadData)

function openClient(clientId: string): void {
  if (clientStore.showDeleted) return
  router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId } })
}

function createClient(): void {
  router.push({ name: ROUTE_NAMES.CLIENT_NEW })
}

function toggleShowDeleted(): void {
  clientStore.setShowDeleted(!clientStore.showDeleted)
}

async function restoreClient(clientId: string, name: string): Promise<void> {
  try {
    await clientStore.restoreClient(clientId)
    toastStore.show('success', t('client.clientsPage.restoredTitle'), t('client.clientsPage.restoredDescription', { name }))
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    resultDialogStore.showError(t('client.clientsPage.failedToRestore'), detail)
  }
}

const CLIENT_TYPE_LABEL_KEYS: Record<string, string> = {
  Individual: 'clientOptions.type.individual',
  Company: 'clientOptions.type.company',
  Organisation: 'clientOptions.type.organisation',
  'Government Entity': 'clientOptions.type.governmentEntity',
  Other: 'clientOptions.type.other',
}
function clientTypeLabel(clientType: string): string {
  return t(CLIENT_TYPE_LABEL_KEYS[clientType] ?? clientType)
}

const CLIENT_STATUS_LABEL_KEYS: Record<string, string> = {
  Active: 'clientOptions.status.active',
  Inactive: 'clientOptions.status.inactive',
}
function clientStatusLabel(status: string): string {
  return t(CLIENT_STATUS_LABEL_KEYS[status] ?? status)
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader
      :title="t('client.clientsPage.title')"
      :subtitle="t('client.clientsPage.subtitle')"
    >
      <template #actions>
        <BaseButton
          variant="secondary"
          :icon="clientStore.showDeleted ? undefined : Trash2"
          @click="toggleShowDeleted"
        >
          {{ clientStore.showDeleted ? t('client.clientsPage.backToClients') : t('client.clientsPage.deletedClients') }}
        </BaseButton>
        <BaseButton :icon="Plus" @click="createClient">{{ t('client.clientsPage.newClient') }}</BaseButton>
      </template>
    </PageHeader>

    <FilterBar
      :show-search="false"
      :has-active-filters="clientStore.hasActiveFilters"
      @clear="clientStore.clearFilters"
    >
      <template #filters>
        <div class="w-44">
          <SelectBox
            :label="t('client.clientsPage.clientType')"
            :model-value="clientStore.typeFilter"
            :options="TYPE_OPTIONS"
            @update:model-value="clientStore.setTypeFilter($event as ClientType | 'All')"
          />
        </div>
        <div class="w-44">
          <SelectBox
            :label="t('client.clientsPage.status')"
            :model-value="clientStore.statusFilter"
            :options="CLIENT_STATUS_OPTIONS"
            @update:model-value="clientStore.setStatusFilter($event as ClientStatus | 'All')"
          />
        </div>
        <BaseButton
          size="sm"
          :variant="clientStore.myClientsOnly ? 'primary' : 'secondary'"
          :aria-pressed="clientStore.myClientsOnly"
          @click="clientStore.setMyClientsOnly(!clientStore.myClientsOnly)"
        >
          {{ t('client.clientsPage.myClients') }}
        </BaseButton>
      </template>
      <template #actions>
        <div class="flex items-center gap-1 rounded-lg border border-border-default p-1" role="group" :aria-label="t('client.clientsPage.layoutAria')">
          <IconButton
            :icon="LayoutGrid"
            :label="t('client.clientsPage.gridView')"
            size="sm"
            :variant="clientStore.viewMode === 'grid' ? 'primary' : 'ghost'"
            :aria-pressed="clientStore.viewMode === 'grid'"
            @click="clientStore.setViewMode('grid')"
          />
          <IconButton
            :icon="TableProperties"
            :label="t('client.clientsPage.tableView')"
            size="sm"
            :variant="clientStore.viewMode === 'table' ? 'primary' : 'ghost'"
            :aria-pressed="clientStore.viewMode === 'table'"
            @click="clientStore.setViewMode('table')"
          />
        </div>
      </template>
    </FilterBar>

    <ErrorState v-if="clientStore.error" :description="clientStore.error" @retry="loadData" />

    <template v-else-if="clientStore.showDeleted">
      <div v-if="clientStore.isPageLoading" class="flex flex-col gap-3">
        <div v-for="placeholder in 4" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="2" />
        </div>
      </div>

      <EmptyState
        v-else-if="clientStore.pageItems.length === 0"
        :title="t('client.clientsPage.noDeletedClientsTitle')"
        :description="t('client.clientsPage.noDeletedClientsDescription')"
      />

      <template v-else>
        <div class="flex flex-col gap-3">
          <div
            v-for="client in clientStore.pageItems"
            :key="client.id"
            class="flex flex-col gap-2 rounded-xl border border-border-light bg-bg-card p-4 tablet:flex-row tablet:items-center tablet:justify-between"
          >
            <div class="flex flex-col gap-0.5">
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ client.code }} · {{ clientTypeLabel(client.clientType) }}</p>
              <p class="text-sm font-semibold text-text-primary">{{ getClientDisplayName(client) }}</p>
              <p class="text-xs text-text-muted">{{ client.email }} · {{ client.mobile }}</p>
            </div>
            <BaseButton size="sm" :icon="RotateCcw" @click="restoreClient(client.id, getClientDisplayName(client))">
              {{ t('client.clientsPage.restore') }}
            </BaseButton>
          </div>
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

    <template v-else-if="clientStore.viewMode === 'grid'">
      <div v-if="clientStore.isPageLoading" class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
        <div v-for="placeholder in 6" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="5" />
        </div>
      </div>

      <EmptyState
        v-else-if="clientStore.pageItems.length === 0"
        :title="clientStore.myClientsOnly ? t('client.clientsPage.noClientsAssignedTitle') : t('client.clientsPage.noClientsFoundTitle')"
        :description="
          clientStore.myClientsOnly
            ? t('client.clientsPage.noClientsAssignedDescription')
            : t('client.clientsPage.noClientsFoundDescription')
        "
        :action-label="t('client.clientsPage.newClient')"
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
        :empty-title="clientStore.myClientsOnly ? t('client.clientsPage.noClientsAssignedTitle') : t('client.clientsPage.noClientsFoundTitle')"
        :empty-description="
          clientStore.myClientsOnly
            ? t('client.clientsPage.noClientsAssignedDescriptionTable')
            : t('client.clientsPage.noClientsFoundDescription')
        "
        @row-click="openClient($event.id)"
      >
        <template #cell-clientType="{ value }">
          {{ clientTypeLabel(value as string) }}
        </template>
        <template #cell-status="{ value }">
          <StatusBadge :label="clientStatusLabel(value as string)" :variant="getClientStatusVariant(value as ClientStatus)" show-dot />
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
