import { defineStore } from 'pinia'

import { RequestCancelledError } from '@/services/httpClient'
import { searchService } from '@/services/searchService'
import type { SearchResult, SearchResultCategory, SearchResultGroup } from '@/types/Search'

// Below this, a term is too unselective to be worth a network round trip --
// mirrors MIN_TERM_LENGTH in the backend's search_service.py, which refuses
// it too. Kept here as the primary gate so the request is never sent in the
// first place, not just rejected after the fact.
export const MIN_QUERY_LENGTH = 2

// Cancels whatever search is currently in flight, if any -- module-level
// rather than store state, since an AbortController isn't the kind of thing
// that belongs in a reactive/serializable Pinia state object (same reasoning
// as the load-gate registry in utils/loadGate.ts).
let inFlightSearch: AbortController | undefined

interface SearchStoreState {
  isOpen: boolean
  query: string
  results: SearchResult[]
  isLoading: boolean
  activeIndex: number
  requestId: number
}

const CATEGORY_ORDER: SearchResultCategory[] = [
  'Client',
  'Project',
  'Document',
  'Form',
  'Task',
  'Contract',
  'Quotation',
  'Submission',
  'Payment',
  'User',
]

export const useSearchStore = defineStore('search', {
  state: (): SearchStoreState => ({
    isOpen: false,
    query: '',
    results: [],
    isLoading: false,
    activeIndex: 0,
    requestId: 0,
  }),

  getters: {
    hasQuery(state): boolean {
      return state.query.trim().length > 0
    },

    // True while there's text but not yet enough to have searched --
    // distinct from "hasQuery but genuinely no results" so the palette can
    // show "keep typing" instead of a misleading "no results for X".
    needsMoreCharacters(state): boolean {
      const length = state.query.trim().length
      return length > 0 && length < MIN_QUERY_LENGTH
    },

    groupedResults(state): SearchResultGroup[] {
      return CATEGORY_ORDER.map((category) => ({
        category,
        results: state.results.filter((result) => result.category === category),
      })).filter((group) => group.results.length > 0)
    },

    flatResults(state): SearchResult[] {
      return CATEGORY_ORDER.flatMap((category) => state.results.filter((result) => result.category === category))
    },

    activeResult(): SearchResult | undefined {
      return this.flatResults[this.activeIndex]
    },
  },

  actions: {
    open() {
      this.isOpen = true
      this.activeIndex = 0
    },

    close() {
      inFlightSearch?.abort()
      this.isOpen = false
      this.query = ''
      this.results = []
      this.activeIndex = 0
    },

    toggle() {
      if (this.isOpen) {
        this.close()
      } else {
        this.open()
      }
    },

    async setQuery(query: string) {
      this.query = query
      this.activeIndex = 0

      // A new query always supersedes whatever's in flight, whether or not
      // this one ends up short enough to skip its own request -- there's no
      // reason to let an older, now-irrelevant search keep running on the
      // server.
      inFlightSearch?.abort()

      const term = query.trim()
      if (term.length < MIN_QUERY_LENGTH) {
        this.requestId += 1
        this.results = []
        this.isLoading = false
        return
      }

      this.requestId += 1
      const currentRequest = this.requestId
      this.isLoading = true
      const controller = new AbortController()
      inFlightSearch = controller
      try {
        const results = await searchService.search(term, controller.signal)
        if (currentRequest === this.requestId) {
          this.results = results
        }
      } catch (error) {
        // A cancellation means a newer setQuery() call already took over --
        // that call owns isLoading/results now, so there is nothing to do
        // here. Anything else is a genuine failure; log it rather than leave
        // an unhandled rejection (setQuery's callers fire-and-forget it).
        if (!(error instanceof RequestCancelledError)) {
          console.error('Search failed:', error)
        }
      } finally {
        if (currentRequest === this.requestId) {
          this.isLoading = false
        }
        if (inFlightSearch === controller) {
          inFlightSearch = undefined
        }
      }
    },

    moveActive(delta: number) {
      const total = this.flatResults.length
      if (total === 0) return
      this.activeIndex = (this.activeIndex + delta + total) % total
    },

    setActiveIndex(index: number) {
      this.activeIndex = index
    },
  },
})
