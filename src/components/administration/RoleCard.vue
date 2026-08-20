<script setup lang="ts">
import { Pencil, X } from '@lucide/vue'
import { ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import IconButton from '@/components/common/IconButton.vue'
import PermissionMatrix from '@/components/administration/PermissionMatrix.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useRbac } from '@/composables/useRbac'
import { useUserStore } from '@/stores/userStore'
import { useToastStore } from '@/stores/toastStore'
import type { RoleDefinition, RolePermission } from '@/types/Role'

interface Props {
  definition: RoleDefinition
  userCount: number
}

const props = defineProps<Props>()

const { can } = useRbac()
const userStore = useUserStore()
const toastStore = useToastStore()

const isEditing = ref(false)
const isConfirmOpen = ref(false)
const isSaving = ref(false)
const draft = ref<RolePermission[]>([])

function startEditing(): void {
  draft.value = props.definition.permissions.map((permission) => ({ ...permission }))
  isEditing.value = true
}

function cancelEditing(): void {
  isEditing.value = false
  draft.value = []
}

function requestSave(): void {
  isConfirmOpen.value = true
}

async function confirmSave(): Promise<void> {
  isSaving.value = true
  try {
    await userStore.updateRoleDefinition(props.definition.role, draft.value)
    toastStore.show('success', 'Permissions updated', `${props.definition.role} permissions were saved.`)
    isEditing.value = false
    isConfirmOpen.value = false
  } catch (error) {
    toastStore.show('error', 'Update failed', error instanceof Error ? error.message : 'Please try again.')
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <Card>
    <template #header>
      <div class="flex items-center justify-between gap-2">
        <h3 class="text-sm font-semibold text-text-primary">{{ definition.role }}</h3>
        <div class="flex items-center gap-2">
          <StatusBadge :label="`${userCount} ${userCount === 1 ? 'user' : 'users'}`" variant="neutral" />
          <IconButton
            v-if="can('roles.edit') && !isEditing"
            :icon="Pencil"
            label="Edit permissions"
            size="sm"
            @click="startEditing"
          />
          <IconButton v-else-if="isEditing" :icon="X" label="Cancel" size="sm" @click="cancelEditing" />
        </div>
      </div>
    </template>

    <p class="mb-4 text-sm text-text-muted">{{ definition.description }}</p>
    <PermissionMatrix
      :permissions="isEditing ? draft : definition.permissions"
      :editable="isEditing"
      @update:permissions="draft = $event"
    />

    <div v-if="isEditing" class="mt-4 flex justify-end gap-3">
      <BaseButton variant="secondary" @click="cancelEditing">Cancel</BaseButton>
      <BaseButton @click="requestSave">Save Changes</BaseButton>
    </div>
  </Card>

  <ConfirmationDialog
    v-model="isConfirmOpen"
    title="Update role permissions"
    :message="`This changes access for every user assigned the ${definition.role} role. Continue?`"
    confirm-label="Save Changes"
    :loading="isSaving"
    @confirm="confirmSave"
  />
</template>
