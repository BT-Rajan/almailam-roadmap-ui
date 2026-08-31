import { defineStore } from 'pinia'

import { userService } from '@/services/userService'
import type { CreatedUser } from '@/services/userService'
import type { RoleDefinition, RolePermission } from '@/types/Role'
import type { AppUser, UserRole, UserStatus } from '@/types/User'

interface UserStoreState {
  users: AppUser[]
  roleDefinitions: RoleDefinition[]
  isLoading: boolean
  isRolesLoading: boolean
  error: string | undefined
  searchTerm: string
  roleFilter: UserRole | 'All'
  statusFilter: UserStatus | 'All'
}

export const useUserStore = defineStore('user', {
  state: (): UserStoreState => ({
    users: [],
    roleDefinitions: [],
    isLoading: false,
    isRolesLoading: false,
    error: undefined,
    searchTerm: '',
    roleFilter: 'All',
    statusFilter: 'All',
  }),

  getters: {
    filteredUsers(state): AppUser[] {
      const term = state.searchTerm.trim().toLowerCase()

      return state.users.filter((user) => {
        const matchesSearch =
          term.length === 0 ||
          user.name.toLowerCase().includes(term) ||
          user.email.toLowerCase().includes(term) ||
          user.designation.toLowerCase().includes(term)

        const matchesRole = state.roleFilter === 'All' || user.role === state.roleFilter
        const matchesStatus = state.statusFilter === 'All' || user.status === state.statusFilter

        return matchesSearch && matchesRole && matchesStatus
      })
    },

    hasActiveFilters(state): boolean {
      return state.searchTerm.trim().length > 0 || state.roleFilter !== 'All' || state.statusFilter !== 'All'
    },

    getRoleDefinition(state) {
      return (role: UserRole): RoleDefinition | undefined =>
        state.roleDefinitions.find((definition) => definition.role === role)
    },

    userCountByRole(state) {
      return (role: UserRole): number => state.users.filter((user) => user.role === role).length
    },
  },

  actions: {
    async loadUsers() {
      this.isLoading = true
      this.error = undefined
      try {
        this.users = await userService.getUsers()
      } catch {
        this.error = 'Unable to load users. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async loadRoleDefinitions() {
      this.isRolesLoading = true
      try {
        this.roleDefinitions = await userService.getRoleDefinitions()
      } finally {
        this.isRolesLoading = false
      }
    },

    async updateRoleDefinition(role: string, permissions: RolePermission[]) {
      const updated = await userService.updateRoleDefinition(role, permissions)
      const index = this.roleDefinitions.findIndex((definition) => definition.role === role)
      if (index !== -1) this.roleDefinitions[index] = updated
      return updated
    },

    // Persist first, then store the backend-assigned user (including its
    // real id) -- previously this stored the caller's locally-generated
    // placeholder id (see UserDialog.vue) and discarded what the backend
    // actually created, so the id shown in the UI right after creating a
    // user didn't match the one it would have after a refresh.
    async addUser(user: AppUser): Promise<CreatedUser> {
      const created = await userService.createUser(user)
      // UserCreate has no is_active field server-side -- new users are
      // always created Active, so an unchecked "Active" toggle in the
      // dialog needs a follow-up status call to actually take effect.
      if (user.status === 'Inactive') {
        await userService.setUserStatus(created.id, 'Inactive')
        created.status = 'Inactive'
      }
      this.users = [created, ...this.users]
      return created
    },

    // Persist first, then reconcile local state from what the backend
    // actually saved -- previously this wrote the caller's optimistic
    // AppUser into local state *before* the update call, so a failed or
    // partially-accepted save still looked successful in the UI.
    async saveUser(user: AppUser) {
      const updated = await userService.updateUser(user)
      if (updated.status !== user.status) {
        await userService.setUserStatus(user.id, user.status)
        updated.status = user.status
      }
      const index = this.users.findIndex((existing) => existing.id === user.id)
      if (index !== -1) this.users[index] = updated
    },

    async toggleUserStatus(userId: string) {
      const user = this.users.find((existing) => existing.id === userId)
      if (!user) return
      const nextStatus: UserStatus = user.status === 'Active' ? 'Inactive' : 'Active'
      user.status = nextStatus
      await userService.setUserStatus(userId, nextStatus)
    },

    async resetUserPassword(userId: string): Promise<string> {
      return userService.resetPassword(userId)
    },

    async deleteUser(userId: string) {
      await userService.deleteUser(userId)
      this.users = this.users.filter((existing) => existing.id !== userId)
    },

    setSearchTerm(term: string) {
      this.searchTerm = term
    },

    setRoleFilter(role: UserRole | 'All') {
      this.roleFilter = role
    },

    setStatusFilter(status: UserStatus | 'All') {
      this.statusFilter = status
    },

    clearFilters() {
      this.searchTerm = ''
      this.roleFilter = 'All'
      this.statusFilter = 'All'
    },
  },
})
