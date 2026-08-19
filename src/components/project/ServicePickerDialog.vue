<script setup lang="ts">
import { Minus, Plus, X } from '@lucide/vue'
import { computed, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import IconButton from '@/components/common/IconButton.vue'
import type { SelectedServiceActivity, ServiceCatalogItem } from '@/types/ServiceCatalog'
import { formatCurrency } from '@/utils/currencyFormatter'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    services: ServiceCatalogItem[]
    selected: SelectedServiceActivity[]
    currency?: string
  }>(),
  { currency: 'KWD' },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [value: SelectedServiceActivity[]]
}>()

// Draft state -- edits here don't touch the caller's selection until "Add
// Services" is clicked, so closing the dialog (Escape, backdrop click,
// Cancel) without confirming leaves the wizard's actual selection alone.
const selectedIds = ref<string[]>([])
const expandedServiceIds = ref<string[]>([])

// Re-seed the draft from whatever the caller already has selected every
// time the dialog opens, so re-opening to tweak a pick shows the current
// state rather than starting empty. Services that already have a pick are
// pre-expanded so the user isn't hunting for what's checked.
watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    selectedIds.value = props.selected.map((item) => item.activityId)
    const servicesWithPicks = new Set(props.selected.map((item) => item.serviceId))
    expandedServiceIds.value = props.services.filter((service) => servicesWithPicks.has(service.id)).map((service) => service.id)
  },
  { immediate: true },
)

function isExpanded(serviceId: string): boolean {
  return expandedServiceIds.value.includes(serviceId)
}

function toggleExpanded(serviceId: string): void {
  expandedServiceIds.value = isExpanded(serviceId)
    ? expandedServiceIds.value.filter((id) => id !== serviceId)
    : [...expandedServiceIds.value, serviceId]
}

function isActivitySelected(activityId: string): boolean {
  return selectedIds.value.includes(activityId)
}

function toggleActivity(activityId: string): void {
  selectedIds.value = isActivitySelected(activityId)
    ? selectedIds.value.filter((id) => id !== activityId)
    : [...selectedIds.value, activityId]
}

// A service's own checkbox is a shortcut for "all of its activities" --
// checked when every activity under it is picked, indeterminate when only
// some are, so partial picks (the whole point of the tree) stay visible
// at the service level too.
function serviceSelectionState(service: ServiceCatalogItem): 'all' | 'some' | 'none' {
  if (service.activities.length === 0) return 'none'
  const pickedCount = service.activities.filter((activity) => isActivitySelected(activity.id)).length
  if (pickedCount === 0) return 'none'
  return pickedCount === service.activities.length ? 'all' : 'some'
}

function toggleService(service: ServiceCatalogItem): void {
  const activityIds = service.activities.map((activity) => activity.id)
  if (serviceSelectionState(service) === 'all') {
    selectedIds.value = selectedIds.value.filter((id) => !activityIds.includes(id))
  } else {
    selectedIds.value = [...new Set([...selectedIds.value, ...activityIds])]
  }
  if (!isExpanded(service.id)) toggleExpanded(service.id)
}

// Flat list of picks in service order -- this is what drives both the
// "selected" and "price" columns, so they always stay row-aligned.
const selectedItems = computed<SelectedServiceActivity[]>(() =>
  props.services.flatMap((service) =>
    service.activities
      .filter((activity) => isActivitySelected(activity.id))
      .map((activity) => ({
        serviceId: service.id,
        serviceName: service.name,
        activityId: activity.id,
        activityName: activity.name,
        fixedCost: activity.fixedCost,
      })),
  ),
)

const total = computed(() => selectedItems.value.reduce((sum, item) => sum + item.fixedCost, 0))
const distinctServiceCount = computed(() => new Set(selectedItems.value.map((item) => item.serviceId)).size)

function removeItem(activityId: string): void {
  toggleActivity(activityId)
}

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  emit('confirm', selectedItems.value)
  emit('update:modelValue', false)
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="Select Services" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <div class="grid grid-cols-1 gap-4 tablet:grid-cols-12">
      <!-- Column 1: service tree -->
      <div class="flex flex-col rounded-lg border border-border-light tablet:col-span-5">
        <div class="border-b border-border-light bg-bg-hover px-3 py-2 text-xs font-medium uppercase tracking-wide text-neutral-400">Services</div>
        <div class="max-h-96 overflow-y-auto p-2">
          <p v-if="services.length === 0" class="p-2 text-sm text-neutral-400">No services in the catalog yet.</p>
          <div v-for="service in services" :key="service.id" class="mb-1">
            <div class="flex items-center gap-1.5 rounded-md px-1 py-1.5 hover:bg-bg-hover">
              <IconButton
                :icon="isExpanded(service.id) ? Minus : Plus"
                :label="isExpanded(service.id) ? `Collapse ${service.name}` : `Expand ${service.name}`"
                size="sm"
                :disabled="service.activities.length === 0"
                @click="toggleExpanded(service.id)"
              />
              <Checkbox
                :model-value="serviceSelectionState(service) === 'all'"
                :indeterminate="serviceSelectionState(service) === 'some'"
                :label="service.name"
                :disabled="service.activities.length === 0"
                @update:model-value="toggleService(service)"
              />
            </div>
            <div v-if="isExpanded(service.id)" class="ml-9 flex flex-col gap-0.5 border-l border-border-light pl-3">
              <p v-if="service.activities.length === 0" class="py-1 text-xs text-neutral-400">No activities under this service.</p>
              <div v-for="activity in service.activities" :key="activity.id" class="flex items-center justify-between gap-2 rounded px-1 py-1 hover:bg-bg-hover">
                <Checkbox
                  :model-value="isActivitySelected(activity.id)"
                  :label="activity.name"
                  @update:model-value="toggleActivity(activity.id)"
                />
                <span class="shrink-0 text-xs text-neutral-400">{{ formatCurrency(activity.fixedCost, currency) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Column 2: selected activities -->
      <div class="flex flex-col rounded-lg border border-border-light tablet:col-span-4">
        <div class="border-b border-border-light bg-bg-hover px-3 py-2 text-xs font-medium uppercase tracking-wide text-neutral-400">Selected</div>
        <div class="max-h-96 overflow-y-auto p-2">
          <p v-if="selectedItems.length === 0" class="p-2 text-sm text-neutral-400">Nothing selected yet -- check items on the left.</p>
          <div v-for="item in selectedItems" :key="item.activityId" class="flex items-start justify-between gap-2 rounded-md px-2 py-1.5 hover:bg-bg-hover">
            <div class="min-w-0">
              <p class="truncate text-sm text-neutral-800">{{ item.activityName }}</p>
              <p class="truncate text-xs text-neutral-400">{{ item.serviceName }}</p>
            </div>
            <IconButton :icon="X" label="Remove" size="sm" @click="removeItem(item.activityId)" />
          </div>
        </div>
      </div>

      <!-- Column 3: price -->
      <div class="flex flex-col rounded-lg border border-border-light tablet:col-span-3">
        <div class="border-b border-border-light bg-bg-hover px-3 py-2 text-xs font-medium uppercase tracking-wide text-neutral-400">Price</div>
        <div class="max-h-96 overflow-y-auto p-2">
          <p v-if="selectedItems.length === 0" class="p-2 text-sm text-neutral-400">--</p>
          <div v-for="item in selectedItems" :key="item.activityId" class="rounded-md px-2 py-1.5 text-right text-sm text-neutral-800">
            {{ formatCurrency(item.fixedCost, currency) }}
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex w-full items-center justify-between gap-3">
        <p class="text-sm font-medium text-neutral-700">
          <span v-if="selectedItems.length === 0" class="text-neutral-400">No services selected</span>
          <span v-else>
            {{ distinctServiceCount }} service{{ distinctServiceCount === 1 ? '' : 's' }} ·
            {{ selectedItems.length }} activit{{ selectedItems.length === 1 ? 'y' : 'ies' }} ·
            <span class="text-primary-700">{{ formatCurrency(total, currency) }}</span>
          </span>
        </p>
        <div class="flex gap-3">
          <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
          <BaseButton :disabled="selectedItems.length === 0" @click="handleConfirm">Add Services</BaseButton>
        </div>
      </div>
    </template>
  </BaseDialog>
</template>
