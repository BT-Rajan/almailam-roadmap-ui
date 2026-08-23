<script setup lang="ts">
import { onMounted } from 'vue'

import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import PermitCatalogListEditor from '@/components/administration/PermitCatalogListEditor.vue'
import { usePermitCatalogStore } from '@/stores/permitCatalogStore'
import { useToastStore } from '@/stores/toastStore'

const permitCatalogStore = usePermitCatalogStore()
const toastStore = useToastStore()

function loadData(): void {
  permitCatalogStore.loadPermits()
}

onMounted(() => {
  if (permitCatalogStore.permits.length === 0) loadData()
})

// New-permit edits and mutations save immediately as they're made (see
// permitCatalogStore), so the only feedback needed here is a toast if a
// particular action failed -- e.g. a duplicate name, rejected server-side.
function reportIfFailed(action: Promise<void>): void {
  action.then(() => {
    if (permitCatalogStore.mutationError) {
      toastStore.show('error', 'Change not saved', permitCatalogStore.mutationError)
    }
  })
}

function handleAddPermit(name: string): void {
  reportIfFailed(permitCatalogStore.addPermit(name))
}

function handleUpdatePermit(permitId: string, name: string): void {
  reportIfFailed(permitCatalogStore.renamePermit(permitId, name))
}

function handleRemovePermit(permitId: string): void {
  reportIfFailed(permitCatalogStore.removePermit(permitId))
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader
      title="Permit Catalog"
      subtitle="Configure the permits that can be attached to a project during setup."
    />

    <ErrorState v-if="permitCatalogStore.error" :description="permitCatalogStore.error" @retry="loadData" />

    <div v-else-if="permitCatalogStore.isLoading" class="rounded-xl border border-border-light bg-bg-card p-6">
      <SkeletonLoader :rows="5" />
    </div>

    <Card v-else class="max-w-2xl">
      <PermitCatalogListEditor
        :permits="permitCatalogStore.permits"
        @add="handleAddPermit"
        @update="handleUpdatePermit"
        @remove="handleRemovePermit"
      />
    </Card>
  </div>
</template>
