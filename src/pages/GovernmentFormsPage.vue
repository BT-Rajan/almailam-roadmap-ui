<script setup lang="ts">
import { LayoutGrid, TableProperties } from '@lucide/vue'
import { computed, onMounted } from 'vue'

import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import IconButton from '@/components/common/IconButton.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import GovernmentFormCard from '@/components/government/GovernmentFormCard.vue'
import { useGovernmentFormStore } from '@/stores/governmentFormStore'
import { useToastStore } from '@/stores/toastStore'
import type { SmartTableColumn } from '@/types/Table'
import type { GovernmentForm, GovernmentFormCategory } from '@/types/Government'
import type { SelectOption } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'
import { getFormCategoryVariant } from '@/utils/governmentFormHelpers'

interface GovernmentFormTableRow {
  [key: string]: unknown
  id: string
  formCode: string
  title: string
  authorityName: string
  category: GovernmentFormCategory
  language: string
  version: string
  lastUpdated: string
}

const governmentFormStore = useGovernmentFormStore()
const toastStore = useToastStore()

const CATEGORY_OPTIONS: SelectOption[] = [
  { label: 'All Categories', value: 'All' },
  { label: 'Building Permit', value: 'Building Permit' },
  { label: 'Occupancy Certificate', value: 'Occupancy Certificate' },
  { label: 'Fire Safety Approval', value: 'Fire Safety Approval' },
  { label: 'Utility Connection', value: 'Utility Connection' },
  { label: 'Environmental Clearance', value: 'Environmental Clearance' },
  { label: 'Business License', value: 'Business License' },
]

const authorityOptions = computed<SelectOption[]>(() => [
  { label: 'All Authorities', value: 'All' },
  ...governmentFormStore.authorities.map((authority) => ({ label: authority.name, value: authority.id })),
])

const TABLE_COLUMNS: SmartTableColumn<GovernmentFormTableRow>[] = [
  { key: 'formCode', label: 'Form Code', sortable: true, width: '130px' },
  { key: 'title', label: 'Form Title', sortable: true },
  { key: 'authorityName', label: 'Authority', sortable: true },
  { key: 'category', label: 'Category', sortable: true },
  { key: 'language', label: 'Language', sortable: true },
  { key: 'version', label: 'Version', sortable: true, width: '100px' },
  { key: 'lastUpdated', label: 'Last Updated', sortable: true, align: 'right' },
]

const tableRows = computed<GovernmentFormTableRow[]>(() =>
  governmentFormStore.filteredForms.map((form) => ({
    id: form.id,
    formCode: form.formCode,
    title: form.title,
    authorityName: governmentFormStore.getAuthorityById(form.authorityId)?.name ?? 'Unknown Authority',
    category: form.category,
    language: form.language,
    version: form.version,
    lastUpdated: form.lastUpdated,
  })),
)

function loadData(): void {
  governmentFormStore.loadForms()
}

onMounted(() => {
  if (governmentFormStore.forms.length === 0) loadData()
})

function handleAiHelp(form: GovernmentForm): void {
  const authorityName = governmentFormStore.getAuthorityById(form.authorityId)?.name ?? 'the relevant authority'
  toastStore.show(
    'info',
    'AI Guidance',
    `Ensure all Required Documents for "${form.title}" are certified copies before submitting to ${authorityName}.`,
  )
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader
      title="Government Forms Library"
      subtitle="Browse official submission forms grouped by authority and category."
    />

    <FilterBar
      :search-value="governmentFormStore.searchTerm"
      search-placeholder="Search by form title or code"
      :has-active-filters="governmentFormStore.hasActiveFilters"
      @update:search-value="governmentFormStore.setSearchTerm"
      @clear="governmentFormStore.clearFilters"
    >
      <template #filters>
        <div class="w-56">
          <SelectBox
            :model-value="governmentFormStore.authorityFilter"
            :options="authorityOptions"
            @update:model-value="governmentFormStore.setAuthorityFilter($event)"
          />
        </div>
        <div class="w-52">
          <SelectBox
            :model-value="governmentFormStore.categoryFilter"
            :options="CATEGORY_OPTIONS"
            @update:model-value="governmentFormStore.setCategoryFilter($event as GovernmentFormCategory | 'All')"
          />
        </div>
      </template>
      <template #actions>
        <div class="flex items-center gap-1 rounded-lg border border-border-default p-1">
          <IconButton
            :icon="LayoutGrid"
            label="Grid view"
            size="sm"
            :variant="governmentFormStore.viewMode === 'grid' ? 'primary' : 'ghost'"
            @click="governmentFormStore.setViewMode('grid')"
          />
          <IconButton
            :icon="TableProperties"
            label="Table view"
            size="sm"
            :variant="governmentFormStore.viewMode === 'table' ? 'primary' : 'ghost'"
            @click="governmentFormStore.setViewMode('table')"
          />
        </div>
      </template>
    </FilterBar>

    <ErrorState v-if="governmentFormStore.error" :description="governmentFormStore.error" @retry="loadData" />

    <template v-else-if="governmentFormStore.viewMode === 'grid'">
      <div v-if="governmentFormStore.isLoading" class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
        <div v-for="placeholder in 6" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="5" />
        </div>
      </div>

      <EmptyState
        v-else-if="governmentFormStore.groupedByAuthority.length === 0"
        title="No forms found"
        description="Try adjusting your search or filters."
      />

      <div v-else class="flex flex-col gap-8">
        <div v-for="group in governmentFormStore.groupedByAuthority" :key="group.authority.id" class="flex flex-col gap-3">
          <div class="flex items-center gap-2">
            <h2 class="text-sm font-semibold text-neutral-700">{{ group.authority.name }}</h2>
            <StatusBadge :label="group.authority.category" variant="neutral" size="sm" />
          </div>
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
            <GovernmentFormCard
              v-for="form in group.forms"
              :key="form.id"
              :form="form"
              :authority="group.authority"
              @ai-help="handleAiHelp"
            />
          </div>
        </div>
      </div>
    </template>

    <SmartTable
      v-else
      :columns="TABLE_COLUMNS"
      :rows="tableRows"
      row-key="id"
      :loading="governmentFormStore.isLoading"
      :searchable="false"
      empty-title="No forms found"
      empty-description="Try adjusting your search or filters."
    >
      <template #cell-category="{ value }">
        <StatusBadge :label="value as string" :variant="getFormCategoryVariant(value as GovernmentFormCategory)" />
      </template>
      <template #cell-lastUpdated="{ value }">
        {{ formatDate(value as string) }}
      </template>
    </SmartTable>
  </div>
</template>
