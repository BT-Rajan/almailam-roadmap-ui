<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import PermitCatalogListEditor from '@/components/administration/PermitCatalogListEditor.vue'
import { usePermitCatalogStore } from '@/stores/permitCatalogStore'
import { useServiceCatalogStore } from '@/stores/serviceCatalogStore'
import { useToastStore } from '@/stores/toastStore'
import type { SelectOption } from '@/types/Ui'

const permitCatalogStore = usePermitCatalogStore()
const serviceCatalogStore = useServiceCatalogStore()
const toastStore = useToastStore()
const { t } = useI18n()

// Every Design-branch activity, flat, for the "eligible once these are
// Complete" prerequisite picker (see PermitPrerequisite) -- Permits
// only ever gate on Design work, never Supervision.
const designActivityOptions = computed<SelectOption[]>(() =>
  serviceCatalogStore.services
    .filter((service) => service.branch === 'Design')
    .flatMap((service) =>
      service.activities.map((activity) => ({
        label: `${service.name} — ${activity.name}`,
        value: activity.id,
      })),
    ),
)

function loadData(): void {
  permitCatalogStore.loadPermits()
  if (serviceCatalogStore.services.length === 0) serviceCatalogStore.loadServices()
}

onMounted(() => {
  if (permitCatalogStore.permits.length === 0) loadData()
  else if (serviceCatalogStore.services.length === 0) serviceCatalogStore.loadServices()
})

// New-permit edits and mutations save immediately as they're made (see
// permitCatalogStore), so the only feedback needed here is a toast if a
// particular action failed -- e.g. a duplicate name, rejected server-side.
function reportIfFailed(action: Promise<void>): void {
  action.then(() => {
    if (permitCatalogStore.mutationError) {
      toastStore.show('error', t('common.changeNotSaved'), permitCatalogStore.mutationError)
    }
  })
}

function handleAddPermit(name: string, fixedCost: number): void {
  reportIfFailed(permitCatalogStore.addPermit(name, fixedCost))
}

function handleUpdatePermit(permitId: string, name: string, fixedCost: number): void {
  reportIfFailed(permitCatalogStore.renamePermit(permitId, name, fixedCost))
}

function handleRemovePermit(permitId: string): void {
  reportIfFailed(permitCatalogStore.removePermit(permitId))
}
</script>

<template>
  <ErrorState v-if="permitCatalogStore.error" :description="permitCatalogStore.error" @retry="loadData" />

  <div v-else-if="permitCatalogStore.isLoading" class="rounded-xl border border-border-light bg-bg-card p-6">
    <SkeletonLoader :rows="5" />
  </div>

  <Card v-else class="max-w-2xl">
    <PermitCatalogListEditor
      :permits="permitCatalogStore.permits"
      :design-activity-options="designActivityOptions"
      @add="handleAddPermit"
      @update="handleUpdatePermit"
      @remove="handleRemovePermit"
    />
  </Card>
</template>
