<script setup lang="ts">
import { ArrowLeft, Landmark, LayoutGrid, Pencil, Plus, TableProperties, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import IconButton from '@/components/common/IconButton.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import GovernmentAuthorityFormDialog from '@/components/administration/GovernmentAuthorityFormDialog.vue'
import GovernmentFormFormDialog from '@/components/administration/GovernmentFormFormDialog.vue'
import AuthorityCard from '@/components/government/AuthorityCard.vue'
import GovernmentFormCard from '@/components/government/GovernmentFormCard.vue'
import type { AuthorityInput, FormInput } from '@/services/governmentFormService'
import { useGovernmentFormStore } from '@/stores/governmentFormStore'
import { useToastStore } from '@/stores/toastStore'
import type { GovernmentAuthority, GovernmentForm, GovernmentFormCategory } from '@/types/Government'
import type { SmartTableColumn } from '@/types/Table'
import type { SelectOption } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'
import { getFormCategoryVariant } from '@/utils/governmentFormHelpers'

interface GovernmentFormTableRow {
  [key: string]: unknown
  id: string
  formCode: string
  title: string
  category: GovernmentFormCategory
  language: string
  version: string
  lastUpdated: string
}

const store = useGovernmentFormStore()
const toastStore = useToastStore()

const selectedAuthorityId = ref<string | undefined>(undefined)
const authoritySearchTerm = ref('')

const isAuthorityDialogOpen = ref(false)
const editingAuthority = ref<GovernmentAuthority | undefined>(undefined)
const isSavingAuthority = ref(false)

const isFormDialogOpen = ref(false)
const editingForm = ref<GovernmentForm | undefined>(undefined)
const isSavingForm = ref(false)

const deleteTarget = ref<{ type: 'authority' | 'form'; id: string; label: string } | undefined>(undefined)
const isDeleting = ref(false)

const CATEGORY_OPTIONS: SelectOption[] = [
  { label: 'All Categories', value: 'All' },
  { label: 'Building Permit', value: 'Building Permit' },
  { label: 'Occupancy Certificate', value: 'Occupancy Certificate' },
  { label: 'Fire Safety Approval', value: 'Fire Safety Approval' },
  { label: 'Utility Connection', value: 'Utility Connection' },
  { label: 'Environmental Clearance', value: 'Environmental Clearance' },
  { label: 'Business License', value: 'Business License' },
]

const TABLE_COLUMNS: SmartTableColumn<GovernmentFormTableRow>[] = [
  { key: 'formCode', label: 'Form Code', sortable: true, width: '130px' },
  { key: 'title', label: 'Form Title', sortable: true },
  { key: 'category', label: 'Category', sortable: true },
  { key: 'language', label: 'Language', sortable: true },
  { key: 'version', label: 'Version', sortable: true, width: '100px' },
  { key: 'lastUpdated', label: 'Last Updated', sortable: true, align: 'right' },
]

const selectedAuthority = computed(() =>
  store.authorities.find((authority) => authority.id === selectedAuthorityId.value),
)

const authorityFormCounts = computed<Record<string, number>>(() => {
  const counts: Record<string, number> = {}
  store.forms.forEach((form) => {
    counts[form.authorityId] = (counts[form.authorityId] ?? 0) + 1
  })
  return counts
})

const visibleAuthorities = computed<GovernmentAuthority[]>(() => {
  const term = authoritySearchTerm.value.trim().toLowerCase()
  if (term.length === 0) return store.authorities
  return store.authorities.filter(
    (authority) =>
      authority.name.toLowerCase().includes(term) || authority.category.toLowerCase().includes(term),
  )
})

const authorityForms = computed<GovernmentForm[]>(() => {
  if (!selectedAuthorityId.value) return []

  const term = store.searchTerm.trim().toLowerCase()

  return store.forms.filter((form) => {
    const matchesAuthority = form.authorityId === selectedAuthorityId.value
    const matchesSearch =
      term.length === 0 || form.title.toLowerCase().includes(term) || form.formCode.toLowerCase().includes(term)
    const matchesCategory = store.categoryFilter === 'All' || form.category === store.categoryFilter
    return matchesAuthority && matchesSearch && matchesCategory
  })
})

const authorityFormTableRows = computed<GovernmentFormTableRow[]>(() =>
  authorityForms.value.map((form) => ({
    id: form.id,
    formCode: form.formCode,
    title: form.title,
    category: form.category,
    language: form.language,
    version: form.version,
    lastUpdated: form.lastUpdated,
  })),
)

// Ensures the "Add Form" dialog defaults to the authority currently being viewed.
const dialogAuthorities = computed<GovernmentAuthority[]>(() => {
  if (!selectedAuthority.value) return store.authorities
  return [selectedAuthority.value, ...store.authorities.filter((a) => a.id !== selectedAuthority.value?.id)]
})

function loadData(): void {
  store.loadForms()
}

onMounted(() => {
  if (store.forms.length === 0) loadData()
})

function openAuthority(authority: GovernmentAuthority): void {
  selectedAuthorityId.value = authority.id
  store.clearFilters()
}

function backToAuthorities(): void {
  selectedAuthorityId.value = undefined
  store.clearFilters()
}

function openAddAuthority(): void {
  editingAuthority.value = undefined
  isAuthorityDialogOpen.value = true
}

function openEditAuthority(authority: GovernmentAuthority): void {
  editingAuthority.value = authority
  isAuthorityDialogOpen.value = true
}

async function saveAuthority(input: AuthorityInput): Promise<void> {
  isSavingAuthority.value = true
  try {
    if (editingAuthority.value) {
      await store.updateAuthority(editingAuthority.value.id, input)
      toastStore.show('success', 'Authority updated', `${input.name} has been saved.`)
    } else {
      await store.createAuthority(input)
      toastStore.show('success', 'Authority added', `${input.name} is now available for forms.`)
    }
    isAuthorityDialogOpen.value = false
  } catch {
    toastStore.show('error', 'Unable to save authority', 'Please try again.')
  } finally {
    isSavingAuthority.value = false
  }
}

function openAddForm(): void {
  editingForm.value = undefined
  isFormDialogOpen.value = true
}

function openEditForm(form: GovernmentForm): void {
  editingForm.value = form
  isFormDialogOpen.value = true
}

async function saveForm(input: FormInput): Promise<void> {
  isSavingForm.value = true
  try {
    if (editingForm.value) {
      await store.updateForm(editingForm.value.id, input)
      toastStore.show('success', 'Form updated', `${input.title} has been saved.`)
    } else {
      await store.createForm(input)
      toastStore.show('success', 'Form added', `${input.title} has been added to the library.`)
    }
    isFormDialogOpen.value = false
  } catch {
    toastStore.show('error', 'Unable to save form', 'Please try again.')
  } finally {
    isSavingForm.value = false
  }
}

function requestDeleteAuthority(authority: GovernmentAuthority): void {
  deleteTarget.value = { type: 'authority', id: authority.id, label: authority.name }
}

function requestDeleteForm(form: GovernmentForm): void {
  deleteTarget.value = { type: 'form', id: form.id, label: form.title }
}

async function confirmDelete(): Promise<void> {
  if (!deleteTarget.value) return
  isDeleting.value = true
  try {
    if (deleteTarget.value.type === 'authority') {
      await store.deleteAuthority(deleteTarget.value.id)
      if (selectedAuthorityId.value === deleteTarget.value.id) selectedAuthorityId.value = undefined
      toastStore.show('info', 'Authority removed', `${deleteTarget.value.label} and its forms were removed.`)
    } else {
      await store.deleteForm(deleteTarget.value.id)
      toastStore.show('info', 'Form removed', `${deleteTarget.value.label} was removed from the library.`)
    }
    deleteTarget.value = undefined
  } catch {
    toastStore.show('error', 'Unable to delete', 'Please try again.')
  } finally {
    isDeleting.value = false
  }
}

function formById(formId: string): GovernmentForm | undefined {
  return authorityForms.value.find((form) => form.id === formId)
}

function handleAiHelp(form: GovernmentForm): void {
  const authorityName = selectedAuthority.value?.name ?? 'the relevant authority'
  toastStore.show(
    'info',
    'AI Guidance',
    `Ensure all Required Documents for "${form.title}" are certified copies before submitting to ${authorityName}.`,
  )
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <template v-if="!selectedAuthorityId">
      <PageHeader
        title="Government Forms Library"
        subtitle="Browse government authorities and their submission forms."
      >
        <template #actions>
          <BaseButton :icon="Landmark" @click="openAddAuthority">Add Authority</BaseButton>
        </template>
      </PageHeader>

      <FilterBar
        :search-value="authoritySearchTerm"
        search-placeholder="Search authorities by name or category"
        :has-active-filters="authoritySearchTerm.trim().length > 0"
        @update:search-value="authoritySearchTerm = $event"
        @clear="authoritySearchTerm = ''"
      />

      <ErrorState v-if="store.error" :description="store.error" @retry="loadData" />

      <div v-else-if="store.isLoading" class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
        <div v-for="placeholder in 6" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="5" />
        </div>
      </div>

      <EmptyState
        v-else-if="visibleAuthorities.length === 0"
        title="No authorities found"
        description="Try a different search, or add a government authority to get started."
        action-label="Add Authority"
        @action="openAddAuthority"
      />

      <div v-else class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
        <AuthorityCard
          v-for="authority in visibleAuthorities"
          :key="authority.id"
          :authority="authority"
          :form-count="authorityFormCounts[authority.id] ?? 0"
          @open="openAuthority"
          @edit="openEditAuthority"
          @delete="requestDeleteAuthority"
        />
      </div>
    </template>

    <template v-else>
      <div class="flex flex-col gap-3">
        <button
          type="button"
          class="inline-flex w-fit items-center gap-1.5 text-sm font-medium text-neutral-500 hover:text-neutral-800"
          @click="backToAuthorities"
        >
          <ArrowLeft class="h-4 w-4" />
          Back to Authorities
        </button>

        <PageHeader :title="selectedAuthority?.name ?? 'Authority'" :subtitle="selectedAuthority?.description">
          <template #actions>
            <IconButton
              :icon="Pencil"
              label="Edit authority"
              variant="ghost"
              @click="selectedAuthority && openEditAuthority(selectedAuthority)"
            />
            <IconButton
              :icon="Trash2"
              label="Delete authority"
              variant="ghost"
              @click="selectedAuthority && requestDeleteAuthority(selectedAuthority)"
            />
            <BaseButton :icon="Plus" @click="openAddForm">Add Form</BaseButton>
          </template>
        </PageHeader>
      </div>

      <FilterBar
        :search-value="store.searchTerm"
        search-placeholder="Search by form title or code"
        :has-active-filters="store.hasActiveFilters"
        @update:search-value="store.setSearchTerm"
        @clear="store.clearFilters"
      >
        <template #filters>
          <div class="w-52">
            <SelectBox
              :model-value="store.categoryFilter"
              :options="CATEGORY_OPTIONS"
              @update:model-value="store.setCategoryFilter($event as GovernmentFormCategory | 'All')"
            />
          </div>
        </template>
        <template #actions>
          <div class="flex items-center gap-1 rounded-lg border border-border-default p-1">
            <IconButton
              :icon="LayoutGrid"
              label="Grid view"
              size="sm"
              :variant="store.viewMode === 'grid' ? 'primary' : 'ghost'"
              @click="store.setViewMode('grid')"
            />
            <IconButton
              :icon="TableProperties"
              label="Table view"
              size="sm"
              :variant="store.viewMode === 'table' ? 'primary' : 'ghost'"
              @click="store.setViewMode('table')"
            />
          </div>
        </template>
      </FilterBar>

      <template v-if="store.viewMode === 'grid'">
        <EmptyState
          v-if="authorityForms.length === 0"
          title="No forms found"
          description="Try adjusting your search or filters, or add a form to this authority."
          action-label="Add Form"
          @action="openAddForm"
        />
        <div v-else class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
          <GovernmentFormCard
            v-for="form in authorityForms"
            :key="form.id"
            :form="form"
            :authority="selectedAuthority"
            @ai-help="handleAiHelp"
            @edit="openEditForm"
            @delete="requestDeleteForm"
          />
        </div>
      </template>

      <SmartTable
        v-else
        :columns="TABLE_COLUMNS"
        :rows="authorityFormTableRows"
        row-key="id"
        :searchable="false"
        empty-title="No forms found"
        empty-description="Try adjusting your search or filters, or add a form to this authority."
      >
        <template #cell-category="{ value }">
          <StatusBadge :label="value as string" :variant="getFormCategoryVariant(value as GovernmentFormCategory)" />
        </template>
        <template #cell-lastUpdated="{ value }">
          {{ formatDate(value as string) }}
        </template>
        <template #row-actions="{ row }">
          <div class="flex items-center justify-end gap-1">
            <IconButton
              :icon="Pencil"
              label="Edit form"
              size="sm"
              variant="ghost"
              @click="formById(row.id) && openEditForm(formById(row.id)!)"
            />
            <IconButton
              :icon="Trash2"
              label="Delete form"
              size="sm"
              variant="ghost"
              @click="formById(row.id) && requestDeleteForm(formById(row.id)!)"
            />
          </div>
        </template>
      </SmartTable>
    </template>

    <GovernmentAuthorityFormDialog
      v-model="isAuthorityDialogOpen"
      :authority="editingAuthority"
      :saving="isSavingAuthority"
      @save="saveAuthority"
    />

    <GovernmentFormFormDialog
      v-model="isFormDialogOpen"
      :form="editingForm"
      :authorities="dialogAuthorities"
      :saving="isSavingForm"
      @save="saveForm"
    />

    <ConfirmationDialog
      :model-value="!!deleteTarget"
      title="Confirm Deletion"
      :message="`Are you sure you want to delete '${deleteTarget?.label}'? This cannot be undone.`"
      confirm-label="Delete"
      confirm-variant="danger"
      :loading="isDeleting"
      @update:model-value="deleteTarget = undefined"
      @confirm="confirmDelete"
    />
  </div>
</template>
