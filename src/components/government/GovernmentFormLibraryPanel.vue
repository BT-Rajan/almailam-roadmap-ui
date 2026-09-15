<script setup lang="ts">
import { ArrowLeft, ArrowRight, LayoutGrid, Pencil, Plus, TableProperties, Trash2 } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import IconButton from '@/components/common/IconButton.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import FormDetailDrawer from '@/components/government/FormDetailDrawer.vue'
import GovernmentFormsView from '@/components/government/GovernmentFormsView.vue'
import { useLocale } from '@/composables/useLocale'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useGovernmentFormStore } from '@/stores/governmentFormStore'
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
const { isRtl } = useLocale()
const router = useRouter()

// Points the way "back" actually goes, which flips with reading
// direction.
const backIcon = computed(() => (isRtl.value ? ArrowRight : ArrowLeft))
const store = useGovernmentFormStore()
const toastStore = useToastStore()

const showArchived = ref(false)

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

function openAddForm(): void {
  router.push({ name: ROUTE_NAMES.GOVERNMENT_FORM_FORM, params: { formId: 'new' }, query: { authorityId: props.authority.id } })
}

// Editing a form affects the shared master copy, so confirm intent first.
function requestEditForm(form: GovernmentForm): void {
  pendingEditForm.value = form
  isEditWarningOpen.value = true
}

function confirmEditWarning(): void {
  isEditWarningOpen.value = false
  isDetailDrawerOpen.value = false
  if (pendingEditForm.value) router.push({ name: ROUTE_NAMES.GOVERNMENT_FORM_FORM, params: { formId: pendingEditForm.value.id } })
  pendingEditForm.value = undefined
}

function requestArchiveForm(form: GovernmentForm): void {
  archiveTarget.value = form
}

async function confirmArchiveForm(): Promise<void> {
  if (!archiveTarget.value) return
  isArchiving.value = true
  try {
    await store.archiveForm(archiveTarget.value.id)
    toastStore.show('info', t('government.formLibraryPanel.formArchivedTitle'), t('government.formLibraryPanel.formArchivedDescription', { title: archiveTarget.value.title }))
    isDetailDrawerOpen.value = false
    archiveTarget.value = undefined
  } catch {
    toastStore.show('error', t('government.formLibraryPanel.unableToArchiveForm'), t('common.pleaseTryAgain'))
  } finally {
    isArchiving.value = false
  }
}

async function restoreForm(form: GovernmentForm): Promise<void> {
  try {
    await store.restoreForm(form.id)
    toastStore.show('success', t('government.formLibraryPanel.formRestoredTitle'), t('government.formLibraryPanel.formRestoredDescription', { title: form.title }))
  } catch {
    toastStore.show('error', t('government.formLibraryPanel.unableToRestoreForm'), t('common.pleaseTryAgain'))
  }
}

function viewForm(form: GovernmentForm): void {
  viewingForm.value = form
  isDetailDrawerOpen.value = true
}

function handleAiHelp(form: GovernmentForm): void {
  toastStore.show(
    'info',
    t('government.formLibraryPanel.aiGuidanceTitle'),
    t('government.formLibraryPanel.aiGuidanceDescription', { title: form.title, authority: props.authority.name }),
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
      <component :is="backIcon" class="h-4 w-4" />
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

  <ConfirmationDialog
    :model-value="isEditWarningOpen"
    :title="t('government.formLibraryPanel.editMasterFormTitle')"
    :message="t('government.formLibraryPanel.editMasterFormMessage')"
    :confirm-label="t('government.formLibraryPanel.continueToEdit')"
    @update:model-value="isEditWarningOpen = $event"
    @confirm="confirmEditWarning"
  />

  <ConfirmationDialog
    :model-value="!!archiveTarget"
    :title="t('government.formLibraryPanel.archiveFormConfirmTitle')"
    :message="t('government.formLibraryPanel.archiveFormConfirmMessage', { title: archiveTarget?.title })"
    :confirm-label="t('government.formLibraryPanel.archiveFormConfirmLabel')"
    confirm-variant="danger"
    :loading="isArchiving"
    @update:model-value="archiveTarget = undefined"
    @confirm="confirmArchiveForm"
  />
</template>
