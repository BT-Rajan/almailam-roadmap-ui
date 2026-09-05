<script setup lang="ts">
import { Check, Minus } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import Checkbox from '@/components/common/Checkbox.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import type { RolePermission } from '@/types/Role'
import type { SmartTableColumn } from '@/types/Table'

interface PermissionRow extends RolePermission {
  [key: string]: unknown
}

interface Props {
  permissions: RolePermission[]
  editable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  editable: false,
})

const emit = defineEmits<{
  'update:permissions': [permissions: RolePermission[]]
}>()

const { t } = useI18n()

const rows = computed<PermissionRow[]>(() => props.permissions as PermissionRow[])

const COLUMNS = computed<SmartTableColumn<PermissionRow>[]>(() => [
  { key: 'module', label: t('administration.permissionMatrix.module') },
  { key: 'view', label: t('administration.permissionMatrix.view'), align: 'center', width: '90px' },
  { key: 'edit', label: t('administration.permissionMatrix.edit'), align: 'center', width: '90px' },
  { key: 'delete', label: t('administration.permissionMatrix.delete'), align: 'center', width: '90px' },
])

function toggle(module: string, field: 'view' | 'edit' | 'delete'): void {
  emit(
    'update:permissions',
    props.permissions.map((permission) =>
      permission.module === module ? { ...permission, [field]: !permission[field] } : permission,
    ),
  )
}
</script>

<template>
  <SmartTable
    :columns="COLUMNS"
    :rows="rows"
    row-key="module"
    :searchable="false"
    :empty-title="t('administration.permissionMatrix.noPermissionsDefined')"
  >
    <template #cell-view="{ value, row }">
      <Checkbox v-if="editable" :model-value="Boolean(value)" @update:model-value="toggle(row.module as string, 'view')" />
      <template v-else>
        <Check v-if="value" :size="15" class="mx-auto text-success-600" />
        <Minus v-else :size="15" class="mx-auto text-text-muted" />
      </template>
    </template>
    <template #cell-edit="{ value, row }">
      <Checkbox v-if="editable" :model-value="Boolean(value)" @update:model-value="toggle(row.module as string, 'edit')" />
      <template v-else>
        <Check v-if="value" :size="15" class="mx-auto text-success-600" />
        <Minus v-else :size="15" class="mx-auto text-text-muted" />
      </template>
    </template>
    <template #cell-delete="{ value, row }">
      <Checkbox v-if="editable" :model-value="Boolean(value)" @update:model-value="toggle(row.module as string, 'delete')" />
      <template v-else>
        <Check v-if="value" :size="15" class="mx-auto text-success-600" />
        <Minus v-else :size="15" class="mx-auto text-text-muted" />
      </template>
    </template>
  </SmartTable>
</template>
