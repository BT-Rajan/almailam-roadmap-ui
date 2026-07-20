import { defineStore } from 'pinia'

import { userService } from '@/services/userService'
import type { RoleDefinition } from '@/types/Role'
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

    async addUser(user: AppUser) {
      this.users = [user, ...this.users]
      await userService.createUser(user)
    },

    async saveUser(user: AppUser) {
      const index = this.users.findIndex((existing) => existing.id === user.id)
      if (index !== -1) this.users[index] = user
      await userService.updateUser(user)
    },

    async toggleUserStatus(userId: string) {
      const user = this.users.find((existing) => existing.id === userId)
      if (!user) return
      const nextStatus: UserStatus = user.status === 'Active' ? 'Inactive' : 'Active'
      user.status = nextStatus
      await userService.setUserStatus(userId, nextStatus)
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
