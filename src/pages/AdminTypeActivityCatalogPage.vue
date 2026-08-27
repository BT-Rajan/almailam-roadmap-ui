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
import TypeActivityCategoryCard from '@/components/administration/TypeActivityCategoryCard.vue'
import TypeActivityItemEditor from '@/components/administration/TypeActivityItemEditor.vue'
import { useTypeActivityCatalogStore } from '@/stores/typeActivityCatalogStore'
import { useToastStore } from '@/stores/toastStore'

const typeActivityCatalogStore = useTypeActivityCatalogStore()
const toastStore = useToastStore()

function loadData(): void {
  typeActivityCatalogStore.loadCategories()
}

onMounted(() => {
  if (typeActivityCatalogStore.categories.length === 0) loadData()
})

// Same "save immediately, toast only on failure" convention as
// AdminServiceCatalogPage.vue.
function reportIfFailed(action: Promise<void>): void {
  action.then(() => {
    if (typeActivityCatalogStore.mutationError) {
      toastStore.show('error', 'Change not saved', typeActivityCatalogStore.mutationError)
    }
  })
}

const newCategoryName = ref('')

function submitNewCategory(): void {
  if (newCategoryName.value.trim().length === 0) return
  const name = newCategoryName.value.trim()
  reportIfFailed(typeActivityCatalogStore.addCategory(name))
  newCategoryName.value = ''
}

function handleRemoveCategory(categoryId: string): void {
  reportIfFailed(typeActivityCatalogStore.removeCategory(categoryId))
}

// Local draft of the selected category's in-progress name edit, same
// pattern as AdminServiceCatalogPage.vue's nameDraft.
const nameDraft = ref<string | undefined>(undefined)

function commitRename(categoryId: string, value: string, currentName: string): void {
  nameDraft.value = undefined
  const trimmed = value.trim()
  if (trimmed.length === 0 || trimmed === currentName) return
  reportIfFailed(typeActivityCatalogStore.renameCategory(categoryId, trimmed))
}

function handleAddActivity(name: string, cost: number): void {
  reportIfFailed(typeActivityCatalogStore.addActivity(name, cost))
}

function handleUpdateActivity(activityId: string, fields: { name?: string; cost?: number }): void {
  reportIfFailed(typeActivityCatalogStore.updateActivity(activityId, fields))
}

function handleRemoveActivity(activityId: string): void {
  reportIfFailed(typeActivityCatalogStore.removeActivity(activityId))
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader
      title="Additional Activity Catalog"
      subtitle="Configure the engagement type categories (Design, Supervision, etc) offered at project creation, and each category's checklist of priced additional activities."
    />

    <ErrorState v-if="typeActivityCatalogStore.error" :description="typeActivityCatalogStore.error" @retry="loadData" />

    <div v-else-if="typeActivityCatalogStore.isLoading" class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="rounded-xl border border-border-light bg-bg-card p-6">
        <SkeletonLoader :rows="5" />
      </div>
      <div class="rounded-xl border border-border-light bg-bg-card p-6 laptop:col-span-2">
        <SkeletonLoader :rows="8" />
      </div>
    </div>

    <div v-else class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="flex flex-col gap-3">
        <TypeActivityCategoryCard
          v-for="category in typeActivityCatalogStore.categories"
          :key="category.id"
          :category="category"
          :active="category.id === typeActivityCatalogStore.selectedCategoryId"
          @select="typeActivityCatalogStore.selectCategory"
        />

        <div class="flex flex-col gap-2 rounded-lg border border-dashed border-border-default p-4">
          <p class="text-sm font-medium text-text-secondary">Add Type Category</p>
          <div class="flex flex-col gap-2 sm:flex-row">
            <TextInput v-model="newCategoryName" placeholder="e.g. Design, Supervision" class="sm:flex-1" @keyup.enter="submitNewCategory" />
            <BaseButton :icon="Plus" variant="secondary" :disabled="newCategoryName.trim().length === 0" @click="submitNewCategory">
              Add
            </BaseButton>
          </div>
        </div>
      </div>

      <div class="flex flex-col gap-6 laptop:col-span-2">
        <EmptyState
          v-if="!typeActivityCatalogStore.selectedCategory"
          title="Select a type category"
          description="Choose a category on the left, or add a new one, to view and edit its activities."
        />

        <template v-else>
          <Card>
            <template #header>
              <div class="flex items-center justify-between gap-3">
                <TextInput
                  :model-value="nameDraft ?? typeActivityCatalogStore.selectedCategory.name"
                  aria-label="Type category name"
                  class="max-w-sm"
                  @update:model-value="nameDraft = $event"
                  @blur="commitRename(typeActivityCatalogStore.selectedCategory!.id, $event, typeActivityCatalogStore.selectedCategory!.name)"
                />
                <IconButton
                  :icon="Trash2"
                  :label="`Remove ${typeActivityCatalogStore.selectedCategory.name} category`"
                  size="sm"
                  variant="danger"
                  @click="handleRemoveCategory(typeActivityCatalogStore.selectedCategory!.id)"
                />
              </div>
            </template>

            <TypeActivityItemEditor
              :activities="typeActivityCatalogStore.selectedCategory.activities"
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
