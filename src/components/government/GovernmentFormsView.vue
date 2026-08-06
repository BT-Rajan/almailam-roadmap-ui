<script setup lang="ts">
import { Pencil, Trash2 } from '@lucide/vue'
import { computed } from 'vue'

import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import GovernmentFormCard from '@/components/government/GovernmentFormCard.vue'
import type { GovernmentAuthority, GovernmentForm, GovernmentFormCategory } from '@/types/Government'
import type { SmartTableColumn } from '@/types/Table'
import { formatDate } from '@/utils/dateFormatter'
import { getFormCategoryVariant } from '@/utils/governmentFormHelpers'

interface GovernmentFormTableRow {
  [key: string]: unknown
  id: string
  formCode: string
  title: string
  category: GovernmentFormCategory
  language: string
  version: string
  lastUpdated: string
  status: string
}

const props = defineProps<{
  forms: GovernmentForm[]
  authority: GovernmentAuthority
  viewMode: 'grid' | 'table'
}>()

const emit = defineEmits<{
  view: [form: GovernmentForm]
  aiHelp: [form: GovernmentForm]
  edit: [form: GovernmentForm]
  archive: [form: GovernmentForm]
  restore: [form: GovernmentForm]
  addForm: []
}>()

const TABLE_COLUMNS: SmartTableColumn<GovernmentFormTableRow>[] = [
  { key: 'formCode', label: 'Form Code', sortable: true, width: '130px' },
  { key: 'title', label: 'Form Title', sortable: true },
  { key: 'category', label: 'Category', sortable: true },
  { key: 'language', label: 'Language', sortable: true },
  { key: 'version', label: 'Version', sortable: true, width: '100px' },
  { key: 'status', label: 'Status', sortable: true, width: '100px' },
  { key: 'lastUpdated', label: 'Last Updated', sortable: true, align: 'right' },
]

const tableRows = computed<GovernmentFormTableRow[]>(() =>
  props.forms.map((form) => ({
    id: form.id,
    formCode: form.formCode,
    title: form.title,
    category: form.category,
    language: form.language,
    version: form.version,
    status: form.status,
    lastUpdated: form.lastUpdated,
  })),
)

function formById(formId: string): GovernmentForm | undefined {
  return props.forms.find((form) => form.id === formId)
}
</script>

<template>
  <template v-if="viewMode === 'grid'">
    <EmptyState
      v-if="forms.length === 0"
      title="No forms found"
      description="Try adjusting your search or filters, or add a form to this authority."
      action-label="Add Form"
      @action="emit('addForm')"
    />
    <div v-else class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
      <GovernmentFormCard
        v-for="form in forms"
        :key="form.id"
        :form="form"
        :authority="authority"
        @view="emit('view', form)"
        @ai-help="emit('aiHelp', form)"
        @edit="emit('edit', form)"
        @archive="emit('archive', form)"
        @restore="emit('restore', form)"
      />
    </div>
  </template>

  <SmartTable
    v-else
    :columns="TABLE_COLUMNS"
    :rows="tableRows"
    row-key="id"
    :searchable="false"
    empty-title="No forms found"
    empty-description="Try adjusting your search or filters, or add a form to this authority."
    @row-click="(row) => formById(row.id) && emit('view', formById(row.id)!)"
  >
    <template #cell-category="{ value }">
      <StatusBadge :label="value as string" :variant="getFormCategoryVariant(value as GovernmentFormCategory)" />
    </template>
    <template #cell-status="{ value }">
      <StatusBadge :label="value as string" :variant="value === 'Archived' ? 'neutral' : 'success'" />
    </template>
    <template #cell-lastUpdated="{ value }">
      {{ formatDate(value as string) }}
    </template>
    <template #row-actions="{ row }">
      <div class="flex items-center justify-end gap-1" @click.stop>
        <IconButton
          :icon="Pencil"
          label="Edit form"
          size="sm"
          variant="ghost"
          @click="formById(row.id) && emit('edit', formById(row.id)!)"
        />
        <IconButton
          :icon="Trash2"
          label="Archive form"
          size="sm"
          variant="ghost"
          @click="formById(row.id) && emit('archive', formById(row.id)!)"
        />
      </div>
    </template>
  </SmartTable>
</template>
