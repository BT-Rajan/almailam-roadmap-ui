<script setup lang="ts">
import { ChevronDown, ChevronUp, Plus, Trash2, X } from '@lucide/vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import IconButton from '@/components/common/IconButton.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { documentRequirementService } from '@/services/documentRequirementService'
import { usePermitCatalogStore } from '@/stores/permitCatalogStore'
import { useServiceCatalogStore } from '@/stores/serviceCatalogStore'
import { useToastStore } from '@/stores/toastStore'
import type { DocumentRequirement, DocumentRequirementLink, DocumentRequirementTargetType } from '@/types/DocumentRequirement'
import type { SelectOption } from '@/types/Ui'

const { t } = useI18n()
const toastStore = useToastStore()
const serviceCatalogStore = useServiceCatalogStore()
const permitCatalogStore = usePermitCatalogStore()

const requirements = ref<DocumentRequirement[]>([])
const isLoading = ref(false)
const error = ref<string>()

async function loadData(): Promise<void> {
  isLoading.value = true
  error.value = undefined
  try {
    const [loadedRequirements] = await Promise.all([
      documentRequirementService.getRequirements(),
      serviceCatalogStore.services.length === 0 ? serviceCatalogStore.loadServices() : Promise.resolve(),
      permitCatalogStore.permits.length === 0 ? permitCatalogStore.loadPermits() : Promise.resolve(),
    ])
    requirements.value = loadedRequirements
  } catch (err) {
    error.value = err instanceof Error ? err.message : t('common.pleaseTryAgain')
  } finally {
    isLoading.value = false
  }
}

onMounted(loadData)

// Every catalog activity/permit, flat, as the "link to" picker options --
// value encodes {targetType, targetCatalogId} as "Design:ACT-004" /
// "Permit:PER-003" so a plain SelectBox (string value) can drive it.
const targetOptions = computed<SelectOption[]>(() => {
  const options: SelectOption[] = []
  for (const service of serviceCatalogStore.services) {
    for (const activity of service.activities) {
      options.push({ label: `${service.branch}: ${service.name} — ${activity.name}`, value: `${service.branch}:${activity.id}` })
    }
  }
  for (const permit of permitCatalogStore.permits) {
    options.push({ label: `Permit: ${permit.name}`, value: `Permit:${permit.id}` })
  }
  return options
})

function targetLabel(link: DocumentRequirementLink): string {
  const match = targetOptions.value.find((option) => option.value === `${link.targetType}:${link.targetCatalogId}`)
  return match?.label ?? `${link.targetType}: ${link.targetCatalogId}`
}

const newRequirementName = ref('')
const newRequirementDescription = ref('')
const isSubmittingNew = ref(false)

async function submitNewRequirement(): Promise<void> {
  const name = newRequirementName.value.trim()
  if (name.length === 0) return
  isSubmittingNew.value = true
  try {
    const created = await documentRequirementService.createRequirement(name, newRequirementDescription.value.trim() || undefined)
    requirements.value = [...requirements.value, created].sort((a, b) => a.name.localeCompare(b.name))
    newRequirementName.value = ''
    newRequirementDescription.value = ''
  } catch (err) {
    toastStore.show('error', t('administration.documentRequirements.failedToAdd'), err instanceof Error ? err.message : t('common.pleaseTryAgain'))
  } finally {
    isSubmittingNew.value = false
  }
}

async function removeRequirement(requirement: DocumentRequirement): Promise<void> {
  try {
    await documentRequirementService.removeRequirement(requirement.id)
    requirements.value = requirements.value.filter((r) => r.id !== requirement.id)
  } catch (err) {
    toastStore.show('error', t('administration.documentRequirements.failedToRemove'), err instanceof Error ? err.message : t('common.pleaseTryAgain'))
  }
}

const nameDrafts = reactive<Record<string, string>>({})
const descriptionDrafts = reactive<Record<string, string>>({})

async function commitName(requirement: DocumentRequirement, value: string): Promise<void> {
  delete nameDrafts[requirement.id]
  const trimmed = value.trim()
  if (trimmed.length === 0 || trimmed === requirement.name) return
  try {
    const updated = await documentRequirementService.updateRequirement(requirement.id, { name: trimmed })
    requirement.name = updated.name
  } catch (err) {
    toastStore.show('error', t('common.changeNotSaved'), err instanceof Error ? err.message : t('common.pleaseTryAgain'))
  }
}

async function commitDescription(requirement: DocumentRequirement, value: string): Promise<void> {
  delete descriptionDrafts[requirement.id]
  if (value === (requirement.description ?? '')) return
  try {
    const updated = await documentRequirementService.updateRequirement(requirement.id, { description: value })
    requirement.description = updated.description
  } catch (err) {
    toastStore.show('error', t('common.changeNotSaved'), err instanceof Error ? err.message : t('common.pleaseTryAgain'))
  }
}

// Links (reuse targets) are fetched lazily, per requirement, only once
// its row is expanded -- same pattern as PermitCatalogListEditor's
// prerequisites panel.
const expandedRequirementId = ref<string>()
const linksByRequirement = reactive<Record<string, DocumentRequirementLink[]>>({})
const isLoadingLinks = ref<string>()
const newLinkTarget = reactive<Record<string, string>>({})
const isMutatingLink = ref<string>()

async function toggleExpanded(requirement: DocumentRequirement): Promise<void> {
  if (expandedRequirementId.value === requirement.id) {
    expandedRequirementId.value = undefined
    return
  }
  expandedRequirementId.value = requirement.id
  if (linksByRequirement[requirement.id]) return
  isLoadingLinks.value = requirement.id
  try {
    linksByRequirement[requirement.id] = await documentRequirementService.getLinksForRequirement(requirement.id)
  } catch (err) {
    toastStore.show('error', t('administration.documentRequirements.failedToLoadLinks'), err instanceof Error ? err.message : t('common.pleaseTryAgain'))
  } finally {
    isLoadingLinks.value = undefined
  }
}

async function addLink(requirement: DocumentRequirement): Promise<void> {
  const raw = newLinkTarget[requirement.id]
  if (!raw) return
  const [targetType, targetCatalogId] = raw.split(':') as [DocumentRequirementTargetType, string]
  isMutatingLink.value = requirement.id
  try {
    const created = await documentRequirementService.addLink(requirement.id, targetType, targetCatalogId)
    linksByRequirement[requirement.id] = [...(linksByRequirement[requirement.id] ?? []), created]
    newLinkTarget[requirement.id] = ''
  } catch (err) {
    toastStore.show('error', t('administration.documentRequirements.failedToLink'), err instanceof Error ? err.message : t('common.pleaseTryAgain'))
  } finally {
    isMutatingLink.value = undefined
  }
}

async function removeLink(requirement: DocumentRequirement, link: DocumentRequirementLink): Promise<void> {
  isMutatingLink.value = requirement.id
  try {
    await documentRequirementService.removeLink(link.id)
    linksByRequirement[requirement.id] = (linksByRequirement[requirement.id] ?? []).filter((l) => l.id !== link.id)
  } catch (err) {
    toastStore.show('error', t('administration.documentRequirements.failedToUnlink'), err instanceof Error ? err.message : t('common.pleaseTryAgain'))
  } finally {
    isMutatingLink.value = undefined
  }
}
</script>

<template>
  <ErrorState v-if="error" :description="error" @retry="loadData" />

  <div v-else-if="isLoading" class="rounded-xl border border-border-light bg-bg-card p-6">
    <SkeletonLoader :rows="5" />
  </div>

  <div v-else class="flex max-w-2xl flex-col gap-4">
    <p class="text-sm text-text-muted">{{ t('administration.documentRequirements.description') }}</p>

    <ol v-if="requirements.length > 0" class="flex flex-col gap-3">
      <li
        v-for="requirement in requirements"
        :key="requirement.id"
        class="flex flex-col gap-3 rounded-lg border border-border-light bg-bg-card p-4"
      >
        <div class="flex items-start gap-3">
          <div class="flex flex-1 flex-col gap-2">
            <TextInput
              :model-value="nameDrafts[requirement.id] ?? requirement.name"
              :placeholder="t('administration.documentRequirements.name')"
              @update:model-value="nameDrafts[requirement.id] = $event"
              @blur="commitName(requirement, $event)"
            />
            <TextInput
              :model-value="descriptionDrafts[requirement.id] ?? (requirement.description ?? '')"
              :placeholder="t('administration.documentRequirements.descriptionPlaceholder')"
              @update:model-value="descriptionDrafts[requirement.id] = $event"
              @blur="commitDescription(requirement, $event)"
            />
          </div>
          <IconButton
            :icon="expandedRequirementId === requirement.id ? ChevronUp : ChevronDown"
            :label="t('administration.documentRequirements.linkedTo')"
            size="sm" variant="ghost"
            @click="toggleExpanded(requirement)"
          />
          <IconButton :icon="Trash2" :label="t('administration.documentRequirements.remove')" size="sm" variant="danger" @click="removeRequirement(requirement)" />
        </div>

        <div v-if="expandedRequirementId === requirement.id" class="flex flex-col gap-2 rounded-lg border border-border-light bg-bg-hover p-3">
          <p class="text-xs font-medium text-text-secondary">{{ t('administration.documentRequirements.linkedToDescription') }}</p>
          <SkeletonLoader v-if="isLoadingLinks === requirement.id" :rows="2" />
          <template v-else>
            <p v-if="(linksByRequirement[requirement.id] ?? []).length === 0" class="text-xs text-text-muted">
              {{ t('administration.documentRequirements.noLinksYet') }}
            </p>
            <div v-else class="flex flex-wrap gap-2">
              <span
                v-for="link in linksByRequirement[requirement.id]"
                :key="link.id"
                class="inline-flex items-center gap-1 rounded-full border border-accent-300 bg-accent-100 px-2.5 py-1 text-xs font-medium text-accent-700"
              >
                {{ targetLabel(link) }}
                <button
                  type="button"
                  :aria-label="t('administration.documentRequirements.unlink')"
                  :disabled="isMutatingLink === requirement.id"
                  @click="removeLink(requirement, link)"
                >
                  <X class="h-3 w-3" />
                </button>
              </span>
            </div>
            <div class="flex gap-2">
              <SelectBox
                v-model="newLinkTarget[requirement.id]"
                :placeholder="t('administration.documentRequirements.linkPlaceholder')"
                :options="targetOptions"
                class="flex-1"
              />
              <BaseButton
                variant="secondary" size="sm"
                :disabled="!newLinkTarget[requirement.id] || isMutatingLink === requirement.id"
                @click="addLink(requirement)"
              >{{ t('administration.documentRequirements.link') }}</BaseButton>
            </div>
          </template>
        </div>
      </li>
    </ol>
    <p v-else class="text-sm text-text-muted">{{ t('administration.documentRequirements.noRequirementsYet') }}</p>

    <div class="flex flex-col gap-2 rounded-lg border border-dashed border-border-default p-4">
      <p class="text-sm font-medium text-text-secondary">{{ t('administration.documentRequirements.addRequirement') }}</p>
      <div class="flex flex-col gap-2">
        <TextInput v-model="newRequirementName" :placeholder="t('administration.documentRequirements.name')" @keyup.enter="submitNewRequirement" />
        <TextArea v-model="newRequirementDescription" :placeholder="t('administration.documentRequirements.descriptionPlaceholder')" :rows="2" />
        <BaseButton :icon="Plus" variant="secondary" :disabled="newRequirementName.trim().length === 0 || isSubmittingNew" @click="submitNewRequirement">
          {{ t('administration.documentRequirements.add') }}
        </BaseButton>
      </div>
    </div>
  </div>
</template>
