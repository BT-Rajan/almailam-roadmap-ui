import { defineStore } from 'pinia'

import { governmentFormService } from '@/services/governmentFormService'
import { governmentSubmissionService } from '@/services/governmentSubmissionService'
import type { SubmissionCreateInput } from '@/services/governmentSubmissionService'
import { projectService } from '@/services/projectService'
import type { GovernmentAuthority, GovernmentForm } from '@/types/Government'
import type { Project } from '@/types/Project'
import type { GovernmentSubmission, SubmissionStatus } from '@/types/Submission'

interface GovernmentSubmissionStoreState {
  submissions: GovernmentSubmission[]
  projects: Project[]
  authorities: GovernmentAuthority[]
  forms: GovernmentForm[]
  isLoading: boolean
  error: string | undefined
  searchTerm: string
  statusFilter: SubmissionStatus | 'All'
  authorityFilter: string | 'All'
  isMutating: boolean
  mutationError: string | undefined
}

export const useGovernmentSubmissionStore = defineStore('governmentSubmission', {
  state: (): GovernmentSubmissionStoreState => ({
    submissions: [],
    projects: [],
    authorities: [],
    forms: [],
    isLoading: false,
    error: undefined,
    searchTerm: '',
    statusFilter: 'All',
    authorityFilter: 'All',
    isMutating: false,
    mutationError: undefined,
  }),

  getters: {
    filteredSubmissions(state): GovernmentSubmission[] {
      const term = state.searchTerm.trim().toLowerCase()

      return state.submissions.filter((submission) => {
        const project = state.projects.find((item) => item.id === submission.projectId)
        const matchesSearch =
          term.length === 0 ||
          submission.submissionNo.toLowerCase().includes(term) ||
          (project?.projectName.toLowerCase().includes(term) ?? false)

        const matchesStatus = state.statusFilter === 'All' || submission.status === state.statusFilter
        const matchesAuthority = state.authorityFilter === 'All' || submission.authorityId === state.authorityFilter

        return matchesSearch && matchesStatus && matchesAuthority
      })
    },

    hasActiveFilters(state): boolean {
      return state.searchTerm.trim().length > 0 || state.statusFilter !== 'All' || state.authorityFilter !== 'All'
    },

    getProjectById(state) {
      return (projectId: string): Project | undefined => state.projects.find((project) => project.id === projectId)
    },

    getAuthorityById(state) {
      return (authorityId: string): GovernmentAuthority | undefined =>
        state.authorities.find((authority) => authority.id === authorityId)
    },

    getFormById(state) {
      return (formId: string): GovernmentForm | undefined => state.forms.find((form) => form.id === formId)
    },

    submissionsByProject(state) {
      return (projectId: string): GovernmentSubmission[] =>
        state.submissions.filter((submission) => submission.projectId === projectId)
    },
  },

  actions: {
    async loadSubmissions() {
      this.isLoading = true
      this.error = undefined
      try {
        const [submissions, projects, authorities, forms] = await Promise.all([
          governmentSubmissionService.getSubmissions(),
          projectService.getProjects(),
          governmentFormService.getAuthorities(),
          governmentFormService.getForms(),
        ])
        this.submissions = submissions
        this.projects = projects
        this.authorities = authorities
        this.forms = forms
      } catch {
        this.error = 'Unable to load government submissions. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    setSearchTerm(term: string) {
      this.searchTerm = term
    },

    setStatusFilter(status: SubmissionStatus | 'All') {
      this.statusFilter = status
    },

    setAuthorityFilter(authorityId: string | 'All') {
      this.authorityFilter = authorityId
    },

    clearFilters() {
      this.searchTerm = ''
      this.statusFilter = 'All'
      this.authorityFilter = 'All'
    },

    // Moves a submission to a new status (e.g. Withdrawn) via the real
    // state-machine-enforced backend endpoint. Returns true on success so
    // callers can react (close a dialog, show a toast) without needing to
    // inspect store state.
    async setSubmissionStatus(submissionId: string, status: SubmissionStatus, reason?: string): Promise<boolean> {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const updated = await governmentSubmissionService.setSubmissionStatus(submissionId, status, reason)
        this.submissions = this.submissions.map((submission) =>
          submission.id === submissionId ? updated : submission,
        )
        return true
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to update the submission status.'
        return false
      } finally {
        this.isMutating = false
      }
    },

    async createSubmission(input: SubmissionCreateInput): Promise<GovernmentSubmission> {
      const submission = await governmentSubmissionService.createSubmission(input)
      this.submissions = [submission, ...this.submissions]
      return submission
    },
  },
})
