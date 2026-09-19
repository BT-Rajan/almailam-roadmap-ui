import { defineStore } from 'pinia'

import { governmentFormService } from '@/services/governmentFormService'
import { governmentSubmissionService } from '@/services/governmentSubmissionService'
import type {
  AcknowledgementInput,
  CloseApplicationInput,
  FollowupCreateInput,
  SubmissionCreateInput,
  SubmissionUpdateInput,
} from '@/services/governmentSubmissionService'
import { useProjectStore } from '@/stores/projectStore'
import type { GovernmentAuthority, GovernmentForm } from '@/types/Government'
import type { Project } from '@/types/Project'
import type { GovernmentSubmission, SubmissionFollowup, SubmissionStage } from '@/types/Submission'

interface GovernmentSubmissionStoreState {
  submissions: GovernmentSubmission[]
  authorities: GovernmentAuthority[]
  forms: GovernmentForm[]
  isLoading: boolean
  error: string | undefined
  searchTerm: string
  stageFilter: SubmissionStage | 'All'
  authorityFilter: string | 'All'
  isMutating: boolean
  mutationError: string | undefined
  followups: SubmissionFollowup[]
  isFollowupsLoading: boolean
}

export const useGovernmentSubmissionStore = defineStore('governmentSubmission', {
  state: (): GovernmentSubmissionStoreState => ({
    submissions: [],
    authorities: [],
    forms: [],
    isLoading: false,
    error: undefined,
    searchTerm: '',
    stageFilter: 'All',
    authorityFilter: 'All',
    isMutating: false,
    mutationError: undefined,
    followups: [],
    isFollowupsLoading: false,
  }),

  getters: {
    filteredSubmissions(state): GovernmentSubmission[] {
      const term = state.searchTerm.trim().toLowerCase()
      const projectStore = useProjectStore()

      return state.submissions.filter((submission) => {
        const project = projectStore.getProjectById(submission.projectId)
        const matchesSearch =
          term.length === 0 ||
          submission.submissionNo.toLowerCase().includes(term) ||
          (project?.projectName.toLowerCase().includes(term) ?? false)

        const matchesStage = state.stageFilter === 'All' || submission.stage === state.stageFilter
        const matchesAuthority = state.authorityFilter === 'All' || submission.authorityId === state.authorityFilter

        return matchesSearch && matchesStage && matchesAuthority
      })
    },

    hasActiveFilters(state): boolean {
      return state.searchTerm.trim().length > 0 || state.stageFilter !== 'All' || state.authorityFilter !== 'All'
    },

    // projectStore is the single, canonical place the full project list
    // lives -- see projectStore's own comment on `clients` for why this
    // delegates rather than keeping (and independently fetching) a
    // second copy.
    projects(): Project[] {
      return useProjectStore().projects
    },

    getProjectById(): (projectId: string) => Project | undefined {
      return (projectId: string) => useProjectStore().getProjectById(projectId)
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

    getSubmissionByNo(state) {
      return (submissionNo: string): GovernmentSubmission | undefined =>
        state.submissions.find((submission) => submission.submissionNo === submissionNo)
    },
  },

  actions: {
    async loadSubmissions() {
      this.isLoading = true
      this.error = undefined
      try {
        const projectStore = useProjectStore()
        const [submissions, , authorities, forms] = await Promise.all([
          governmentSubmissionService.getSubmissions(),
          projectStore.projects.length === 0 ? projectStore.loadProjects() : Promise.resolve(),
          governmentFormService.getAuthorities(),
          governmentFormService.getForms(),
        ])
        this.submissions = submissions
        this.authorities = authorities
        this.forms = forms
      } catch {
        this.error = 'Unable to load permit applications. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    setSearchTerm(term: string) {
      this.searchTerm = term
    },

    setStageFilter(stage: SubmissionStage | 'All') {
      this.stageFilter = stage
    },

    setAuthorityFilter(authorityId: string | 'All') {
      this.authorityFilter = authorityId
    },

    clearFilters() {
      this.searchTerm = ''
      this.stageFilter = 'All'
      this.authorityFilter = 'All'
    },

    async createSubmission(input: SubmissionCreateInput): Promise<GovernmentSubmission> {
      const submission = await governmentSubmissionService.createSubmission(input)
      this.submissions = [submission, ...this.submissions]
      return submission
    },

    async updateSubmission(submissionNo: string, input: SubmissionUpdateInput): Promise<GovernmentSubmission> {
      const updated = await governmentSubmissionService.updateSubmission(submissionNo, input)
      this._replaceSubmission(updated)
      return updated
    },

    async deleteSubmission(submissionNo: string): Promise<void> {
      await governmentSubmissionService.deleteSubmission(submissionNo)
      this.submissions = this.submissions.filter((submission) => submission.submissionNo !== submissionNo)
    },

    // Loads a single submission by number into the store's list, for the
    // full-screen workspace page (deep link / refresh, where the list may
    // not be populated yet).
    async loadSubmissionByNo(submissionNo: string): Promise<GovernmentSubmission | undefined> {
      if (!this.getSubmissionByNo(submissionNo)) {
        await this.loadSubmissions()
      }
      return this.getSubmissionByNo(submissionNo)
    },

    _replaceSubmission(updated: GovernmentSubmission) {
      this.submissions = this.submissions.map((submission) =>
        submission.submissionNo === updated.submissionNo ? updated : submission,
      )
    },

    async uploadDocument(submissionId: string, documentId: number, file: File): Promise<boolean> {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const updated = await governmentSubmissionService.uploadDocument(submissionId, documentId, file)
        this._replaceSubmission(updated)
        return true
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to upload the document.'
        return false
      } finally {
        this.isMutating = false
      }
    },

    // Prepare -> Apply.
    async confirmReadiness(submissionId: string): Promise<boolean> {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const updated = await governmentSubmissionService.confirmReadiness(submissionId)
        this._replaceSubmission(updated)
        return true
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to confirm readiness.'
        return false
      } finally {
        this.isMutating = false
      }
    },

    // Apply -> Track.
    async recordAcknowledgement(submissionId: string, input: AcknowledgementInput): Promise<boolean> {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const updated = await governmentSubmissionService.recordAcknowledgement(submissionId, input)
        this._replaceSubmission(updated)
        return true
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to record the acknowledgement.'
        return false
      } finally {
        this.isMutating = false
      }
    },

    async loadFollowups(submissionId: string) {
      this.isFollowupsLoading = true
      try {
        this.followups = await governmentSubmissionService.getFollowups(submissionId)
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to load follow-ups.'
      } finally {
        this.isFollowupsLoading = false
      }
    },

    // Logs contact with the authority (Track) or one that also carries a
    // document (Update) -- moves the application's stage to match.
    async addFollowup(submissionId: string, input: FollowupCreateInput): Promise<boolean> {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const followup = await governmentSubmissionService.addFollowup(submissionId, input)
        this.followups = [followup, ...this.followups]
        // Recording contact moves the application's own stage to match
        // (Track/Update) -- refresh so the workspace's header/stepper
        // reflects it.
        const updated = await governmentSubmissionService.getSubmission(submissionId)
        this._replaceSubmission(updated)
        return true
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to record the follow-up.'
        return false
      } finally {
        this.isMutating = false
      }
    },

    // -> Close, reachable from any stage.
    async closeApplication(submissionId: string, input: CloseApplicationInput): Promise<boolean> {
      this.isMutating = true
      this.mutationError = undefined
      try {
        const updated = await governmentSubmissionService.closeApplication(submissionId, input)
        this._replaceSubmission(updated)
        return true
      } catch (error) {
        this.mutationError = error instanceof Error ? error.message : 'Unable to close the application.'
        return false
      } finally {
        this.isMutating = false
      }
    },
  },
})
