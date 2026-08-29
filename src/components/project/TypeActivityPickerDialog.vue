<script setup lang="ts">
import { ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import type { SelectedTypeActivity, TypeActivityCategory } from '@/types/TypeActivityCatalog'
import { formatCurrency } from '@/utils/currencyFormatter'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    categories: TypeActivityCategory[]
    selected: SelectedTypeActivity[]
    currency?: string
  }>(),
  { currency: 'KWD' },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [value: SelectedTypeActivity[]]
}>()

// Draft state -- edits here don't touch the caller's selection until
// "Add Activities" is clicked, so closing the dialog (Escape, backdrop
// click, Cancel) without confirming leaves the wizard's actual selection
// alone. Same pattern as ServicePickerDialog.
//
// A project can now include activities from more than one category at
// once (e.g. both Design and Supervision) -- viewedCategoryId is just
// which category's checklist is currently on screen, not a constraint on
// what's selected. selectedActivityIds accumulates across every category
// the user has visited, and activity ids are unique across the whole
// catalog, so looking up which category a selected id belongs to (see
// selectedItems below) never needs viewedCategoryId's help.
const viewedCategoryId = ref<string | undefined>(undefined)
const selectedActivityIds = ref<string[]>([])

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    viewedCategoryId.value = props.selected[0]?.categoryId ?? props.categories[0]?.id
    selectedActivityIds.value = props.selected.map((item) => item.activityId)
  },
  { immediate: true },
)

function viewedCategory(): TypeActivityCategory | undefined {
  return props.categories.find((category) => category.id === viewedCategoryId.value)
}

function viewCategory(categoryId: string): void {
  viewedCategoryId.value = categoryId
}

function isActivitySelected(activityId: string): boolean {
  return selectedActivityIds.value.includes(activityId)
}

function toggleActivity(activityId: string): void {
  selectedActivityIds.value = isActivitySelected(activityId)
    ? selectedActivityIds.value.filter((id) => id !== activityId)
    : [...selectedActivityIds.value, activityId]
}

function categorySelectedCount(category: TypeActivityCategory): number {
  return category.activities.filter((activity) => isActivitySelected(activity.id)).length
}

function selectedItems(): SelectedTypeActivity[] {
  const items: SelectedTypeActivity[] = []
  for (const category of props.categories) {
    for (const activity of category.activities) {
      if (!isActivitySelected(activity.id)) continue
      items.push({
        categoryId: category.id,
        categoryName: category.name,
        activityId: activity.id,
        activityName: activity.name,
        cost: activity.cost,
      })
    }
  }
  return items
}

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  emit('confirm', selectedItems())
  emit('update:modelValue', false)
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="Select Additional Services" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <div>
        <p class="mb-2 text-sm font-medium text-text-secondary">Engagement Type</p>
        <p v-if="categories.length === 0" class="text-sm text-text-muted">No type categories in the catalog yet.</p>
        <div v-else class="flex flex-wrap gap-2">
          <button
            v-for="category in categories"
            :key="category.id"
            type="button"
            role="tab"
            :aria-selected="category.id === viewedCategoryId"
            class="rounded-lg border px-3 py-2 text-sm font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500"
            :class="
              category.id === viewedCategoryId
                ? 'border-primary-500 bg-primary-50 text-primary-700'
                : 'border-border-light text-text-secondary hover:border-primary-300'
            "
            @click="viewCategory(category.id)"
          >
            {{ category.name }}
            <span v-if="categorySelectedCount(category) > 0" class="ml-1 text-xs text-primary-600">
              ({{ categorySelectedCount(category) }})
            </span>
          </button>
        </div>
        <p class="mt-1.5 text-xs text-text-muted">
          Activities can be checked across more than one engagement type -- e.g. both Design and Supervision.
        </p>
      </div>

      <div v-if="viewedCategory()" class="flex flex-col rounded-lg border border-border-light">
        <div class="border-b border-border-light bg-bg-hover px-3 py-2 text-xs font-medium uppercase tracking-wide text-text-muted">
          {{ viewedCategory()!.name }} Activities
        </div>
        <div class="max-h-72 overflow-y-auto p-2">
          <p v-if="viewedCategory()!.activities.length === 0" class="p-2 text-sm text-text-muted">
            No activities under this category yet.
          </p>
          <div
            v-for="activity in viewedCategory()!.activities"
            :key="activity.id"
            class="flex items-center justify-between gap-2 rounded-md px-2 py-1.5 hover:bg-bg-hover"
          >
            <Checkbox
              :model-value="isActivitySelected(activity.id)"
              :label="activity.name"
              @update:model-value="toggleActivity(activity.id)"
            />
            <span class="shrink-0 text-xs text-text-muted">{{ formatCurrency(activity.cost, currency) }}</span>
          </div>
        </div>
      </div>

      <p class="text-xs text-text-muted">
        If an activity checked here is already covered by a service you picked earlier, it won't be charged again --
        only activities not already covered add to the total below.
      </p>
    </div>

    <template #footer>
      <div class="flex w-full items-center justify-between gap-3">
        <p class="text-sm font-medium text-text-secondary">
          <span v-if="selectedItems().length === 0" class="text-text-muted">No activities selected</span>
          <span v-else>
            {{ selectedItems().length }} activit{{ selectedItems().length === 1 ? 'y' : 'ies' }} selected ·
            <span class="text-primary-700">up to {{ formatCurrency(selectedItems().reduce((sum, item) => sum + item.cost, 0), currency) }}</span>
          </span>
        </p>
        <div class="flex gap-3">
          <BaseButton variant="secondary" @click="closeDialog">Skip</BaseButton>
          <BaseButton :disabled="selectedItems().length === 0" @click="handleConfirm">Add Activities</BaseButton>
        </div>
      </div>
    </template>
  </BaseDialog>
</template>
