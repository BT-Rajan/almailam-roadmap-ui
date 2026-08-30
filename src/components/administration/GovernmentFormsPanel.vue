<script setup lang="ts">
import { Ban, Eye, Landmark, Pencil, Plus, RotateCcw, Trash2, Upload } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import IconButton from '@/components/common/IconButton.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import GovernmentAuthorityFormDialog from '@/components/administration/GovernmentAuthorityFormDialog.vue'
import GovernmentFormFormDialog from '@/components/administration/GovernmentFormFormDialog.vue'
import LoadStandardFormsDialog from '@/components/administration/LoadStandardFormsDialog.vue'
import FormTemplatePreviewDialog from '@/components/government/FormTemplatePreviewDialog.vue'
import { FORM_STATUS_FILTER_OPTIONS } from '@/constants/governmentFormOptions'
import { STANDARD_GOVERNMENT_FORMS } from '@/constants/standardGovernmentForms'
import type { AuthorityInput, FormInput } from '@/services/governmentFormService'
import { useGovernmentFormStore } from '@/stores/governmentFormStore'
import { useServiceCatalogStore } from '@/stores/serviceCatalogStore'
import { useToastStore } from '@/stores/toastStore'
import type { GovernmentAuthority, GovernmentForm, GovernmentFormStatus } from '@/types/Government'
import type { SmartTableColumn } from '@/types/Table'
import type { SelectOption } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'
import { getFormCategoryVariant } from '@/utils/governmentFormHelpers'

interface FormRow {
  [key: string]: unknown
  id: string
  formCode: string
  title: string
  category: GovernmentForm['category']
  language: GovernmentForm['language']
  version: string
  status: GovernmentForm['status']
  lastUpdated: string
}

const store = useGovernmentFormStore()
const serviceCatalogStore = useServiceCatalogStore()
const toastStore = useToastStore()

const selectedAuthorityId = ref<string | 'All'>('All')
const statusFilter = ref<GovernmentFormStatus | 'All'>('Active')

const isAuthorityDialogOpen = ref(false)
const editingAuthority = ref<GovernmentAuthority | undefined>(undefined)
const isSavingAuthority = ref(false)

const isFormDialogOpen = ref(false)
const editingForm = ref<GovernmentForm | undefined>(undefined)
const isSavingForm = ref(false)

const isImportDialogOpen = ref(false)
const isImporting = ref(false)

const previewTarget = ref<GovernmentForm | undefined>(undefined)

const deleteTarget = ref<{ type: 'authority' | 'form'; id: string; label: string } | undefined>(undefined)
const isDeleting = ref(false)

const TABLE_COLUMNS: SmartTableColumn<FormRow>[] = [
  { key: 'formCode', label: 'Code', sortable: true, width: '140px' },
  { key: 'title', label: 'Form Title', sortable: true },
  { key: 'category', label: 'Category', sortable: true },
  { key: 'language', label: 'Language', sortable: true },
  { key: 'version', label: 'Version', width: '100px' },
  { key: 'status', label: 'Status', sortable: true, width: '110px' },
  { key: 'lastUpdated', label: 'Last Updated', sortable: true, align: 'right' },
]

const authorityOptions = computed<SelectOption[]>(() => [
  { label: `All Authorities (${store.forms.length})`, value: 'All' },
  ...store.authorities.map((authority) => ({
    label: `${authority.name} (${store.forms.filter((form) => form.authorityId === authority.id).length})`,
    value: authority.id,
  })),
])

const selectedAuthority = computed<GovernmentAuthority | undefined>(() =>
  store.authorities.find((authority) => authority.id === selectedAuthorityId.value),
)

const visibleForms = computed<GovernmentForm[]>(() =>
  store.forms
    .filter((form) => selectedAuthorityId.value === 'All' || form.authorityId === selectedAuthorityId.value)
    .filter((form) => statusFilter.value === 'All' || form.status === statusFilter.value),
)

const tableRows = computed<FormRow[]>(() =>
  visibleForms.value.map((form) => ({
    id: form.id,
    formCode: form.formCode,
    title: form.title,
    category: form.category,
    language: form.language,
    version: form.version,
    status: form.status,
    lastUpdated: form.lastUpdated,
  })),
)

function loadData(): void {
  store.loadForms()
}

onMounted(() => {
  if (store.forms.length === 0) loadData()
  if (serviceCatalogStore.services.length === 0) serviceCatalogStore.loadServices()
})

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
      if (selectedAuthorityId.value === deleteTarget.value.id) selectedAuthorityId.value = 'All'
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
  return store.forms.find((form) => form.id === formId)
}

async function toggleFormStatus(form: GovernmentForm): Promise<void> {
  try {
    if (form.status === 'Active') {
      await store.archiveForm(form.id)
      toastStore.show('info', 'Form disabled', `${form.title} is now archived and hidden from projects.`)
    } else {
      await store.restoreForm(form.id)
      toastStore.show('success', 'Form enabled', `${form.title} is active again.`)
    }
  } catch {
    toastStore.show('error', 'Unable to update status', 'Please try again.')
  }
}

async function importStandardForms(payload: { authorityId: string; formCodes: string[] }): Promise<void> {
  isImporting.value = true
  try {
    const seeds = STANDARD_GOVERNMENT_FORMS.filter((seed) => payload.formCodes.includes(seed.formCode))
    for (const seed of seeds) {
      await store.createForm({
        authorityId: payload.authorityId,
        formCode: seed.formCode,
        title: seed.title,
        version: 'v1.0',
        language: seed.language,
        category: seed.category,
        description: seed.description,
        requiredDocuments: [],
        lastUpdated: new Date().toISOString().slice(0, 10),
        status: 'Active',
        template: seed.template,
        serviceTags: [],
        fields: [],
      })
    }
    toastStore.show('success', 'Standard forms added', `${seeds.length} form${seeds.length === 1 ? '' : 's'} added to the library.`)
    isImportDialogOpen.value = false
  } catch {
    toastStore.show('error', 'Unable to import forms', 'Some forms may not have been added. Please try again.')
  } finally {
    isImporting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <div class="flex justify-end gap-2">
      <BaseButton variant="secondary" :icon="Landmark" @click="openAddAuthority">Add Authority</BaseButton>
      <BaseButton variant="secondary" :icon="Upload" @click="isImportDialogOpen = true">Load Standard Forms</BaseButton>
      <BaseButton :icon="Plus" @click="openAddForm">Add Form</BaseButton>
    </div>

    <ErrorState v-if="store.error" :description="store.error" @retry="loadData" />

    <div v-else-if="store.isLoading" class="rounded-xl border border-border-light bg-bg-card p-6">
      <SkeletonLoader :rows="8" />
    </div>

    <div v-else class="flex flex-col gap-3">
      <div class="flex flex-wrap items-end justify-between gap-3">
        <div class="flex items-end gap-2">
          <div class="w-64">
            <SelectBox v-model="selectedAuthorityId" label="Authority" :options="authorityOptions" />
          </div>
          <IconButton
            v-if="selectedAuthority"
            :icon="Pencil"
            label="Edit authority"
            size="sm"
            variant="ghost"
            @click="openEditAuthority(selectedAuthority)"
          />
          <IconButton
            v-if="selectedAuthority"
            :icon="Trash2"
            label="Delete authority"
            size="sm"
            variant="ghost"
            @click="requestDeleteAuthority(selectedAuthority)"
          />
        </div>

        <div class="w-48">
          <SelectBox v-model="statusFilter" label="Status" :options="FORM_STATUS_FILTER_OPTIONS" />
        </div>
      </div>

      <p v-if="store.authorities.length === 0" class="text-sm text-text-muted">
        No authorities yet -- add one to start filing forms under it.
      </p>

      <div>
        <SmartTable
          :columns="TABLE_COLUMNS"
          :rows="tableRows"
          row-key="id"
          :searchable="true"
          search-placeholder="Search forms by title or code"
          empty-title="No forms found"
          empty-description="Add a government form to build out the library."
        >
          <template #cell-category="{ value }">
            <StatusBadge :label="value as string" :variant="getFormCategoryVariant(value as GovernmentForm['category'])" />
          </template>
          <template #cell-status="{ value }">
            <StatusBadge :label="value as string" :variant="value === 'Active' ? 'success' : 'neutral'" show-dot />
          </template>
          <template #cell-lastUpdated="{ value }">
            {{ formatDate(value as string) }}
          </template>
          <template #row-actions="{ row }">
            <div class="flex items-center justify-end gap-1">
              <IconButton
                :icon="Eye"
                label="Preview form"
                size="sm"
                variant="ghost"
                @click="previewTarget = formById(row.id)"
              />
              <IconButton
                v-if="formById(row.id)?.status === 'Active'"
                :icon="Ban"
                label="Disable form"
                size="sm"
                variant="ghost"
                @click="formById(row.id) && toggleFormStatus(formById(row.id)!)"
              />
              <IconButton
                v-else
                :icon="RotateCcw"
                label="Enable form"
                size="sm"
                variant="ghost"
                @click="formById(row.id) && toggleFormStatus(formById(row.id)!)"
              />
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
      </div>
    </div>

    <GovernmentAuthorityFormDialog
      v-model="isAuthorityDialogOpen"
      :authority="editingAuthority"
      :saving="isSavingAuthority"
      @save="saveAuthority"
    />

    <GovernmentFormFormDialog
      v-model="isFormDialogOpen"
      :form="editingForm"
      :authorities="store.authorities"
      :services="serviceCatalogStore.services"
      :saving="isSavingForm"
      @save="saveForm"
    />

    <LoadStandardFormsDialog
      v-model="isImportDialogOpen"
      :authorities="store.authorities"
      :existing-form-codes="store.forms.map((form) => form.formCode)"
      :importing="isImporting"
      @import="importStandardForms"
    />

    <FormTemplatePreviewDialog
      :model-value="!!previewTarget"
      :form="previewTarget"
      :context="{
        companyName: 'Al Mailam Engineering Office',
        clientName: 'Sample Client Name',
        projectName: 'Sample Project',
        projectAddress: 'Sample Property Address',
        engineerName: 'Sample Engineer',
        date: formatDate(new Date().toISOString()),
      }"
      stub-notice="Fields below start filled with sample data -- edit them and save as PDF to try the template. Nothing here is saved to a project; filling a form for a real project is done from that project's own workspace."
      @update:model-value="previewTarget = undefined"
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
