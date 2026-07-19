import { defineStore } from 'pinia'

import { searchService } from '@/services/searchService'
import type { SearchResult, SearchResultCategory, SearchResultGroup } from '@/types/Search'

interface SearchStoreState {
  isOpen: boolean
  query: string
  results: SearchResult[]
  isLoading: boolean
  activeIndex: number
  requestId: number
}

const CATEGORY_ORDER: SearchResultCategory[] = ['Project', 'Document', 'Form', 'Task', 'User']

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

      const term = query.trim()
      if (term.length === 0) {
        this.results = []
        this.isLoading = false
        return
      }

      this.requestId += 1
      const currentRequest = this.requestId
      this.isLoading = true
      try {
        const results = await searchService.search(term)
        if (currentRequest === this.requestId) {
          this.results = results
        }
      } finally {
        if (currentRequest === this.requestId) {
          this.isLoading = false
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
