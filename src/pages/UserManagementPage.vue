<script setup lang="ts">
import { ListChecks, Plus, Users as UsersIcon } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import RoleCard from '@/components/administration/RoleCard.vue'
import UserCard from '@/components/administration/UserCard.vue'
import UserDialog from '@/components/administration/UserDialog.vue'
import { useUserStore } from '@/stores/userStore'
import { useToastStore } from '@/stores/toastStore'
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

const activeTab = ref<'users' | 'roles'>('users')
const selectedUserId = ref<string | undefined>(undefined)
const isDrawerOpen = ref(false)
const isDialogOpen = ref(false)
const editingUser = ref<AppUser | undefined>(undefined)

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
  isDrawerOpen.value = true
}

function openCreateDialog(): void {
  editingUser.value = undefined
  isDialogOpen.value = true
}

function openEditDialog(user: AppUser): void {
  editingUser.value = user
  isDialogOpen.value = true
  isDrawerOpen.value = false
}

async function handleSave(user: AppUser): Promise<void> {
  if (editingUser.value) {
    await userStore.saveUser(user)
    toastStore.show('success', 'User updated', `${user.name} was updated successfully.`)
  } else {
    await userStore.addUser(user)
    toastStore.show('success', 'User added', `${user.name} was added to the firm.`)
  }
}

async function handleToggleStatus(user: AppUser): Promise<void> {
  await userStore.toggleUserStatus(user.id)
  const nextStatus = user.status === 'Active' ? 'Inactive' : 'Active'
  toastStore.show('info', `User ${nextStatus.toLowerCase()}`, `${user.name} is now ${nextStatus.toLowerCase()}.`)
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
        :class="activeTab === 'users' ? 'bg-primary-600 text-neutral-0' : 'text-neutral-600 hover:bg-bg-hover'"
        @click="activeTab = 'users'"
      >
        <UsersIcon :size="15" />
        Users
      </button>
      <button
        type="button"
        class="flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-fast"
        :class="activeTab === 'roles' ? 'bg-primary-600 text-neutral-0' : 'text-neutral-600 hover:bg-bg-hover'"
        @click="activeTab = 'roles'"
      >
        <ListChecks :size="15" />
        Roles &amp; Permissions
      </button>
    </div>

    <template v-if="activeTab === 'users'">
      <FilterBar
        :search-value="userStore.searchTerm"
        search-placeholder="Search by name, email, or designation"
        :has-active-filters="userStore.hasActiveFilters"
        @update:search-value="userStore.setSearchTerm"
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

    <BaseDrawer v-model="isDrawerOpen" title="User Profile" width="md">
      <div v-if="selectedUser" class="flex flex-col gap-4">
        <UserCard :user="selectedUser" />
        <div class="flex justify-end gap-3">
          <BaseButton variant="secondary" @click="handleToggleStatus(selectedUser)">
            {{ selectedUser.status === 'Active' ? 'Deactivate' : 'Activate' }}
          </BaseButton>
          <BaseButton @click="openEditDialog(selectedUser)">Edit User</BaseButton>
        </div>
      </div>
    </BaseDrawer>

    <UserDialog v-model="isDialogOpen" :user="editingUser" @save="handleSave" />
  </div>
</template>
