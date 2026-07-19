<script setup lang="ts">
import { FileText, FolderKanban, Landmark, ListChecks, User } from '@lucide/vue'
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import Loader from '@/components/common/Loader.vue'
import SearchBox from '@/components/common/SearchBox.vue'
import { useSearchStore } from '@/stores/searchStore'
import type { SearchResult, SearchResultCategory } from '@/types/Search'

const searchStore = useSearchStore()
const router = useRouter()
const paletteRef = ref<HTMLDivElement>()

const CATEGORY_LABELS: Record<SearchResultCategory, string> = {
  Project: 'Projects',
  Document: 'Documents',
  Form: 'Forms',
  Task: 'Tasks',
  User: 'Users',
}

const CATEGORY_ICONS: Record<SearchResultCategory, typeof FolderKanban> = {
  Project: FolderKanban,
  Document: FileText,
  Form: Landmark,
  Task: ListChecks,
  User,
}

const flatIndexOf = (result: SearchResult): number => searchStore.flatResults.indexOf(result)

const selectResult = (result: SearchResult): void => {
  searchStore.close()
  router.push({ name: result.routeName, params: result.params })
}

const handleSearch = (value: string): void => {
  void searchStore.setQuery(value)
}

const handleKeydown = (event: KeyboardEvent): void => {
  const isShortcut = (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k'
  if (isShortcut) {
    event.preventDefault()
    searchStore.toggle()
    return
  }

  if (!searchStore.isOpen) return

  if (event.key === 'Escape') {
    searchStore.close()
  } else if (event.key === 'ArrowDown') {
    event.preventDefault()
    searchStore.moveActive(1)
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    searchStore.moveActive(-1)
  } else if (event.key === 'Enter' && searchStore.activeResult) {
    event.preventDefault()
    selectResult(searchStore.activeResult)
  }
}

window.addEventListener('keydown', handleKeydown)
onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
})

watch(
  () => searchStore.isOpen,
  (isOpen) => {
    document.body.classList.toggle('overflow-hidden', isOpen)
    if (isOpen) {
      void nextTick(() => {
        paletteRef.value?.querySelector('input')?.focus()
      })
    }
  },
)
</script>

<template>
  <Teleport to="body">
    <div v-if="searchStore.isOpen" class="fixed inset-0 z-modal flex items-start justify-center p-4 pt-24">
      <div class="absolute inset-0 bg-neutral-900/50" @click="searchStore.close" />

      <div ref="paletteRef" class="relative flex max-h-[70vh] w-full max-w-xl flex-col rounded-xl bg-bg-card shadow-elevated">
        <div class="border-b border-border-light p-3">
          <SearchBox
            :model-value="searchStore.query"
            placeholder="Search projects, documents, forms, tasks, users..."
            :debounce-ms="200"
            @update:model-value="searchStore.query = $event"
            @search="handleSearch"
          />
        </div>

        <div class="flex-1 overflow-y-auto p-2">
          <Loader v-if="searchStore.isLoading" label="Searching..." />

          <p
            v-else-if="searchStore.hasQuery && searchStore.groupedResults.length === 0"
            class="px-3 py-8 text-center text-sm text-neutral-400"
          >
            No results for "{{ searchStore.query }}"
          </p>

          <p v-else-if="!searchStore.hasQuery" class="px-3 py-8 text-center text-sm text-neutral-400">
            Search across projects, documents, forms, tasks, and users.
          </p>

          <div v-else class="flex flex-col gap-3">
            <section v-for="group in searchStore.groupedResults" :key="group.category">
              <p class="mb-1 px-2 text-xs font-medium uppercase tracking-wide text-neutral-400">
                {{ CATEGORY_LABELS[group.category] }}
              </p>
              <div class="flex flex-col">
                <button
                  v-for="result in group.results"
                  :key="result.id"
                  type="button"
                  class="flex items-center gap-3 rounded-lg px-2 py-2 text-left transition-colors duration-fast"
                  :class="
                    flatIndexOf(result) === searchStore.activeIndex
                      ? 'bg-primary-50'
                      : 'hover:bg-bg-hover'
                  "
                  @mouseenter="searchStore.setActiveIndex(flatIndexOf(result))"
                  @click="selectResult(result)"
                >
                  <span
                    class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-bg-secondary text-neutral-500"
                  >
                    <component :is="CATEGORY_ICONS[result.category]" :size="15" />
                  </span>
                  <span class="min-w-0 flex-1">
                    <span class="block truncate text-sm font-medium text-neutral-800">{{ result.title }}</span>
                    <span class="block truncate text-xs text-neutral-400">{{ result.subtitle }}</span>
                  </span>
                </button>
              </div>
            </section>
          </div>
        </div>

        <div class="flex items-center justify-between gap-4 border-t border-border-light px-4 py-2.5">
          <span class="flex items-center gap-3 text-xs text-neutral-400">
            <span class="flex items-center gap-1">
              <kbd class="rounded border border-border-default bg-bg-secondary px-1.5 py-0.5 text-[10px] font-medium text-neutral-500">↑</kbd>
              <kbd class="rounded border border-border-default bg-bg-secondary px-1.5 py-0.5 text-[10px] font-medium text-neutral-500">↓</kbd>
              Navigate
            </span>
            <span class="flex items-center gap-1">
              <kbd class="rounded border border-border-default bg-bg-secondary px-1.5 py-0.5 text-[10px] font-medium text-neutral-500">↵</kbd>
              Select
            </span>
          </span>
          <span class="flex items-center gap-1 text-xs text-neutral-400">
            <kbd class="rounded border border-border-default bg-bg-secondary px-1.5 py-0.5 text-[10px] font-medium text-neutral-500">Esc</kbd>
            Close
          </span>
        </div>
      </div>
    </div>
  </Teleport>
</template>
