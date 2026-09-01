<script setup lang="ts">
import { ListChecks, Plus, Users as UsersIcon } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import PasswordResetDialog from '@/components/administration/PasswordResetDialog.vue'
import RoleCard from '@/components/administration/RoleCard.vue'
import UserCard from '@/components/administration/UserCard.vue'
import UserDialog from '@/components/administration/UserDialog.vue'
import { useUserStore } from '@/stores/userStore'
import { useToastStore } from '@/stores/toastStore'
import { useAuthStore } from '@/stores/authStore'
import type { SmartTableColumn } from '@/types/Table'
import type { AppUser, UserRole, UserStatus } from '@/types/User'
import type { SelectOption } from '@/types/Ui'
import { getUserRoleVariant, getUserStatusVariant } from '@/utils/userHelpers'

interface UserTableRow {
  [key: string]: unknown
  id: string
  name: string
  designation: string
  email: string
  role: UserRole
  status: UserStatus
}

const userStore = useUserStore()
const toastStore = useToastStore()
const authStore = useAuthStore()

const activeTab = ref<'users' | 'roles'>('users')
const selectedUserId = ref<string | undefined>(undefined)
const isProfileDialogOpen = ref(false)
const isDialogOpen = ref(false)
const editingUser = ref<AppUser | undefined>(undefined)
const isResetConfirmOpen = ref(false)
const isResettingPassword = ref(false)
const isPasswordResultOpen = ref(false)
const resetPasswordResult = ref('')
const passwordDialogUserName = ref('')
const passwordDialogHeading = ref<string | undefined>(undefined)
const isSavingUser = ref(false)
const isDeleteConfirmOpen = ref(false)
const isDeletingUser = ref(false)

const ROLE_OPTIONS: SelectOption[] = [
  { label: 'All Roles', value: 'All' },
  { label: 'Administrator', value: 'Administrator' },
  { label: 'Project Manager', value: 'Project Manager' },
  { label: 'Engineer', value: 'Engineer' },
  { label: 'Document Controller', value: 'Document Controller' },
  { label: 'Viewer', value: 'Viewer' },
]

const STATUS_OPTIONS: SelectOption[] = [
  { label: 'All Statuses', value: 'All' },
  { label: 'Active', value: 'Active' },
  { label: 'Inactive', value: 'Inactive' },
]

const TABLE_COLUMNS: SmartTableColumn<UserTableRow>[] = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'designation', label: 'Designation', sortable: true },
  { key: 'email', label: 'Email', sortable: true },
  { key: 'role', label: 'Role', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
]

const tableRows = computed<UserTableRow[]>(() =>
  userStore.filteredUsers.map((user) => ({
    id: user.id,
    name: user.name,
    designation: user.designation,
    email: user.email,
    role: user.role,
    status: user.status,
  })),
)

const selectedUser = computed(() => userStore.users.find((user) => user.id === selectedUserId.value))

function loadData(): void {
  userStore.loadUsers()
  userStore.loadRoleDefinitions()
}

onMounted(() => {
  if (userStore.users.length === 0) loadData()
  if (userStore.roleDefinitions.length === 0) userStore.loadRoleDefinitions()
})

function openUser(row: UserTableRow): void {
  selectedUserId.value = row.id
  isProfileDialogOpen.value = true
}

function openCreateDialog(): void {
  editingUser.value = undefined
  isDialogOpen.value = true
}

function openEditDialog(user: AppUser): void {
  editingUser.value = user
  isDialogOpen.value = true
  isProfileDialogOpen.value = false
}

async function handleSave(user: AppUser): Promise<void> {
  isSavingUser.value = true
  try {
    if (editingUser.value) {
      await userStore.saveUser(user)
      toastStore.show('success', 'User updated', `${user.name} was updated successfully.`)
    } else {
      const created = await userStore.addUser(user)
      toastStore.show('success', 'User added', `${created.name} was added to the firm.`)
      passwordDialogUserName.value = created.name
      passwordDialogHeading.value = `Login created for ${created.name}`
      resetPasswordResult.value = created.temporaryPassword
      isPasswordResultOpen.value = true
    }
    isDialogOpen.value = false
  } catch (error) {
    toastStore.show(
      'error',
      editingUser.value ? 'Failed to update user' : 'Failed to add user',
      error instanceof Error ? error.message : 'Please try again.',
    )
  } finally {
    isSavingUser.value = false
  }
}

async function handleToggleStatus(user: AppUser): Promise<void> {
  const name = user.name
  const nextStatus = await userStore.toggleUserStatus(user.id)
  if (!nextStatus) return
  toastStore.show('info', `User ${nextStatus.toLowerCase()}`, `${name} is now ${nextStatus.toLowerCase()}.`)
}

async function handleResetPassword(): Promise<void> {
  if (!selectedUser.value) return
  isResettingPassword.value = true
  try {
    resetPasswordResult.value = await userStore.resetUserPassword(selectedUser.value.id)
    passwordDialogUserName.value = selectedUser.value.name
    passwordDialogHeading.value = undefined
    isResetConfirmOpen.value = false
    isPasswordResultOpen.value = true
  } catch (error) {
    toastStore.show('error', 'Password reset failed', error instanceof Error ? error.message : undefined)
  } finally {
    isResettingPassword.value = false
  }
}

async function handleDeleteUser(): Promise<void> {
  if (!selectedUser.value) return
  isDeletingUser.value = true
  try {
    const name = selectedUser.value.name
    await userStore.deleteUser(selectedUser.value.id)
    toastStore.show('success', 'User deleted', `${name} was removed from the firm.`)
    isDeleteConfirmOpen.value = false
    isProfileDialogOpen.value = false
  } catch (error) {
    toastStore.show('error', 'Failed to delete user', error instanceof Error ? error.message : 'Please try again.')
  } finally {
    isDeletingUser.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader title="User Management" subtitle="Manage users, roles, and permissions across the firm.">
      <template #actions>
        <BaseButton :icon="Plus" @click="openCreateDialog">Add User</BaseButton>
      </template>
    </PageHeader>

    <div class="flex items-center gap-1 rounded-lg border border-border-default p-1 w-fit">
      <button
        type="button"
        class="flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-fast"
        :class="activeTab === 'users' ? 'bg-primary-600 text-neutral-0' : 'text-text-secondary hover:bg-bg-hover'"
        @click="activeTab = 'users'"
      >
        <UsersIcon :size="15" />
        Users
      </button>
      <button
        type="button"
        class="flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-fast"
        :class="activeTab === 'roles' ? 'bg-primary-600 text-neutral-0' : 'text-text-secondary hover:bg-bg-hover'"
        @click="activeTab = 'roles'"
      >
        <ListChecks :size="15" />
        Roles &amp; Permissions
      </button>
    </div>

    <template v-if="activeTab === 'users'">
      <FilterBar
        :show-search="false"
        :has-active-filters="userStore.hasActiveFilters"
        @clear="userStore.clearFilters"
      >
        <template #filters>
          <div class="w-48">
            <SelectBox
              :model-value="userStore.roleFilter"
              :options="ROLE_OPTIONS"
              @update:model-value="userStore.setRoleFilter($event as UserRole | 'All')"
            />
          </div>
          <div class="w-40">
            <SelectBox
              :model-value="userStore.statusFilter"
              :options="STATUS_OPTIONS"
              @update:model-value="userStore.setStatusFilter($event as UserStatus | 'All')"
            />
          </div>
        </template>
      </FilterBar>

      <ErrorState v-if="userStore.error" :description="userStore.error" @retry="loadData" />

      <SmartTable
        v-else
        :columns="TABLE_COLUMNS"
        :rows="tableRows"
        row-key="id"
        :loading="userStore.isLoading"
        :searchable="false"
        empty-title="No users found"
        empty-description="Try adjusting your search or filters, or add a new user."
        @row-click="openUser"
      >
        <template #cell-role="{ value }">
          <StatusBadge :label="value as string" :variant="getUserRoleVariant(value as UserRole)" />
        </template>
        <template #cell-status="{ value }">
          <StatusBadge :label="value as string" :variant="getUserStatusVariant(value as UserStatus)" show-dot />
        </template>
      </SmartTable>
    </template>

    <div v-else class="grid grid-cols-1 gap-4 laptop:grid-cols-2">
      <RoleCard
        v-for="definition in userStore.roleDefinitions"
        :key="definition.role"
        :definition="definition"
        :user-count="userStore.userCountByRole(definition.role)"
      />
    </div>

    <BaseDialog v-model="isProfileDialogOpen" title="User Profile" size="md">
      <div v-if="selectedUser" class="flex flex-col gap-4">
        <UserCard :user="selectedUser" />
        <div class="flex justify-end gap-3">
          <BaseButton
            v-if="selectedUser.role !== 'Administrator'"
            variant="secondary"
            @click="isResetConfirmOpen = true"
          >
            Reset Password
          </BaseButton>
          <BaseButton variant="secondary" @click="handleToggleStatus(selectedUser)">
            {{ selectedUser.status === 'Active' ? 'Deactivate' : 'Activate' }}
          </BaseButton>
          <BaseButton
            v-if="selectedUser.id !== authStore.user?.id"
            variant="danger"
            @click="isDeleteConfirmOpen = true"
          >
            Delete User
          </BaseButton>
          <BaseButton @click="openEditDialog(selectedUser)">Edit User</BaseButton>
        </div>
      </div>
    </BaseDialog>

    <UserDialog v-model="isDialogOpen" :user="editingUser" :saving="isSavingUser" @save="handleSave" />

    <ConfirmationDialog
      v-model="isResetConfirmOpen"
      title="Reset Password"
      :message="`Generate a new random password for ${selectedUser?.name}? Their current password will stop working immediately.`"
      confirm-label="Reset Password"
      :loading="isResettingPassword"
      @confirm="handleResetPassword"
    />

    <PasswordResetDialog
      v-model="isPasswordResultOpen"
      :user-name="passwordDialogUserName"
      :password="resetPasswordResult"
      :heading="passwordDialogHeading"
    />

    <ConfirmationDialog
      v-model="isDeleteConfirmOpen"
      title="Delete User"
      :message="`Permanently remove ${selectedUser?.name} from the firm? They will immediately lose access and this cannot be undone.`"
      confirm-label="Delete User"
      confirm-variant="danger"
      :loading="isDeletingUser"
      @confirm="handleDeleteUser"
    />
  </div>
</template>
