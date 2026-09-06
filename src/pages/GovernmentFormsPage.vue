<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import GovernmentAuthorityFormDialog from '@/components/administration/GovernmentAuthorityFormDialog.vue'
import GovernmentAuthorityBrowser from '@/components/government/GovernmentAuthorityBrowser.vue'
import GovernmentFormLibraryPanel from '@/components/government/GovernmentFormLibraryPanel.vue'
import type { AuthorityInput } from '@/services/governmentFormService'
import { useGovernmentFormStore } from '@/stores/governmentFormStore'
import { useToastStore } from '@/stores/toastStore'
import type { GovernmentAuthority } from '@/types/Government'

const store = useGovernmentFormStore()
const toastStore = useToastStore()
const { t } = useI18n()

const selectedAuthority = ref<GovernmentAuthority | undefined>(undefined)

const isAuthorityDialogOpen = ref(false)
const editingAuthority = ref<GovernmentAuthority | undefined>(undefined)
const isSavingAuthority = ref(false)

const deleteTarget = ref<{ id: string; label: string } | undefined>(undefined)
const isDeleting = ref(false)

onMounted(() => {
  if (store.forms.length === 0) store.loadForms()
})

function openAuthority(authority: GovernmentAuthority): void {
  selectedAuthority.value = authority
  store.clearFilters()
}

function backToAuthorities(): void {
  selectedAuthority.value = undefined
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
      toastStore.show('success', t('administration.governmentFormsPanel.authorityUpdatedTitle'), t('administration.governmentFormsPanel.authorityUpdatedDescription', { name: input.name }))
    } else {
      await store.createAuthority(input)
      toastStore.show('success', t('administration.governmentFormsPanel.authorityAddedTitle'), t('administration.governmentFormsPanel.authorityAddedDescription', { name: input.name }))
    }
    isAuthorityDialogOpen.value = false
  } catch {
    toastStore.show('error', t('administration.governmentFormsPanel.unableToSaveAuthority'), t('common.pleaseTryAgain'))
  } finally {
    isSavingAuthority.value = false
  }
}

function requestDeleteAuthority(authority: GovernmentAuthority): void {
  deleteTarget.value = { id: authority.id, label: authority.name }
}

async function confirmDeleteAuthority(): Promise<void> {
  if (!deleteTarget.value) return
  isDeleting.value = true
  try {
    await store.deleteAuthority(deleteTarget.value.id)
    if (selectedAuthority.value?.id === deleteTarget.value.id) selectedAuthority.value = undefined
    toastStore.show('info', t('administration.governmentFormsPanel.authorityRemovedTitle'), t('administration.governmentFormsPanel.authorityRemovedDescription', { label: deleteTarget.value.label }))
    deleteTarget.value = undefined
  } catch {
    toastStore.show('error', t('government.authorityBrowser.unableToDeleteAuthority'), t('common.pleaseTryAgain'))
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <GovernmentAuthorityBrowser
      v-if="!selectedAuthority"
      @open="openAuthority"
      @add="openAddAuthority"
      @edit="openEditAuthority"
      @delete="requestDeleteAuthority"
    />

    <GovernmentFormLibraryPanel
      v-else
      :authority="selectedAuthority"
      @back="backToAuthorities"
      @edit-authority="openEditAuthority"
      @delete-authority="requestDeleteAuthority"
    />

    <GovernmentAuthorityFormDialog
      v-model="isAuthorityDialogOpen"
      :authority="editingAuthority"
      :saving="isSavingAuthority"
      @save="saveAuthority"
    />

    <ConfirmationDialog
      :model-value="!!deleteTarget"
      :title="t('administration.governmentFormsPanel.confirmDeletionTitle')"
      :message="t('administration.governmentFormsPanel.confirmDeletionMessage', { label: deleteTarget?.label })"
      :confirm-label="t('common.delete')"
      confirm-variant="danger"
      :loading="isDeleting"
      @update:model-value="deleteTarget = undefined"
      @confirm="confirmDeleteAuthority"
    />
  </div>
</template>
