<script setup lang="ts">
import { Plus, Trash2 } from '@lucide/vue'
import { onMounted, ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import IconButton from '@/components/common/IconButton.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextInput from '@/components/common/TextInput.vue'
import ServiceCatalogActivityEditor from '@/components/administration/ServiceCatalogActivityEditor.vue'
import ServiceCatalogCard from '@/components/administration/ServiceCatalogCard.vue'
import { useServiceCatalogStore } from '@/stores/serviceCatalogStore'
import { useToastStore } from '@/stores/toastStore'

const serviceCatalogStore = useServiceCatalogStore()
const toastStore = useToastStore()

function loadData(): void {
  serviceCatalogStore.loadServices()
}

onMounted(() => {
  if (serviceCatalogStore.services.length === 0) loadData()
})

// New-service edits and mutations save immediately as they're made (see
// serviceCatalogStore), so the only feedback needed here is a toast if a
// particular action failed -- e.g. a duplicate name, rejected server-side.
function reportIfFailed(action: Promise<void>): void {
  action.then(() => {
    if (serviceCatalogStore.mutationError) {
      toastStore.show('error', 'Change not saved', serviceCatalogStore.mutationError)
    }
  })
}

const newServiceName = ref('')

function submitNewService(): void {
  if (newServiceName.value.trim().length === 0) return
  const name = newServiceName.value.trim()
  reportIfFailed(serviceCatalogStore.addService(name))
  newServiceName.value = ''
}

function handleRemoveService(serviceId: string): void {
  reportIfFailed(serviceCatalogStore.removeService(serviceId))
}

// Local draft of the selected service's in-progress name edit, so typing
// doesn't fire a save (and a duplicate-name round trip) on every
// keystroke -- only once the field loses focus and the value changed.
const nameDraft = ref<string | undefined>(undefined)

function commitRename(serviceId: string, value: string, currentName: string): void {
  nameDraft.value = undefined
  const trimmed = value.trim()
  if (trimmed.length === 0 || trimmed === currentName) return
  reportIfFailed(serviceCatalogStore.renameService(serviceId, trimmed))
}

function handleAddActivity(name: string, fixedCost: number): void {
  reportIfFailed(serviceCatalogStore.addActivity(name, fixedCost))
}

function handleUpdateActivity(activityId: string, fields: { name?: string; fixedCost?: number }): void {
  reportIfFailed(serviceCatalogStore.updateActivity(activityId, fields))
}

function handleRemoveActivity(activityId: string): void {
  reportIfFailed(serviceCatalogStore.removeActivity(activityId))
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader
      title="Service Catalog"
      subtitle="Configure the services offered and each service's activities and fixed costs."
    />

    <ErrorState v-if="serviceCatalogStore.error" :description="serviceCatalogStore.error" @retry="loadData" />

    <div v-else-if="serviceCatalogStore.isLoading" class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="rounded-xl border border-border-light bg-bg-card p-6">
        <SkeletonLoader :rows="5" />
      </div>
      <div class="rounded-xl border border-border-light bg-bg-card p-6 laptop:col-span-2">
        <SkeletonLoader :rows="8" />
      </div>
    </div>

    <div v-else class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="flex flex-col gap-3">
        <ServiceCatalogCard
          v-for="service in serviceCatalogStore.services"
          :key="service.id"
          :service="service"
          :active="service.id === serviceCatalogStore.selectedServiceId"
          @select="serviceCatalogStore.selectService"
        />

        <div class="flex flex-col gap-2 rounded-lg border border-dashed border-border-default p-4">
          <p class="text-sm font-medium text-text-secondary">Add Service</p>
          <div class="flex flex-col gap-2 sm:flex-row">
            <TextInput v-model="newServiceName" placeholder="Service name" class="sm:flex-1" @keyup.enter="submitNewService" />
            <BaseButton :icon="Plus" variant="secondary" :disabled="newServiceName.trim().length === 0" @click="submitNewService">
              Add
            </BaseButton>
          </div>
        </div>
      </div>

      <div class="flex flex-col gap-6 laptop:col-span-2">
        <EmptyState
          v-if="!serviceCatalogStore.selectedService"
          title="Select a service"
          description="Choose a service on the left, or add a new one, to view and edit its activities."
        />

        <template v-else>
          <Card>
            <template #header>
              <div class="flex items-center justify-between gap-3">
                <TextInput
                  :model-value="nameDraft ?? serviceCatalogStore.selectedService.name"
                  class="max-w-sm"
                  @update:model-value="nameDraft = $event"
                  @blur="commitRename(serviceCatalogStore.selectedService!.id, $event, serviceCatalogStore.selectedService!.name)"
                />
                <IconButton
                  :icon="Trash2"
                  label="Remove service"
                  size="sm"
                  variant="danger"
                  @click="handleRemoveService(serviceCatalogStore.selectedService!.id)"
                />
              </div>
            </template>

            <ServiceCatalogActivityEditor
              :activities="serviceCatalogStore.selectedService.activities"
              @add="handleAddActivity"
              @update="handleUpdateActivity"
              @remove="handleRemoveActivity"
            />
          </Card>
        </template>
      </div>
    </div>
  </div>
</template>
