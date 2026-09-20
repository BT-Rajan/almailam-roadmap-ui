<script setup lang="ts">
import { ChevronDown, ChevronUp, Plus, Trash2, X } from '@lucide/vue'
import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import IconButton from '@/components/common/IconButton.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { permitCatalogService } from '@/services/permitCatalogService'
import { useToastStore } from '@/stores/toastStore'
import { formatCurrency } from '@/utils/currencyFormatter'
import type { GovernmentAuthority, GovernmentForm } from '@/types/Government'
import type { PermitApplicationSetupInput, PermitCatalogItem, PermitPrerequisite } from '@/types/PermitCatalog'
import type { SelectOption } from '@/types/Ui'

const { t } = useI18n()
const toastStore = useToastStore()

const props = defineProps<{
  permits: PermitCatalogItem[]
  // Every Design-branch activity, for the "eligible once these are
  // Complete" prerequisite picker -- see PermitCatalogPanel.vue.
  designActivityOptions: SelectOption[]
  // For the application setup (authority -> form) pickers.
  authorities: GovernmentAuthority[]
  forms: GovernmentForm[]
}>()

// update carries both fields together (not a partial), since the
// backend's PermitCatalogItemUpdate replaces the whole row -- unlike
// ServiceCatalogActivityEditor's per-field partial update, there's only
// one PATCH shape here, so name and fixedCost always travel together.
const emit = defineEmits<{
  update: [permitId: string, name: string, fixedCost: number]
  remove: [permitId: string]
  add: [name: string, fixedCost: number]
  'save-setup': [permitId: string, setup: PermitApplicationSetupInput]
}>()

// --- Application setup ------------------------------------------------
// One draft per permit, seeded when its row is expanded. Authority and
// form are saved together (the backend rejects a mismatched pair); the
// checklist is one document name per line, empty meaning "use the
// form's own list".
interface SetupDraft {
  authorityId: string
  formId: string
  documentsText: string
}
const setupDrafts = reactive<Record<string, SetupDraft>>({})

function isConfigured(permit: PermitCatalogItem): boolean {
  return Boolean(permit.authorityId && permit.formId)
}

function seedSetupDraft(permit: PermitCatalogItem): void {
  setupDrafts[permit.id] = {
    authorityId: permit.authorityId ?? '',
    formId: permit.formId ?? '',
    documentsText: (permit.requiredDocuments ?? []).join('\n'),
  }
}

const authorityOptions = computed<SelectOption[]>(() =>
  [...props.authorities]
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((authority) => ({ label: authority.name, value: authority.id })),
)

function formOptionsFor(authorityId: string): SelectOption[] {
  return props.forms
    .filter((form) => form.authorityId === authorityId && form.status === 'Active')
    .map((form) => ({ label: `${form.formCode} — ${form.title}`, value: form.id }))
}

function formDefaultDocuments(formId: string): string[] {
  return props.forms.find((form) => form.id === formId)?.requiredDocuments ?? []
}

function onSetupAuthorityChange(permitId: string, authorityId: string): void {
  const draft = setupDrafts[permitId]
  if (!draft || draft.authorityId === authorityId) return
  draft.authorityId = authorityId
  // A form belongs to exactly one authority -- never keep an orphaned pick.
  draft.formId = ''
}

function parseDocuments(text: string): string[] {
  return text.split('\n').map((line) => line.trim()).filter((line) => line.length > 0)
}

function isSetupDirty(permit: PermitCatalogItem): boolean {
  const draft = setupDrafts[permit.id]
  if (!draft) return false
  return (
    draft.authorityId !== (permit.authorityId ?? '') ||
    draft.formId !== (permit.formId ?? '') ||
    parseDocuments(draft.documentsText).join('\n') !== (permit.requiredDocuments ?? []).join('\n')
  )
}

// Both chosen, or both cleared -- never one without the other.
function isSetupSavable(permit: PermitCatalogItem): boolean {
  const draft = setupDrafts[permit.id]
  if (!draft || !isSetupDirty(permit)) return false
  return Boolean(draft.authorityId) === Boolean(draft.formId)
}

function saveSetup(permit: PermitCatalogItem): void {
  const draft = setupDrafts[permit.id]
  if (!draft || !isSetupSavable(permit)) return
  const documents = parseDocuments(draft.documentsText)
  emit('save-setup', permit.id, {
    authorityId: draft.authorityId || null,
    formId: draft.formId || null,
    requiredDocuments: draft.formId && documents.length > 0 ? documents : null,
  })
}

// Prerequisites are fetched lazily, per permit, only once its row is
// expanded -- most admin sessions never touch this, so there's no
// reason to fetch every permit's prerequisites up front.
const expandedPermitId = ref<string>()
const prerequisitesByPermit = reactive<Record<string, PermitPrerequisite[]>>({})
const isLoadingPrerequisites = ref<string>()
const newPrerequisiteActivityId = reactive<Record<string, string>>({})
const isMutatingPrerequisite = ref<string>()

async function toggleExpanded(permit: PermitCatalogItem): Promise<void> {
  if (expandedPermitId.value === permit.id) {
    expandedPermitId.value = undefined
    return
  }
  expandedPermitId.value = permit.id
  seedSetupDraft(permit)
  if (prerequisitesByPermit[permit.id]) return
  isLoadingPrerequisites.value = permit.id
  try {
    prerequisitesByPermit[permit.id] = await permitCatalogService.getPrerequisites(permit.id)
  } catch (error) {
    toastStore.show('error', t('administration.permitCatalog.failedToLoadPrerequisites'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isLoadingPrerequisites.value = undefined
  }
}

async function addPrerequisite(permit: PermitCatalogItem): Promise<void> {
  const designActivityId = newPrerequisiteActivityId[permit.id]
  if (!designActivityId) return
  isMutatingPrerequisite.value = permit.id
  try {
    const created = await permitCatalogService.addPrerequisite(permit.id, designActivityId)
    prerequisitesByPermit[permit.id] = [...(prerequisitesByPermit[permit.id] ?? []), created]
    newPrerequisiteActivityId[permit.id] = ''
  } catch (error) {
    toastStore.show('error', t('administration.permitCatalog.failedToAddPrerequisite'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isMutatingPrerequisite.value = undefined
  }
}

async function removePrerequisite(permit: PermitCatalogItem, prerequisite: PermitPrerequisite): Promise<void> {
  isMutatingPrerequisite.value = permit.id
  try {
    await permitCatalogService.removePrerequisite(prerequisite.id)
    prerequisitesByPermit[permit.id] = (prerequisitesByPermit[permit.id] ?? []).filter((p) => p.id !== prerequisite.id)
  } catch (error) {
    toastStore.show('error', t('administration.permitCatalog.failedToRemovePrerequisite'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isMutatingPrerequisite.value = undefined
  }
}

const newPermitName = ref('')
const newPermitCost = ref('')

function submitNewPermit(): void {
  if (newPermitName.value.trim().length === 0) return
  const cost = Number(newPermitCost.value)
  // Mirrors the backend's own PermitCatalogItemCreate.fixedCost
  // (condecimal(ge=0)) -- same gap as ServiceCatalogActivityEditor's
  // identical submitNewActivity/commitCost had.
  if (newPermitCost.value.trim() !== '' && (!Number.isFinite(cost) || cost < 0)) {
    toastStore.show('error', t('administration.permitCatalog.invalidCost'))
    return
  }
  emit('add', newPermitName.value.trim(), Number.isFinite(cost) && cost >= 0 ? cost : 0)
  newPermitName.value = ''
  newPermitCost.value = ''
}

// Local drafts of in-progress edits, keyed by permit id, so typing
// doesn't fire a save on every keystroke -- only once the field loses
// focus and the value actually changed. Same pattern as
// ServiceCatalogActivityEditor's name/cost drafts.
const nameDrafts = ref<Record<string, string>>({})
const costDrafts = ref<Record<string, string>>({})

function commitName(permit: PermitCatalogItem, value: string): void {
  delete nameDrafts.value[permit.id]
  const trimmed = value.trim()
  if (trimmed.length > 0 && trimmed !== permit.name) emit('update', permit.id, trimmed, permit.fixedCost)
}

function commitCost(permit: PermitCatalogItem, value: string): void {
  delete costDrafts.value[permit.id]
  const cost = Number(value)
  if (!Number.isFinite(cost) || cost < 0) {
    toastStore.show('error', t('administration.permitCatalog.invalidCost'))
    return
  }
  if (cost !== permit.fixedCost) emit('update', permit.id, permit.name, cost)
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <ol v-if="permits.length > 0" class="flex flex-col gap-3">
      <li
        v-for="permit in permits"
        :key="permit.id"
        class="flex flex-col gap-3 rounded-lg border border-border-light bg-bg-card p-4"
      >
        <div class="flex items-center gap-3">
          <TextInput
            :model-value="nameDrafts[permit.id] ?? permit.name"
            :placeholder="t('administration.permitCatalog.permitName')"
            class="flex-1"
            @update:model-value="nameDrafts[permit.id] = $event"
            @blur="commitName(permit, $event)"
          />
          <TextInput
            :model-value="costDrafts[permit.id] ?? String(permit.fixedCost)"
            type="number"
            inputmode="decimal"
            :placeholder="t('administration.permitCatalog.fixedCost')"
            class="w-32"
            @update:model-value="costDrafts[permit.id] = $event"
            @blur="commitCost(permit, $event)"
          />
          <span class="shrink-0 text-sm font-medium text-text-muted">{{ formatCurrency(permit.fixedCost) }}</span>
          <StatusBadge
            v-if="!isConfigured(permit)"
            :label="t('administration.permitCatalog.setupMissing')"
            variant="warning"
            size="sm"
          />
          <IconButton
            :icon="expandedPermitId === permit.id ? ChevronUp : ChevronDown"
            :label="t('administration.permitCatalog.permitSettings')"
            size="sm" variant="ghost"
            @click="toggleExpanded(permit)"
          />
          <IconButton :icon="Trash2" :label="t('administration.permitCatalog.removePermit')" size="sm" variant="danger" @click="emit('remove', permit.id)" />
        </div>

        <div
          v-if="expandedPermitId === permit.id && setupDrafts[permit.id]"
          class="flex flex-col gap-3 rounded-lg border border-border-light bg-bg-hover p-3"
        >
          <p class="text-xs font-medium text-text-secondary">{{ t('administration.permitCatalog.applicationSetupDescription') }}</p>
          <div class="grid grid-cols-1 gap-3 tablet:grid-cols-2">
            <SelectBox
              :model-value="setupDrafts[permit.id].authorityId"
              :label="t('administration.permitCatalog.authority')"
              :placeholder="t('administration.permitCatalog.selectAuthority')"
              :options="authorityOptions"
              @update:model-value="onSetupAuthorityChange(permit.id, $event)"
            />
            <SelectBox
              v-model="setupDrafts[permit.id].formId"
              :label="t('administration.permitCatalog.form')"
              :placeholder="t('administration.permitCatalog.selectForm')"
              :disabled="!setupDrafts[permit.id].authorityId"
              :options="formOptionsFor(setupDrafts[permit.id].authorityId)"
            />
          </div>
          <TextArea
            v-model="setupDrafts[permit.id].documentsText"
            :label="t('administration.permitCatalog.requiredDocuments')"
            :placeholder="formDefaultDocuments(setupDrafts[permit.id].formId).join('\n')"
            :hint="t('administration.permitCatalog.requiredDocumentsHint')"
            :disabled="!setupDrafts[permit.id].formId"
            :rows="5"
          />
          <div class="flex justify-end">
            <BaseButton size="sm" :disabled="!isSetupSavable(permit)" @click="saveSetup(permit)">
              {{ t('administration.permitCatalog.saveSetup') }}
            </BaseButton>
          </div>
        </div>

        <div v-if="expandedPermitId === permit.id" class="flex flex-col gap-2 rounded-lg border border-border-light bg-bg-hover p-3">
          <p class="text-xs font-medium text-text-secondary">{{ t('administration.permitCatalog.prerequisitesDescription') }}</p>
          <SkeletonLoader v-if="isLoadingPrerequisites === permit.id" :rows="2" />
          <template v-else>
            <p v-if="(prerequisitesByPermit[permit.id] ?? []).length === 0" class="text-xs text-text-muted">
              {{ t('administration.permitCatalog.noPrerequisitesYet') }}
            </p>
            <div v-else class="flex flex-wrap gap-2">
              <span
                v-for="prerequisite in prerequisitesByPermit[permit.id]"
                :key="prerequisite.id"
                class="inline-flex items-center gap-1 rounded-full border border-accent-300 bg-accent-100 px-2.5 py-1 text-xs font-medium text-accent-700"
              >
                {{ prerequisite.serviceName }} — {{ prerequisite.designActivityName }}
                <button
                  type="button"
                  :aria-label="t('administration.permitCatalog.removePrerequisite')"
                  :disabled="isMutatingPrerequisite === permit.id"
                  @click="removePrerequisite(permit, prerequisite)"
                >
                  <X class="h-3 w-3" />
                </button>
              </span>
            </div>
            <div class="flex gap-2">
              <SelectBox
                v-model="newPrerequisiteActivityId[permit.id]"
                :placeholder="t('administration.permitCatalog.addPrerequisitePlaceholder')"
                :options="designActivityOptions"
                class="flex-1"
              />
              <BaseButton
                variant="secondary" size="sm"
                :disabled="!newPrerequisiteActivityId[permit.id] || isMutatingPrerequisite === permit.id"
                @click="addPrerequisite(permit)"
              >{{ t('administration.permitCatalog.add') }}</BaseButton>
            </div>
          </template>
        </div>
      </li>
    </ol>
    <p v-else class="text-sm text-text-muted">{{ t('administration.permitCatalog.noPermitsYet') }}</p>

    <div class="flex flex-col gap-2 rounded-lg border border-dashed border-border-default p-4">
      <p class="text-sm font-medium text-text-secondary">{{ t('administration.permitCatalog.addPermit') }}</p>
      <div class="flex flex-col gap-2 sm:flex-row">
        <TextInput v-model="newPermitName" :placeholder="t('administration.permitCatalog.permitName')" class="sm:flex-1" @keyup.enter="submitNewPermit" />
        <TextInput
          v-model="newPermitCost"
          type="number"
          inputmode="decimal"
          :placeholder="t('administration.permitCatalog.fixedCost')"
          class="sm:w-32"
          @keyup.enter="submitNewPermit"
        />
        <BaseButton :icon="Plus" variant="secondary" :disabled="newPermitName.trim().length === 0" @click="submitNewPermit">
          {{ t('administration.permitCatalog.add') }}
        </BaseButton>
      </div>
    </div>
  </div>
</template>
