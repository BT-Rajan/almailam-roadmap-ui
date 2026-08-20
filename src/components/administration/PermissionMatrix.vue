<script setup lang="ts">
import { Check, Minus } from '@lucide/vue'
import { computed } from 'vue'

import SmartTable from '@/components/common/SmartTable.vue'
import type { RolePermission } from '@/types/Role'
import type { SmartTableColumn } from '@/types/Table'

interface PermissionRow extends RolePermission {
  [key: string]: unknown
}

interface Props {
  permissions: RolePermission[]
}

const props = defineProps<Props>()
const rows = computed<PermissionRow[]>(() => props.permissions as PermissionRow[])

const COLUMNS: SmartTableColumn<PermissionRow>[] = [
  { key: 'module', label: 'Module' },
  { key: 'view', label: 'View', align: 'center', width: '90px' },
  { key: 'edit', label: 'Edit', align: 'center', width: '90px' },
  { key: 'delete', label: 'Delete', align: 'center', width: '90px' },
]
</script>

<template>
  <SmartTable
    :columns="COLUMNS"
    :rows="rows"
    row-key="module"
    :searchable="false"
    empty-title="No permissions defined"
  >
    <template #cell-view="{ value }">
      <Check v-if="value" :size="15" class="mx-auto text-success-600" />
      <Minus v-else :size="15" class="mx-auto text-text-muted" />
    </template>
    <template #cell-edit="{ value }">
      <Check v-if="value" :size="15" class="mx-auto text-success-600" />
      <Minus v-else :size="15" class="mx-auto text-text-muted" />
    </template>
    <template #cell-delete="{ value }">
      <Check v-if="value" :size="15" class="mx-auto text-success-600" />
      <Minus v-else :size="15" class="mx-auto text-text-muted" />
    </template>
  </SmartTable>
</template>
