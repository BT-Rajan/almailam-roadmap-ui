<script setup lang="ts">
import { ArrowLeft, LayoutGrid, Pencil, Plus, TableProperties, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import IconButton from '@/components/common/IconButton.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import GovernmentFormFormDialog from '@/components/administration/GovernmentFormFormDialog.vue'
import FormDetailDrawer from '@/components/government/FormDetailDrawer.vue'
import GovernmentFormsView from '@/components/government/GovernmentFormsView.vue'
import type { FormInput } from '@/services/governmentFormService'
import { useGovernmentFormStore } from '@/stores/governmentFormStore'
import { useServiceCatalogStore } from '@/stores/serviceCatalogStore'
import { useToastStore } from '@/stores/toastStore'
import type { GovernmentAuthority, GovernmentForm, GovernmentFormCategory } from '@/types/Government'
import type { SelectOption } from '@/types/Ui'
import { printFillableForm, printFormSummary } from '@/utils/governmentFormHelpers'

const props = defineProps<{
  authority: GovernmentAuthority
}>()

const emit = defineEmits<{
  back: []
  editAuthority: [authority: GovernmentAuthority]
  deleteAuthority: [authority: GovernmentAuthority]
}>()

const { t } = useI18n()
const store = useGovernmentFormStore()
const serviceCatalogStore = useServiceCatalogStore()
const toastStore = useToastStore()

onMounted(() => {
  if (serviceCatalogStore.services.length === 0) serviceCatalogStore.loadServices()
})

const showArchived = ref(false)

const isFormDialogOpen = ref(false)
const editingForm = ref<GovernmentForm | undefined>(undefined)
const isSavingForm = ref(false)

const isDetailDrawerOpen = ref(false)
const viewingForm = ref<GovernmentForm | undefined>(undefined)

const isEditWarningOpen = ref(false)
const pendingEditForm = ref<GovernmentForm | undefined>(undefined)

const archiveTarget = ref<GovernmentForm | undefined>(undefined)
const isArchiving = ref(false)

const CATEGORY_OPTIONS: SelectOption[] = [
  { label: 'All Categories', value: 'All', labelKey: 'government.formLibraryPanel.allCategories' },
  { label: 'Building Permit', value: 'Building Permit', labelKey: 'governmentFormOptions.formCategory.buildingPermit' },
  {
    label: 'Occupancy Certificate',
    value: 'Occupancy Certificate',
    labelKey: 'governmentFormOptions.formCategory.occupancyCertificate',
  },
  {
    label: 'Fire Safety Approval',
    value: 'Fire Safety Approval',
    labelKey: 'governmentFormOptions.formCategory.fireSafetyApproval',
  },
  { label: 'Utility Connection', value: 'Utility Connection', labelKey: 'governmentFormOptions.formCategory.utilityConnection' },
  {
    label: 'Environmental Clearance',
    value: 'Environmental Clearance',
    labelKey: 'governmentFormOptions.formCategory.environmentalClearance',
  },
  { label: 'Business License', value: 'Business License', labelKey: 'governmentFormOptions.formCategory.businessLicense' },
]

const authorityForms = computed<GovernmentForm[]>(() => {
  const term = store.searchTerm.trim().toLowerCase()

  return store.forms.filter((form) => {
    const matchesAuthority = form.authorityId === props.authority.id
    const matchesArchived = showArchived.value || form.status === 'Active'
    const matchesSearch =
      term.length === 0 || form.title.toLowerCase().includes(term) || form.formCode.toLowerCase().includes(term)
    const matchesCategory = store.categoryFilter === 'All' || form.category === store.categoryFilter
    return matchesAuthority && matchesArchived && matchesSearch && matchesCategory
  })
})

// Ensures the "Add Form" dialog defaults to the authority currently being viewed.
const dialogAuthorities = computed<GovernmentAuthority[]>(() => [
  props.authority,
  ...store.authorities.filter((a) => a.id !== props.authority.id),
])

function openAddForm(): void {
  editingForm.value = undefined
  isFormDialogOpen.value = true
}

// Editing a form affects the shared master copy, so confirm intent first.
function requestEditForm(form: GovernmentForm): void {
  pendingEditForm.value = form
  isEditWarningOpen.value = true
}

function confirmEditWarning(): void {
  isEditWarningOpen.value = false
  isDetailDrawerOpen.value = false
  editingForm.value = pendingEditForm.value
  pendingEditForm.value = undefined
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

function requestArchiveForm(form: GovernmentForm): void {
  archiveTarget.value = form
}

async function confirmArchiveForm(): Promise<void> {
  if (!archiveTarget.value) return
  isArchiving.value = true
  try {
    await store.archiveForm(archiveTarget.value.id)
    toastStore.show('info', 'Form archived', `${archiveTarget.value.title} was moved to archived forms.`)
    isDetailDrawerOpen.value = false
    archiveTarget.value = undefined
  } catch {
    toastStore.show('error', 'Unable to archive form', 'Please try again.')
  } finally {
    isArchiving.value = false
  }
}

async function restoreForm(form: GovernmentForm): Promise<void> {
  try {
    await store.restoreForm(form.id)
    toastStore.show('success', 'Form restored', `${form.title} is active again.`)
  } catch {
    toastStore.show('error', 'Unable to restore form', 'Please try again.')
  }
}

function viewForm(form: GovernmentForm): void {
  viewingForm.value = form
  isDetailDrawerOpen.value = true
}

function handleAiHelp(form: GovernmentForm): void {
  toastStore.show(
    'info',
    'AI Guidance',
    `Ensure all Required Documents for "${form.title}" are certified copies before submitting to ${props.authority.name}.`,
  )
}

function printForm(form: GovernmentForm): void {
  if (form.previewUrl) {
    printFillableForm(form.previewUrl)
  } else {
    printFormSummary(form, props.authority.name)
  }
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <button
      type="button"
      class="inline-flex w-fit items-center gap-1.5 text-sm font-medium text-text-muted hover:text-text-primary"
      @click="emit('back')"
    >
      <ArrowLeft class="h-4 w-4" />
      {{ t('government.formLibraryPanel.backToAuthorities') }}
    </button>

    <PageHeader :title="authority.name" :subtitle="authority.description">
      <template #actions>
        <IconButton :icon="Pencil" :label="t('government.formLibraryPanel.editAuthority')" variant="ghost" @click="emit('editAuthority', authority)" />
        <IconButton :icon="Trash2" :label="t('government.formLibraryPanel.deleteAuthority')" variant="ghost" @click="emit('deleteAuthority', authority)" />
        <BaseButton :icon="Plus" @click="openAddForm">{{ t('government.formLibraryPanel.addForm') }}</BaseButton>
      </template>
    </PageHeader>
  </div>

  <FilterBar
    :search-value="store.searchTerm"
    :search-placeholder="t('government.formLibraryPanel.searchPlaceholder')"
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
      <ToggleSwitch v-model="showArchived" :label="t('government.formLibraryPanel.showArchived')" />
    </template>
    <template #actions>
      <div class="flex items-center gap-1 rounded-lg border border-border-default p-1">
        <IconButton
          :icon="LayoutGrid"
          :label="t('government.formLibraryPanel.gridView')"
          size="sm"
          :variant="store.viewMode === 'grid' ? 'primary' : 'ghost'"
          @click="store.setViewMode('grid')"
        />
        <IconButton
          :icon="TableProperties"
          :label="t('government.formLibraryPanel.tableView')"
          size="sm"
          :variant="store.viewMode === 'table' ? 'primary' : 'ghost'"
          @click="store.setViewMode('table')"
        />
      </div>
    </template>
  </FilterBar>

  <GovernmentFormsView
    :forms="authorityForms"
    :authority="authority"
    :view-mode="store.viewMode"
    @view="viewForm"
    @ai-help="handleAiHelp"
    @edit="requestEditForm"
    @archive="requestArchiveForm"
    @restore="restoreForm"
    @add-form="openAddForm"
  />

  <FormDetailDrawer
    v-model="isDetailDrawerOpen"
    :form="viewingForm"
    :authority="authority"
    @edit="requestEditForm"
    @archive="requestArchiveForm"
    @restore="restoreForm"
    @print="printForm"
  />

  <GovernmentFormFormDialog
    v-model="isFormDialogOpen"
    :form="editingForm"
    :authorities="dialogAuthorities"
    :services="serviceCatalogStore.services"
    :saving="isSavingForm"
    @save="saveForm"
  />

  <ConfirmationDialog
    :model-value="isEditWarningOpen"
    title="Edit Master Form"
    message="You're about to edit the master copy of this form. Changes will apply everywhere this form is referenced. Continue?"
    confirm-label="Continue to Edit"
    @update:model-value="isEditWarningOpen = $event"
    @confirm="confirmEditWarning"
  />

  <ConfirmationDialog
    :model-value="!!archiveTarget"
    title="Archive Form"
    :message="`Archive '${archiveTarget?.title}'? It will be hidden from the library but can be restored later.`"
    confirm-label="Archive"
    confirm-variant="danger"
    :loading="isArchiving"
    @update:model-value="archiveTarget = undefined"
    @confirm="confirmArchiveForm"
  />
</template>
