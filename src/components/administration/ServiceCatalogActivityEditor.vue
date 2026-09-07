<script setup lang="ts">
import { ChevronDown, ChevronUp, Plus, Trash2, X } from '@lucide/vue'
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import IconButton from '@/components/common/IconButton.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextInput from '@/components/common/TextInput.vue'
import { serviceCatalogService } from '@/services/serviceCatalogService'
import { useToastStore } from '@/stores/toastStore'
import { formatCurrency } from '@/utils/currencyFormatter'
import type { ServiceCatalogActivity, ServiceCatalogBranch, SupervisionPrerequisite } from '@/types/ServiceCatalog'
import type { SelectOption } from '@/types/Ui'

const { t } = useI18n()
const toastStore = useToastStore()

const props = defineProps<{
  activities: ServiceCatalogActivity[]
  branch: ServiceCatalogBranch
  // Every Design-branch activity, for the "eligible once these are
  // Complete" prerequisite picker -- only relevant when branch ===
  // 'Supervision'. See ServiceCatalogPanel.vue.
  designActivityOptions: SelectOption[]
}>()

const emit = defineEmits<{
  update: [activityId: string, fields: { name?: string; fixedCost?: number }]
  remove: [activityId: string]
  add: [name: string, fixedCost: number]
}>()

const newActivityName = ref('')
const newActivityCost = ref('')

// Prerequisites (Supervision branch only) are fetched lazily, per
// activity, only once its row is expanded -- same pattern as
// PermitCatalogListEditor's own prerequisites panel.
const expandedActivityId = ref<string>()
const prerequisitesByActivity = reactive<Record<string, SupervisionPrerequisite[]>>({})
const isLoadingPrerequisites = ref<string>()
const newPrerequisiteActivityId = reactive<Record<string, string>>({})
const isMutatingPrerequisite = ref<string>()

async function toggleExpanded(activity: ServiceCatalogActivity): Promise<void> {
  if (props.branch !== 'Supervision') return
  if (expandedActivityId.value === activity.id) {
    expandedActivityId.value = undefined
    return
  }
  expandedActivityId.value = activity.id
  if (prerequisitesByActivity[activity.id]) return
  isLoadingPrerequisites.value = activity.id
  try {
    prerequisitesByActivity[activity.id] = await serviceCatalogService.getSupervisionPrerequisites(activity.id)
  } catch (error) {
    toastStore.show('error', t('administration.serviceCatalog.failedToLoadPrerequisites'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isLoadingPrerequisites.value = undefined
  }
}

async function addPrerequisite(activity: ServiceCatalogActivity): Promise<void> {
  const designActivityId = newPrerequisiteActivityId[activity.id]
  if (!designActivityId) return
  isMutatingPrerequisite.value = activity.id
  try {
    const created = await serviceCatalogService.addSupervisionPrerequisite(activity.id, designActivityId)
    prerequisitesByActivity[activity.id] = [...(prerequisitesByActivity[activity.id] ?? []), created]
    newPrerequisiteActivityId[activity.id] = ''
  } catch (error) {
    toastStore.show('error', t('administration.serviceCatalog.failedToAddPrerequisite'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isMutatingPrerequisite.value = undefined
  }
}

async function removePrerequisite(activity: ServiceCatalogActivity, prerequisite: SupervisionPrerequisite): Promise<void> {
  isMutatingPrerequisite.value = activity.id
  try {
    await serviceCatalogService.removeSupervisionPrerequisite(prerequisite.id)
    prerequisitesByActivity[activity.id] = (prerequisitesByActivity[activity.id] ?? []).filter((p) => p.id !== prerequisite.id)
  } catch (error) {
    toastStore.show('error', t('administration.serviceCatalog.failedToRemovePrerequisite'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isMutatingPrerequisite.value = undefined
  }
}

function submitNewActivity(): void {
  if (newActivityName.value.trim().length === 0) return
  const cost = Number(newActivityCost.value)
  emit('add', newActivityName.value.trim(), Number.isFinite(cost) ? cost : 0)
  newActivityName.value = ''
  newActivityCost.value = ''
}

// Local drafts of in-progress edits, keyed by activity id, so typing
// doesn't fire a save on every keystroke -- only once the field loses
// focus and the value actually changed. Same pattern as
// WorkflowStageEditor's name/description drafts.
const nameDrafts = ref<Record<string, string>>({})
const costDrafts = ref<Record<string, string>>({})

function commitName(activity: ServiceCatalogActivity, value: string): void {
  delete nameDrafts.value[activity.id]
  if (value !== activity.name) emit('update', activity.id, { name: value })
}

function commitCost(activity: ServiceCatalogActivity, value: string): void {
  delete costDrafts.value[activity.id]
  const cost = Number(value)
  if (Number.isFinite(cost) && cost !== activity.fixedCost) emit('update', activity.id, { fixedCost: cost })
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <ol v-if="activities.length > 0" class="flex flex-col gap-3">
      <li
        v-for="activity in activities"
        :key="activity.id"
        class="flex flex-col gap-3 rounded-lg border border-border-light bg-bg-card p-4 sm:flex-row sm:items-start"
      >
        <div class="flex flex-1 flex-col gap-2 sm:flex-row">
          <TextInput
            :model-value="nameDrafts[activity.id] ?? activity.name"
            :placeholder="t('administration.serviceCatalog.activityName')"
            class="sm:flex-1"
            @update:model-value="nameDrafts[activity.id] = $event"
            @blur="commitName(activity, $event)"
          />
          <TextInput
            :model-value="costDrafts[activity.id] ?? String(activity.fixedCost)"
            type="number"
            inputmode="decimal"
            :placeholder="t('administration.serviceCatalog.fixedCost')"
            class="sm:w-40"
            @update:model-value="costDrafts[activity.id] = $event"
            @blur="commitCost(activity, $event)"
          />
        </div>

        <div class="flex shrink-0 items-center gap-2 self-end sm:self-start">
          <span class="text-sm font-medium text-text-muted">{{ formatCurrency(activity.fixedCost) }}</span>
          <IconButton
            v-if="branch === 'Supervision'"
            :icon="expandedActivityId === activity.id ? ChevronUp : ChevronDown"
            :label="t('administration.serviceCatalog.prerequisites')"
            size="sm" variant="ghost"
            @click="toggleExpanded(activity)"
          />
          <IconButton :icon="Trash2" :label="t('administration.serviceCatalog.removeActivity')" size="sm" variant="danger" @click="emit('remove', activity.id)" />
        </div>

        <div
          v-if="branch === 'Supervision' && expandedActivityId === activity.id"
          class="flex w-full flex-col gap-2 rounded-lg border border-border-light bg-bg-hover p-3 sm:basis-full"
        >
          <p class="text-xs font-medium text-text-secondary">{{ t('administration.serviceCatalog.prerequisitesDescription') }}</p>
          <SkeletonLoader v-if="isLoadingPrerequisites === activity.id" :rows="2" />
          <template v-else>
            <p v-if="(prerequisitesByActivity[activity.id] ?? []).length === 0" class="text-xs text-text-muted">
              {{ t('administration.serviceCatalog.noPrerequisitesYet') }}
            </p>
            <div v-else class="flex flex-wrap gap-2">
              <span
                v-for="prerequisite in prerequisitesByActivity[activity.id]"
                :key="prerequisite.id"
                class="inline-flex items-center gap-1 rounded-full border border-accent-300 bg-accent-100 px-2.5 py-1 text-xs font-medium text-accent-700"
              >
                {{ prerequisite.serviceName }} — {{ prerequisite.designActivityName }}
                <button
                  type="button"
                  :aria-label="t('administration.serviceCatalog.removePrerequisite')"
                  :disabled="isMutatingPrerequisite === activity.id"
                  @click="removePrerequisite(activity, prerequisite)"
                >
                  <X class="h-3 w-3" />
                </button>
              </span>
            </div>
            <div class="flex gap-2">
              <SelectBox
                v-model="newPrerequisiteActivityId[activity.id]"
                :placeholder="t('administration.serviceCatalog.addPrerequisitePlaceholder')"
                :options="designActivityOptions"
                class="flex-1"
              />
              <BaseButton
                variant="secondary" size="sm"
                :disabled="!newPrerequisiteActivityId[activity.id] || isMutatingPrerequisite === activity.id"
                @click="addPrerequisite(activity)"
              >{{ t('administration.serviceCatalog.add') }}</BaseButton>
            </div>
          </template>
        </div>
      </li>
    </ol>
    <p v-else class="text-sm text-text-muted">{{ t('administration.serviceCatalog.noActivitiesYet') }}</p>

    <div class="flex flex-col gap-2 rounded-lg border border-dashed border-border-default p-4">
      <p class="text-sm font-medium text-text-secondary">{{ t('administration.serviceCatalog.addActivity') }}</p>
      <div class="flex flex-col gap-2 sm:flex-row">
        <TextInput v-model="newActivityName" :placeholder="t('administration.serviceCatalog.activityName')" class="sm:flex-1" />
        <TextInput v-model="newActivityCost" type="number" inputmode="decimal" :placeholder="t('administration.serviceCatalog.fixedCost')" class="sm:w-40" />
        <BaseButton :icon="Plus" variant="secondary" :disabled="newActivityName.trim().length === 0" @click="submitNewActivity">
          {{ t('administration.serviceCatalog.add') }}
        </BaseButton>
      </div>
    </div>
  </div>
</template>
