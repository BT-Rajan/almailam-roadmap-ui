<script setup lang="ts" generic="T extends Record<string, unknown>">
import { ChevronDown, ChevronUp, ChevronsUpDown, Download, X } from '@lucide/vue'
import { computed, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import IconButton from '@/components/common/IconButton.vue'
import SearchBox from '@/components/common/SearchBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import { usePagination } from '@/composables/usePagination'
import type { ColumnAlign, SmartTableColumn, SortDirection } from '@/types/Table'

const props = withDefaults(
  defineProps<{
    columns: SmartTableColumn<T>[]
    rows: T[]
    rowKey: keyof T & string
    loading?: boolean
    error?: string
    searchable?: boolean
    searchPlaceholder?: string
    searchKeys?: (keyof T & string)[]
    selectable?: boolean
    exportable?: boolean
    pageSize?: number
    emptyTitle?: string
    emptyDescription?: string
  }>(),
  {
    loading: false,
    error: undefined,
    searchable: true,
    searchPlaceholder: 'Search',
    searchKeys: undefined,
    selectable: false,
    exportable: false,
    pageSize: 10,
    emptyTitle: 'No records found',
    emptyDescription: 'There is nothing to display yet.',
  },
)

const emit = defineEmits<{
  'row-click': [row: T]
  'selection-change': [rows: T[]]
  export: [rows: T[]]
  retry: []
}>()

const searchTerm = ref('')
const sortKey = ref<(keyof T & string) | null>(null)
const sortDirection = ref<SortDirection>('asc')
const selectedKeys = ref<Set<unknown>>(new Set())

const alignClasses: Record<ColumnAlign, string> = {
  left: 'text-left',
  center: 'text-center',
  right: 'text-right',
}

const searchedRows = computed(() => {
  if (!props.searchable || !searchTerm.value.trim()) return props.rows

  const term = searchTerm.value.trim().toLowerCase()
  const keys = props.searchKeys ?? props.columns.map((column) => column.key)

  return props.rows.filter((row) =>
    keys.some((key) => String(row[key] ?? '').toLowerCase().includes(term)),
  )
})

function compareValues(valueA: unknown, valueB: unknown): number {
  if (typeof valueA === 'number' && typeof valueB === 'number') return valueA - valueB
  return String(valueA ?? '').localeCompare(String(valueB ?? ''))
}

const sortedRows = computed(() => {
  if (!sortKey.value) return searchedRows.value

  const key = sortKey.value
  const direction = sortDirection.value === 'asc' ? 1 : -1

  return [...searchedRows.value].sort((a, b) => direction * compareValues(a[key], b[key]))
})

const { currentPage, pageSize, totalItems, totalPages, startIndex, endIndex, goToPage, setPageSize, resetPage } =
  usePagination(() => sortedRows.value.length, props.pageSize)

const paginatedRows = computed(() => sortedRows.value.slice(startIndex.value, endIndex.value))
const isEmpty = computed(() => !props.loading && !props.error && sortedRows.value.length === 0)
const selectedCount = computed(() => selectedKeys.value.size)
const isAllSelected = computed(
  () =>
    paginatedRows.value.length > 0 &&
    paginatedRows.value.every((row) => selectedKeys.value.has(row[props.rowKey])),
)

watch(searchTerm, () => resetPage())
watch(() => props.rows, () => resetPage())

function alignClass(align?: ColumnAlign): string {
  return alignClasses[align ?? 'left']
}

function handleSort(column: SmartTableColumn<T>): void {
  if (!column.sortable) return

  if (sortKey.value === column.key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = column.key
    sortDirection.value = 'asc'
  }
}

function sortIcon(column: SmartTableColumn<T>) {
  if (sortKey.value !== column.key) return ChevronsUpDown
  return sortDirection.value === 'asc' ? ChevronUp : ChevronDown
}

function emitSelectionChange(): void {
  const selected = props.rows.filter((row) => selectedKeys.value.has(row[props.rowKey]))
  emit('selection-change', selected)
}

function toggleRow(row: T): void {
  const key = row[props.rowKey]
  if (selectedKeys.value.has(key)) {
    selectedKeys.value.delete(key)
  } else {
    selectedKeys.value.add(key)
  }
  emitSelectionChange()
}

function toggleAllRows(): void {
  if (isAllSelected.value) {
    paginatedRows.value.forEach((row) => selectedKeys.value.delete(row[props.rowKey]))
  } else {
    paginatedRows.value.forEach((row) => selectedKeys.value.add(row[props.rowKey]))
  }
  emitSelectionChange()
}

function clearSelection(): void {
  selectedKeys.value.clear()
  emitSelectionChange()
}
</script>

<template>
  <div class="overflow-hidden rounded-xl border border-border-light bg-bg-card shadow-soft">
    <div
      v-if="selectable && selectedCount > 0"
      class="flex items-center justify-between gap-3 border-b border-border-light bg-bg-selected px-4 py-3"
    >
      <p class="text-sm font-medium text-primary-700">{{ selectedCount }} selected</p>
      <div class="flex items-center gap-2">
        <slot name="bulk-actions" :rows="rows.filter((row) => selectedKeys.has(row[rowKey]))" />
        <IconButton :icon="X" label="Clear selection" size="sm" @click="clearSelection" />
      </div>
    </div>

    <div
      v-else
      class="flex flex-col gap-3 border-b border-border-light px-4 py-3 tablet:flex-row tablet:items-center"
    >
      <div v-if="searchable" class="w-full tablet:max-w-xs">
        <SearchBox v-model="searchTerm" :placeholder="searchPlaceholder" />
      </div>
      <slot name="filters" />
      <div class="flex-1" />
      <BaseButton
        v-if="exportable"
        variant="secondary"
        size="sm"
        :icon="Download"
        @click="emit('export', sortedRows)"
      >
        Export
      </BaseButton>
    </div>

    <ErrorState v-if="error" :description="error" @retry="emit('retry')" />

    <EmptyState v-else-if="isEmpty" :title="emptyTitle" :description="emptyDescription" />

    <div v-else class="overflow-x-auto">
      <table class="w-full border-collapse">
        <thead>
          <tr class="border-b border-border-light bg-bg-secondary">
            <th v-if="selectable" class="w-10 px-4 py-3">
              <input
                type="checkbox"
                class="h-4 w-4 rounded border-border-default text-primary-600 focus:ring-2 focus:ring-primary-500/30"
                :checked="isAllSelected"
                aria-label="Select all rows on this page"
                @change="toggleAllRows"
              />
            </th>
            <th
              v-for="column in columns"
              :key="column.key"
              class="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-neutral-500"
              :class="alignClass(column.align)"
              :style="column.width ? { width: column.width } : undefined"
            >
              <button
                v-if="column.sortable"
                type="button"
                class="inline-flex items-center gap-1 hover:text-neutral-700"
                @click="handleSort(column)"
              >
                {{ column.label }}
                <component :is="sortIcon(column)" class="h-3.5 w-3.5" />
              </button>
              <span v-else>{{ column.label }}</span>
            </th>
            <th v-if="$slots['row-actions']" class="w-10 px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="row in pageSize" :key="row" class="border-b border-border-light last:border-0">
              <td v-if="selectable" class="px-4 py-3" />
              <td v-for="column in columns" :key="column.key" class="px-4 py-3">
                <SkeletonLoader />
              </td>
              <td v-if="$slots['row-actions']" class="px-4 py-3" />
            </tr>
          </template>
          <tr
            v-for="row in paginatedRows"
            v-else
            :key="String(row[rowKey])"
            class="cursor-pointer border-b border-border-light last:border-0 hover:bg-bg-hover"
            @click="emit('row-click', row)"
          >
            <td v-if="selectable" class="px-4 py-3" @click.stop>
              <input
                type="checkbox"
                class="h-4 w-4 rounded border-border-default text-primary-600 focus:ring-2 focus:ring-primary-500/30"
                :checked="selectedKeys.has(row[rowKey])"
                :aria-label="`Select row ${String(row[rowKey])}`"
                @change="toggleRow(row)"
              />
            </td>
            <td
              v-for="column in columns"
              :key="column.key"
              class="px-4 py-3 text-sm text-neutral-700"
              :class="alignClass(column.align)"
            >
              <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">
                {{ row[column.key] }}
              </slot>
            </td>
            <td v-if="$slots['row-actions']" class="px-4 py-3 text-right" @click.stop>
              <slot name="row-actions" :row="row" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <TablePagination
      v-if="!isEmpty && !error"
      :current-page="currentPage"
      :total-pages="totalPages"
      :total-items="totalItems"
      :start-index="startIndex"
      :end-index="endIndex"
      :page-size="pageSize"
      @page-change="goToPage"
      @page-size-change="setPageSize"
    />
  </div>
</template>
