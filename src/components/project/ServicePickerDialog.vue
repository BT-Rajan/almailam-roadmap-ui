<script setup lang="ts">
import { Minus, Plus, X } from '@lucide/vue'
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import IconButton from '@/components/common/IconButton.vue'
import type { PermitCatalogItem } from '@/types/PermitCatalog'
import type { SelectedSupervisionActivity } from '@/types/Project'
import type { SelectedServiceActivity, ServiceCatalogItem } from '@/types/ServiceCatalog'
import { formatCurrency } from '@/utils/currencyFormatter'
import { todayIso } from '@/utils/dateFormatter'

export interface ServicePickerConfirmPayload {
  design: SelectedServiceActivity[]
  supervision: SelectedSupervisionActivity[]
  supervisionStartDate: string | null
  supervisionEndDate: string | null
  permits: PermitCatalogItem[]
}

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    services: ServiceCatalogItem[]
    selectedDesign: SelectedServiceActivity[]
    selectedSupervision: SelectedSupervisionActivity[]
    supervisionStartDate?: string | null
    supervisionEndDate?: string | null
    // Permits only make sense to plan at project *creation* time today --
    // there's no backend support yet for adding a permit to an
    // already-created project the way add_selected_services lets Design/
    // Supervision be added later (see ProjectWorkspacePage.vue's own
    // "Add Services" use of this same dialog, which deliberately leaves
    // this off). Explicit opt-in flag rather than inferring it from
    // `permits` being non-empty, so a caller that simply hasn't loaded
    // the permit catalog yet doesn't have the section silently vanish.
    showPermits?: boolean
    permits?: PermitCatalogItem[]
    selectedPermits?: PermitCatalogItem[]
    currency?: string
  }>(),
  { currency: 'KWD', supervisionStartDate: null, supervisionEndDate: null, showPermits: false, permits: () => [], selectedPermits: () => [] },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [value: ServicePickerConfirmPayload]
}>()

// One catalog, two branches (migration 0059) -- Design services keep the
// exact tree-picker behavior this dialog always had; the single
// Supervision service is rendered as its own section below with its
// activities' own start/end dates, since it's billed monthly rather than
// as a one-time fee. There's normally exactly one Supervision-branch item.
const { t } = useI18n()

const designServices = computed(() => props.services.filter((service) => service.branch === 'Design'))
const supervisionService = computed(() => props.services.find((service) => service.branch === 'Supervision'))

// --- Design picks -- draft state, same "don't touch caller's selection
// until confirmed" convention as before this dialog was unified.
const selectedIds = ref<string[]>([])
const selectedServiceIds = ref<string[]>([])
const expandedServiceIds = ref<string[]>([])

function isBareService(service: ServiceCatalogItem): boolean {
  return service.activities.length === 0
}

// --- Supervision picks -- one draft row per checked activity, keyed by
// activityId. Each row carries its own start/end date; the overall
// Supervision period (supervisionWindowStart/End) is entered once and
// used to default a newly-checked activity's own dates, which can then
// be overridden per-activity.
interface SupervisionDraftRow {
  activityId: string
  activityName: string
  monthlyRate: number
  startDate: string
  endDate: string
}
const supervisionRows = reactive<Record<string, SupervisionDraftRow>>({})
const supervisionWindowStart = ref('')
const supervisionWindowEnd = ref('')

// --- Permit picks -- same simple checkbox-list draft as Design/
// Supervision above, formerly its own separate PermitPickerDialog.
// Folded in here so services, permits and supervision are all planned
// in one place instead of three separate modals/fields on the wizard.
const selectedPermitIds = ref<string[]>([])

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    selectedIds.value = props.selectedDesign
      .filter((item) => item.activityId !== item.serviceId)
      .map((item) => item.activityId)
    selectedServiceIds.value = props.selectedDesign
      .filter((item) => item.activityId === item.serviceId)
      .map((item) => item.serviceId)
    const servicesWithPicks = new Set(props.selectedDesign.map((item) => item.serviceId))
    expandedServiceIds.value = designServices.value
      .filter((service) => servicesWithPicks.has(service.id))
      .map((service) => service.id)

    Object.keys(supervisionRows).forEach((key) => delete supervisionRows[key])
    for (const activity of props.selectedSupervision) {
      supervisionRows[activity.activityId] = {
        activityId: activity.activityId,
        activityName: activity.activityName,
        monthlyRate: activity.monthlyRate,
        startDate: activity.startDate,
        endDate: activity.endDate ?? '',
      }
    }
    supervisionWindowStart.value = props.supervisionStartDate ?? ''
    supervisionWindowEnd.value = props.supervisionEndDate ?? ''

    selectedPermitIds.value = props.selectedPermits.map((permit) => permit.id)
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
// at the service level too. A bare service (no activities) is checked
// purely off its own entry in selectedServiceIds.
function serviceSelectionState(service: ServiceCatalogItem): 'all' | 'some' | 'none' {
  if (isBareService(service)) return selectedServiceIds.value.includes(service.id) ? 'all' : 'none'
  const pickedCount = service.activities.filter((activity) => isActivitySelected(activity.id)).length
  if (pickedCount === 0) return 'none'
  return pickedCount === service.activities.length ? 'all' : 'some'
}

function toggleService(service: ServiceCatalogItem): void {
  if (isBareService(service)) {
    selectedServiceIds.value = selectedServiceIds.value.includes(service.id)
      ? selectedServiceIds.value.filter((id) => id !== service.id)
      : [...selectedServiceIds.value, service.id]
    return
  }
  const activityIds = service.activities.map((activity) => activity.id)
  if (serviceSelectionState(service) === 'all') {
    selectedIds.value = selectedIds.value.filter((id) => !activityIds.includes(id))
  } else {
    selectedIds.value = [...new Set([...selectedIds.value, ...activityIds])]
  }
  if (!isExpanded(service.id)) toggleExpanded(service.id)
}

// Flat list of Design picks in service order -- this is what drives both
// the "selected" and "price" columns, so they always stay row-aligned. A
// bare service pick shows up as its own row (activityId === serviceId, $0).
const selectedDesignItems = computed<SelectedServiceActivity[]>(() =>
  designServices.value.flatMap((service) => {
    if (isBareService(service)) {
      return selectedServiceIds.value.includes(service.id)
        ? [{ serviceId: service.id, serviceName: service.name, activityId: service.id, activityName: service.name, fixedCost: 0 }]
        : []
    }
    return service.activities
      .filter((activity) => isActivitySelected(activity.id))
      .map((activity) => ({
        serviceId: service.id,
        serviceName: service.name,
        activityId: activity.id,
        activityName: activity.name,
        fixedCost: activity.fixedCost,
      }))
  }),
)

const designTotal = computed(() => selectedDesignItems.value.reduce((sum, item) => sum + item.fixedCost, 0))
const distinctServiceCount = computed(() => new Set(selectedDesignItems.value.map((item) => item.serviceId)).size)

function removeDesignItem(item: SelectedServiceActivity): void {
  if (item.activityId === item.serviceId) {
    selectedServiceIds.value = selectedServiceIds.value.filter((id) => id !== item.serviceId)
  } else {
    toggleActivity(item.activityId)
  }
}

function isSupervisionSelected(activityId: string): boolean {
  return activityId in supervisionRows
}

// The end date can't be before its own start date OR before today
// (ISO "YYYY-MM-DD" strings compare correctly as dates lexicographically).
function minEndDate(activityId: string): string {
  const startDate = supervisionRows[activityId]?.startDate || ''
  return startDate > todayIso() ? startDate : todayIso()
}

function toggleSupervisionActivity(activityId: string, activityName: string, monthlyRate: number): void {
  if (isSupervisionSelected(activityId)) {
    delete supervisionRows[activityId]
    return
  }
  supervisionRows[activityId] = {
    activityId,
    activityName,
    monthlyRate,
    startDate: supervisionWindowStart.value,
    endDate: supervisionWindowEnd.value,
  }
}

// Only ever built from rows that already passed supervisionDatesMissing's
// gate below, so both dates are always real strings by the time this
// reaches the caller -- endDate is no longer optional (a Supervision
// activity with none used to be able to reach Payment Plan with no way
// to actually create its Financial Agreement).
const selectedSupervisionItems = computed<SelectedSupervisionActivity[]>(() =>
  Object.values(supervisionRows).map((row) => ({
    activityId: row.activityId,
    activityName: row.activityName,
    monthlyRate: row.monthlyRate,
    startDate: row.startDate,
    endDate: row.endDate,
  })),
)

const supervisionMonthlyTotal = computed(() =>
  selectedSupervisionItems.value.reduce((sum, item) => sum + item.monthlyRate, 0),
)
const hasSupervisionPicks = computed(() => selectedSupervisionItems.value.length > 0)

function isPermitSelected(permitId: string): boolean {
  return selectedPermitIds.value.includes(permitId)
}

function togglePermit(permitId: string): void {
  selectedPermitIds.value = isPermitSelected(permitId)
    ? selectedPermitIds.value.filter((id) => id !== permitId)
    : [...selectedPermitIds.value, permitId]
}

const selectedPermitItems = computed<PermitCatalogItem[]>(() =>
  props.permits.filter((permit) => selectedPermitIds.value.includes(permit.id)),
)

// Every checked activity needs both its own start AND end date before
// this can be confirmed -- the overall window's start/end is what a
// newly-checked activity defaults to, but either can be blank if the
// window itself hasn't been set yet.
const supervisionDatesMissing = computed(
  () => hasSupervisionPicks.value && Object.values(supervisionRows).some((row) => !row.startDate || !row.endDate),
)

const canConfirm = computed(
  () =>
    selectedDesignItems.value.length > 0 ||
    (hasSupervisionPicks.value && !supervisionDatesMissing.value) ||
    selectedPermitItems.value.length > 0,
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  if (!canConfirm.value) return
  emit('confirm', {
    design: selectedDesignItems.value,
    supervision: selectedSupervisionItems.value,
    supervisionStartDate: hasSupervisionPicks.value ? supervisionWindowStart.value || null : null,
    supervisionEndDate: hasSupervisionPicks.value ? supervisionWindowEnd.value || null : null,
    permits: selectedPermitItems.value,
  })
  emit('update:modelValue', false)
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="t('project.servicePickerDialog.title')" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-6">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-12">
        <!-- Column 1: Design service tree -->
        <div class="flex flex-col rounded-lg border border-border-light tablet:col-span-5">
          <div class="border-b border-border-light bg-bg-hover px-3 py-2 text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.servicePickerDialog.designServicesColumn') }}</div>
          <div class="max-h-96 overflow-y-auto p-2">
            <p v-if="designServices.length === 0" class="p-2 text-sm text-text-muted">{{ t('project.servicePickerDialog.noDesignServices') }}</p>
            <div v-for="service in designServices" :key="service.id" class="mb-1">
              <div class="flex items-center gap-1.5 rounded-md px-1 py-1.5 hover:bg-bg-hover">
                <IconButton
                  :icon="isExpanded(service.id) ? Minus : Plus"
                  :label="isExpanded(service.id) ? t('project.servicePickerDialog.collapseService', { name: service.name }) : t('project.servicePickerDialog.expandService', { name: service.name })"
                  size="sm"
                  :disabled="service.activities.length === 0"
                  @click="toggleExpanded(service.id)"
                />
                <Checkbox
                  :model-value="serviceSelectionState(service) === 'all'"
                  :indeterminate="serviceSelectionState(service) === 'some'"
                  :label="service.name"
                  @update:model-value="toggleService(service)"
                />
              </div>
              <div v-if="isExpanded(service.id)" class="ms-9 flex flex-col gap-0.5 border-s border-border-light ps-3">
                <p v-if="service.activities.length === 0" class="py-1 text-xs text-text-muted">{{ t('project.servicePickerDialog.noActivitiesUnderService') }}</p>
                <div v-for="activity in service.activities" :key="activity.id" class="flex items-center justify-between gap-2 rounded px-1 py-1 hover:bg-bg-hover">
                  <Checkbox
                    :model-value="isActivitySelected(activity.id)"
                    :label="activity.name"
                    @update:model-value="toggleActivity(activity.id)"
                  />
                  <span class="shrink-0 text-xs text-text-muted">{{ formatCurrency(activity.fixedCost, currency) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Column 2: selected Design activities -->
        <div class="flex flex-col rounded-lg border border-border-light tablet:col-span-4">
          <div class="border-b border-border-light bg-bg-hover px-3 py-2 text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.servicePickerDialog.selectedColumn') }}</div>
          <div class="max-h-96 overflow-y-auto p-2">
            <p v-if="selectedDesignItems.length === 0" class="p-2 text-sm text-text-muted">{{ t('project.servicePickerDialog.nothingSelectedYet') }}</p>
            <div v-for="item in selectedDesignItems" :key="item.activityId" class="flex items-start justify-between gap-2 rounded-md px-2 py-1.5 hover:bg-bg-hover">
              <div class="min-w-0">
                <p class="truncate text-sm text-text-primary">{{ item.activityName }}</p>
                <p v-if="item.activityId !== item.serviceId" class="truncate text-xs text-text-muted">{{ item.serviceName }}</p>
                <p v-else class="truncate text-xs text-text-muted">{{ t('project.servicePickerDialog.wholeService') }}</p>
              </div>
              <IconButton :icon="X" :label="t('project.servicePickerDialog.removeItem', { name: item.activityName })" size="sm" @click="removeDesignItem(item)" />
            </div>
          </div>
        </div>

        <!-- Column 3: price -->
        <div class="flex flex-col rounded-lg border border-border-light tablet:col-span-3">
          <div class="border-b border-border-light bg-bg-hover px-3 py-2 text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.servicePickerDialog.priceColumn') }}</div>
          <div class="max-h-96 overflow-y-auto p-2">
            <p v-if="selectedDesignItems.length === 0" class="p-2 text-sm text-text-muted">--</p>
            <div v-for="item in selectedDesignItems" :key="item.activityId" class="rounded-md px-2 py-1.5 text-end text-sm text-text-primary">
              {{ formatCurrency(item.fixedCost, currency) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Supervision -- monthly, day-prorated activities with their own dates -->
      <div v-if="supervisionService" class="flex flex-col rounded-lg border border-border-light">
        <div class="border-b border-border-light bg-bg-hover px-3 py-2 text-xs font-medium uppercase tracking-wide text-text-muted">
          {{ t('project.servicePickerDialog.supervisionMonthly') }}
        </div>
        <div class="flex flex-col gap-3 p-3">
          <p v-if="supervisionService.activities.length === 0" class="text-sm text-text-muted">{{ t('project.servicePickerDialog.noSupervisionActivities') }}</p>

          <template v-else>
            <div v-if="hasSupervisionPicks" class="grid grid-cols-1 gap-3 tablet:grid-cols-2">
              <DatePicker v-model="supervisionWindowStart" :label="t('project.servicePickerDialog.supervisionPeriodStart')" required />
              <DatePicker v-model="supervisionWindowEnd" :label="t('project.servicePickerDialog.supervisionPeriodEnd')" />
            </div>

            <div class="flex flex-col gap-2">
              <div v-for="activity in supervisionService.activities" :key="activity.id" class="rounded-md border border-border-light p-2">
                <div class="flex items-center justify-between gap-2">
                  <Checkbox
                    :model-value="isSupervisionSelected(activity.id)"
                    :label="activity.name"
                    @update:model-value="toggleSupervisionActivity(activity.id, activity.name, activity.fixedCost)"
                  />
                  <span class="shrink-0 text-xs text-text-muted">{{ formatCurrency(activity.fixedCost, currency) }}/mo</span>
                </div>
                <div v-if="isSupervisionSelected(activity.id)" class="mt-2 ms-7 grid grid-cols-1 gap-2 tablet:grid-cols-2">
                  <DatePicker v-model="supervisionRows[activity.id].startDate" :label="t('project.servicePickerDialog.startDate')" required />
                  <DatePicker
                    v-model="supervisionRows[activity.id].endDate"
                    :label="t('project.servicePickerDialog.endDate')"
                    required
                    :min="minEndDate(activity.id)"
                  />
                </div>
              </div>
            </div>

            <p v-if="supervisionDatesMissing" class="text-xs text-danger-600">
              {{ t('project.servicePickerDialog.supervisionDatesMissing') }}
            </p>
            <p v-else class="text-xs text-text-muted">
              {{ t('project.servicePickerDialog.supervisionProrationNote') }}
            </p>
          </template>
        </div>
      </div>

      <!-- Permits to apply for -- folded in from the wizard's former
           separate PermitPickerDialog so services, permits and
           supervision are all planned in this one modal. Simple
           checkbox list, no pricing/dates involved. Only offered by
           callers that opt in (see showPermits above). -->
      <div v-if="showPermits" class="flex flex-col rounded-lg border border-border-light">
        <div class="border-b border-border-light bg-bg-hover px-3 py-2 text-xs font-medium uppercase tracking-wide text-text-muted">
          {{ t('project.servicePickerDialog.permitsToApplyFor') }}
        </div>
        <div class="max-h-48 overflow-y-auto p-2">
          <p v-if="permits.length === 0" class="p-2 text-sm text-text-muted">{{ t('project.servicePickerDialog.noPermitsYet') }}</p>
          <div
            v-for="permit in permits"
            :key="permit.id"
            class="flex items-center gap-1.5 rounded-md px-2 py-1.5 hover:bg-bg-hover"
          >
            <Checkbox :model-value="isPermitSelected(permit.id)" :label="permit.name" @update:model-value="togglePermit(permit.id)" />
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex w-full items-center justify-between gap-3">
        <p class="text-sm font-medium text-text-secondary">
          <span
            v-if="selectedDesignItems.length === 0 && !hasSupervisionPicks && selectedPermitItems.length === 0"
            class="text-text-muted"
          >
            {{ t('project.servicePickerDialog.nothingSelected') }}
          </span>
          <span v-else class="flex flex-col items-start gap-0.5">
            <span v-if="selectedDesignItems.length > 0">
              {{ t('project.servicePickerDialog.designServicesCount', distinctServiceCount) }} ·
              {{ t('project.servicePickerDialog.activitiesCount', selectedDesignItems.length) }} ·
              <span class="text-primary-700">{{ formatCurrency(designTotal, currency) }}</span>
            </span>
            <span v-if="hasSupervisionPicks">
              {{ t('project.servicePickerDialog.supervisionActivitiesCount', selectedSupervisionItems.length) }} ·
              <span class="text-primary-700">{{ formatCurrency(supervisionMonthlyTotal, currency) }}/mo</span>
            </span>
            <span v-if="showPermits && selectedPermitItems.length > 0">
              {{ t('project.servicePickerDialog.permitsCount', selectedPermitItems.length) }}
            </span>
          </span>
        </p>
        <div class="flex gap-3">
          <BaseButton variant="secondary" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
          <BaseButton :disabled="!canConfirm" @click="handleConfirm">{{ t('project.servicePickerDialog.saveSelections') }}</BaseButton>
        </div>
      </div>
    </template>
  </BaseDialog>
</template>
