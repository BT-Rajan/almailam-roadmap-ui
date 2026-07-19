<script setup lang="ts">
import { Landmark, Pencil, Plus, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import IconButton from '@/components/common/IconButton.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import GovernmentAuthorityFormDialog from '@/components/administration/GovernmentAuthorityFormDialog.vue'
import GovernmentFormFormDialog from '@/components/administration/GovernmentFormFormDialog.vue'
import type { AuthorityInput, FormInput } from '@/services/governmentFormService'
import { useGovernmentFormStore } from '@/stores/governmentFormStore'
import { useToastStore } from '@/stores/toastStore'
import type { GovernmentAuthority, GovernmentForm } from '@/types/Government'
import type { SmartTableColumn } from '@/types/Table'
import { formatDate } from '@/utils/dateFormatter'
import { getAuthorityCategoryIcon, getFormCategoryVariant } from '@/utils/governmentFormHelpers'

interface FormRow {
  [key: string]: unknown
  id: string
  formCode: string
  title: string
  category: GovernmentForm['category']
  language: GovernmentForm['language']
  version: string
  lastUpdated: string
}

const store = useGovernmentFormStore()
const toastStore = useToastStore()

const selectedAuthorityId = ref<string | 'All'>('All')

const isAuthorityDialogOpen = ref(false)
const editingAuthority = ref<GovernmentAuthority | undefined>(undefined)
const isSavingAuthority = ref(false)

const isFormDialogOpen = ref(false)
const editingForm = ref<GovernmentForm | undefined>(undefined)
const isSavingForm = ref(false)

const deleteTarget = ref<{ type: 'authority' | 'form'; id: string; label: string } | undefined>(undefined)
const isDeleting = ref(false)

const TABLE_COLUMNS: SmartTableColumn<FormRow>[] = [
  { key: 'formCode', label: 'Code', sortable: true, width: '140px' },
  { key: 'title', label: 'Form Title', sortable: true },
  { key: 'category', label: 'Category', sortable: true },
  { key: 'language', label: 'Language', sortable: true },
  { key: 'version', label: 'Version', width: '100px' },
  { key: 'lastUpdated', label: 'Last Updated', sortable: true, align: 'right' },
]

const visibleForms = computed<GovernmentForm[]>(() =>
  selectedAuthorityId.value === 'All'
    ? store.forms
    : store.forms.filter((form) => form.authorityId === selectedAuthorityId.value),
)

const tableRows = computed<FormRow[]>(() =>
  visibleForms.value.map((form) => ({
    id: form.id,
    formCode: form.formCode,
    title: form.title,
    category: form.category,
    language: form.language,
    version: form.version,
    lastUpdated: form.lastUpdated,
  })),
)

function loadData(): void {
  store.loadForms()
}

onMounted(() => {
  if (store.forms.length === 0) loadData()
})

function selectAuthority(authorityId: string | 'All'): void {
  selectedAuthorityId.value = selectedAuthorityId.value === authorityId ? 'All' : authorityId
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
</script>

<template>
  <div class="flex flex-col gap-6 p-4 lg:p-6">
    <PageHeader title="Government Forms Administration" subtitle="Maintain authorities, forms and their document requirements.">
      <template #actions>
        <BaseButton variant="secondary" :icon="Landmark" @click="openAddAuthority">Add Authority</BaseButton>
        <BaseButton :icon="Plus" @click="openAddForm">Add Form</BaseButton>
      </template>
    </PageHeader>

    <ErrorState v-if="store.error" :description="store.error" @retry="loadData" />

    <div v-else-if="store.isLoading" class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="6" />
      </div>
      <div class="rounded-xl border border-border-light bg-bg-card p-5 laptop:col-span-2">
        <SkeletonLoader :rows="8" />
      </div>
    </div>

    <div v-else class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="flex flex-col gap-3">
        <button
          class="rounded-xl border px-4 py-3 text-left text-sm font-medium transition-colors duration-fast"
          :class="
            selectedAuthorityId === 'All'
              ? 'border-primary-500 bg-primary-50 text-primary-700'
              : 'border-border-light bg-bg-card text-neutral-600 hover:bg-bg-hover'
          "
          @click="selectAuthority('All')"
        >
          All Authorities
          <span class="ml-1 text-xs text-neutral-400">({{ store.forms.length }})</span>
        </button>

        <Card v-for="authority in store.authorities" :key="authority.id" class="!p-0">
          <button
            class="flex w-full items-start gap-3 rounded-t-xl px-4 py-3 text-left transition-colors duration-fast"
            :class="selectedAuthorityId === authority.id ? 'bg-primary-50' : 'hover:bg-bg-hover'"
            @click="selectAuthority(authority.id)"
          >
            <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
              <component :is="getAuthorityCategoryIcon(authority.category)" :size="18" />
            </span>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-neutral-800">{{ authority.name }}</p>
              <p class="mt-0.5 text-xs text-neutral-400">{{ authority.category }}</p>
            </div>
          </button>
          <div class="flex items-center justify-end gap-1 border-t border-border-light px-2 py-1.5">
            <IconButton :icon="Pencil" label="Edit authority" size="sm" variant="ghost" @click="openEditAuthority(authority)" />
            <IconButton
              :icon="Trash2"
              label="Delete authority"
              size="sm"
              variant="ghost"
              @click="requestDeleteAuthority(authority)"
            />
          </div>
        </Card>

        <EmptyState
          v-if="store.authorities.length === 0"
          title="No authorities yet"
          description="Add a government authority to start attaching forms to it."
          action-label="Add Authority"
          @action="openAddAuthority"
        />
      </div>

      <div class="laptop:col-span-2">
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
