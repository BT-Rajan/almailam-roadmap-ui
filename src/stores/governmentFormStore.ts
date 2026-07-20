import { defineStore } from 'pinia'

import { governmentFormService } from '@/services/governmentFormService'
import type { AuthorityInput, FormInput } from '@/services/governmentFormService'
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

    async createForm(input: FormInput): Promise<GovernmentForm> {
      const form = await governmentFormService.createForm(input)
      this.forms = [...this.forms, form]
      return form
    },

    async updateForm(formId: string, input: FormInput): Promise<GovernmentForm> {
      const form = await governmentFormService.updateForm(formId, input)
      this.forms = this.forms.map((existing) => (existing.id === formId ? form : existing))
      return form
    },

    async deleteForm(formId: string): Promise<void> {
      await governmentFormService.deleteForm(formId)
      this.forms = this.forms.filter((form) => form.id !== formId)
    },

    async archiveForm(formId: string): Promise<GovernmentForm> {
      const form = await governmentFormService.setFormStatus(formId, 'Archived')
      this.forms = this.forms.map((existing) => (existing.id === formId ? form : existing))
      return form
    },

    async restoreForm(formId: string): Promise<GovernmentForm> {
      const form = await governmentFormService.setFormStatus(formId, 'Active')
      this.forms = this.forms.map((existing) => (existing.id === formId ? form : existing))
      return form
    },

    async createAuthority(input: AuthorityInput): Promise<GovernmentAuthority> {
      const authority = await governmentFormService.createAuthority(input)
      this.authorities = [...this.authorities, authority]
      return authority
    },

    async updateAuthority(authorityId: string, input: AuthorityInput): Promise<GovernmentAuthority> {
      const authority = await governmentFormService.updateAuthority(authorityId, input)
      this.authorities = this.authorities.map((existing) => (existing.id === authorityId ? authority : existing))
      return authority
    },

    async deleteAuthority(authorityId: string): Promise<void> {
      await governmentFormService.deleteAuthority(authorityId)
      this.authorities = this.authorities.filter((authority) => authority.id !== authorityId)
      this.forms = this.forms.filter((form) => form.authorityId !== authorityId)
      if (this.authorityFilter === authorityId) this.authorityFilter = 'All'
    },
  },
})
