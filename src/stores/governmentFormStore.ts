import { defineStore } from 'pinia'

import { governmentFormService } from '@/services/governmentFormService'
import type {
  GovernmentAuthority,
  GovernmentForm,
  GovernmentFormCategory,
  GovernmentFormViewMode,
} from '@/types/Government'

interface GovernmentFormGroup {
  authority: GovernmentAuthority
  forms: GovernmentForm[]
}

interface GovernmentFormStoreState {
  forms: GovernmentForm[]
  authorities: GovernmentAuthority[]
  isLoading: boolean
  error: string | undefined
  searchTerm: string
  authorityFilter: string | 'All'
  categoryFilter: GovernmentFormCategory | 'All'
  viewMode: GovernmentFormViewMode
}

export const useGovernmentFormStore = defineStore('governmentForm', {
  state: (): GovernmentFormStoreState => ({
    forms: [],
    authorities: [],
    isLoading: false,
    error: undefined,
    searchTerm: '',
    authorityFilter: 'All',
    categoryFilter: 'All',
    viewMode: 'grid',
  }),

  getters: {
    filteredForms(state): GovernmentForm[] {
      const term = state.searchTerm.trim().toLowerCase()

      return state.forms.filter((form) => {
        const matchesSearch =
          term.length === 0 ||
          form.title.toLowerCase().includes(term) ||
          form.formCode.toLowerCase().includes(term)

        const matchesAuthority = state.authorityFilter === 'All' || form.authorityId === state.authorityFilter
        const matchesCategory = state.categoryFilter === 'All' || form.category === state.categoryFilter

        return matchesSearch && matchesAuthority && matchesCategory
      })
    },

    hasActiveFilters(state): boolean {
      return (
        state.searchTerm.trim().length > 0 || state.authorityFilter !== 'All' || state.categoryFilter !== 'All'
      )
    },

    getAuthorityById(state) {
      return (authorityId: string): GovernmentAuthority | undefined =>
        state.authorities.find((authority) => authority.id === authorityId)
    },

    groupedByAuthority(): GovernmentFormGroup[] {
      return this.authorities
        .map((authority) => ({
          authority,
          forms: this.filteredForms.filter((form) => form.authorityId === authority.id),
        }))
        .filter((group) => group.forms.length > 0)
    },
  },

  actions: {
    async loadForms() {
      this.isLoading = true
      this.error = undefined
      try {
        const [forms, authorities] = await Promise.all([
          governmentFormService.getForms(),
          governmentFormService.getAuthorities(),
        ])
        this.forms = forms
        this.authorities = authorities
      } catch {
        this.error = 'Unable to load government forms. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    setSearchTerm(term: string) {
      this.searchTerm = term
    },

    setAuthorityFilter(authorityId: string | 'All') {
      this.authorityFilter = authorityId
    },

    setCategoryFilter(category: GovernmentFormCategory | 'All') {
      this.categoryFilter = category
    },

    setViewMode(mode: GovernmentFormViewMode) {
      this.viewMode = mode
    },

    clearFilters() {
      this.searchTerm = ''
      this.authorityFilter = 'All'
      this.categoryFilter = 'All'
    },
  },
})
