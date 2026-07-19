<script setup lang="ts">
import { LayoutGrid, TableProperties, Upload } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import IconButton from '@/components/common/IconButton.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import DocumentCard from '@/components/document/DocumentCard.vue'
import DocumentUploadDialog from '@/components/document/DocumentUploadDialog.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { usePagination } from '@/composables/usePagination'
import { useDocumentStore } from '@/stores/documentStore'
import { useToastStore } from '@/stores/toastStore'
import type { SmartTableColumn } from '@/types/Table'
import type { DocumentStatus, DocumentType, ProjectDocument } from '@/types/Document'
import type { SelectOption } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'
import { getDocumentStatusVariant } from '@/utils/documentHelpers'

interface DocumentTableRow {
  [key: string]: unknown
  id: string
  title: string
  type: DocumentType
  projectName: string
  revision: string
  uploadedBy: string
  uploadDate: string
  status: DocumentStatus
}

const router = useRouter()
const documentStore = useDocumentStore()
const toastStore = useToastStore()

const isUploadDialogOpen = ref(false)

const TYPE_OPTIONS: SelectOption[] = [
  { label: 'All Categories', value: 'All' },
  { label: 'Drawing', value: 'Drawing' },
  { label: 'Report', value: 'Report' },
  { label: 'Contract', value: 'Contract' },
  { label: 'Quotation', value: 'Quotation' },
  { label: 'Municipality Form', value: 'Municipality Form' },
  { label: 'Calculation Sheet', value: 'Calculation Sheet' },
]

const STATUS_OPTIONS: SelectOption[] = [
  { label: 'All Statuses', value: 'All' },
  { label: 'Draft', value: 'Draft' },
  { label: 'Under Review', value: 'Under Review' },
  { label: 'Approved', value: 'Approved' },
  { label: 'Rejected', value: 'Rejected' },
]

const TABLE_COLUMNS: SmartTableColumn<DocumentTableRow>[] = [
  { key: 'title', label: 'Document Title', sortable: true },
  { key: 'type', label: 'Category', sortable: true },
  { key: 'projectName', label: 'Project', sortable: true },
  { key: 'revision', label: 'Revision', sortable: true, width: '110px' },
  { key: 'uploadedBy', label: 'Uploaded By', sortable: true },
  { key: 'uploadDate', label: 'Upload Date', sortable: true, align: 'right' },
  { key: 'status', label: 'Status', sortable: true },
]

const tableRows = computed<DocumentTableRow[]>(() =>
  documentStore.filteredDocuments.map((document) => ({
    id: document.id,
    title: document.title,
    type: document.type,
    projectName: documentStore.getProjectById(document.projectId)?.projectName ?? 'Unknown Project',
    revision: document.revision,
    uploadedBy: document.uploadedBy,
    uploadDate: document.uploadDate,
    status: document.status,
  })),
)

const { currentPage, pageSize, totalItems, totalPages, startIndex, endIndex, goToPage, setPageSize } = usePagination(
  () => documentStore.filteredDocuments.length,
  9,
)

const paginatedGridDocuments = computed(() => documentStore.filteredDocuments.slice(startIndex.value, endIndex.value))

function loadData(): void {
  documentStore.loadDocuments()
}

onMounted(() => {
  if (documentStore.documents.length === 0) loadData()
})

function openDocument(documentId: string): void {
  router.push({ name: ROUTE_NAMES.DOCUMENT_VIEWER, params: { documentId } })
}

function handleUpload(document: ProjectDocument): void {
  documentStore.addDocument(document)
  toastStore.show('success', 'Document uploaded', `${document.title} was added to the repository.`)
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader title="Document Repository" subtitle="Browse, filter and manage every project document in one place.">
      <template #actions>
        <BaseButton :icon="Upload" @click="isUploadDialogOpen = true">Upload Document</BaseButton>
      </template>
    </PageHeader>

    <FilterBar
      :search-value="documentStore.searchTerm"
      search-placeholder="Search by document title or uploader"
      :has-active-filters="documentStore.hasActiveFilters"
      @update:search-value="documentStore.setSearchTerm"
      @clear="documentStore.clearFilters"
    >
      <template #filters>
        <div class="w-48">
          <SelectBox
            :model-value="documentStore.typeFilter"
            :options="TYPE_OPTIONS"
            @update:model-value="documentStore.setTypeFilter($event as DocumentType | 'All')"
          />
        </div>
        <div class="w-44">
          <SelectBox
            :model-value="documentStore.statusFilter"
            :options="STATUS_OPTIONS"
            @update:model-value="documentStore.setStatusFilter($event as DocumentStatus | 'All')"
          />
        </div>
      </template>
      <template #actions>
        <div class="flex items-center gap-1 rounded-lg border border-border-default p-1">
          <IconButton
            :icon="LayoutGrid"
            label="Grid view"
            size="sm"
            :variant="documentStore.viewMode === 'grid' ? 'primary' : 'ghost'"
            @click="documentStore.setViewMode('grid')"
          />
          <IconButton
            :icon="TableProperties"
            label="Table view"
            size="sm"
            :variant="documentStore.viewMode === 'table' ? 'primary' : 'ghost'"
            @click="documentStore.setViewMode('table')"
          />
        </div>
      </template>
    </FilterBar>

    <ErrorState v-if="documentStore.error" :description="documentStore.error" @retry="loadData" />

    <template v-else-if="documentStore.viewMode === 'grid'">
      <div v-if="documentStore.isLoading" class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
        <div v-for="placeholder in 6" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="5" />
        </div>
      </div>

      <EmptyState
        v-else-if="paginatedGridDocuments.length === 0"
        title="No documents found"
        description="Try adjusting your search or filters, or upload a new document."
        action-label="Upload Document"
        @action="isUploadDialogOpen = true"
      />

      <template v-else>
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
          <DocumentCard
            v-for="document in paginatedGridDocuments"
            :key="document.id"
            :document="document"
            :project="documentStore.getProjectById(document.projectId)"
            @open="openDocument"
          />
        </div>
        <div class="rounded-xl border border-border-light bg-bg-card">
          <TablePagination
            :current-page="currentPage"
            :total-pages="totalPages"
            :total-items="totalItems"
            :start-index="startIndex"
            :end-index="endIndex"
            :page-size="pageSize"
            :page-size-options="[9, 18, 27]"
            @page-change="goToPage"
            @page-size-change="setPageSize"
          />
        </div>
      </template>
    </template>

    <SmartTable
      v-else
      :columns="TABLE_COLUMNS"
      :rows="tableRows"
      row-key="id"
      :loading="documentStore.isLoading"
      :searchable="false"
      empty-title="No documents found"
      empty-description="Try adjusting your search or filters, or upload a new document."
      @row-click="openDocument($event.id)"
    >
      <template #cell-type="{ value }">
        <StatusBadge :label="value as string" variant="info" />
      </template>
      <template #cell-status="{ value }">
        <StatusBadge :label="value as string" :variant="getDocumentStatusVariant(value as DocumentStatus)" show-dot />
      </template>
      <template #cell-uploadDate="{ value }">
        {{ formatDate(value as string) }}
      </template>
    </SmartTable>

    <DocumentUploadDialog v-model="isUploadDialogOpen" :projects="documentStore.projects" @upload="handleUpload" />
  </div>
</template>
