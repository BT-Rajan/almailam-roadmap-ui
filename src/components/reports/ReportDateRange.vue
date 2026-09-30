<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import type { ReportRange } from '@/composables/useReportRange'
import type { SelectOption } from '@/types/Ui'
import { RANGE_PRESETS, formatRange, type RangePreset } from '@/utils/reportRange'

// The one period control every report uses: presets first, a custom
// from/to behind "Custom range". Picking a preset applies at once; a
// custom range applies on "Apply", so half-typed dates never refetch.
const props = defineProps<{ state: ReportRange }>()
const { t } = useI18n()

const presetOptions = computed<SelectOption[]>(() =>
  [...RANGE_PRESETS, 'custom' as const].map((value) => ({ value, label: t(`report.range.presets.${value}`) })),
)

const selected = ref<RangePreset>(props.state.preset.value)
const customFrom = ref(props.state.range.value.from)
const customTo = ref(props.state.range.value.to)

watch(
  () => [props.state.preset.value, props.state.range.value] as const,
  ([preset, range]) => {
    selected.value = preset
    customFrom.value = range.from
    customTo.value = range.to
  },
)

function onPresetChange(value: string): void {
  selected.value = value as RangePreset
  if (value !== 'custom') props.state.setRange(value as RangePreset)
}

const canApply = computed(() => Boolean(customFrom.value && customTo.value))

function applyCustom(): void {
  if (canApply.value) props.state.setRange('custom', { from: customFrom.value, to: customTo.value })
}
</script>

<template>
  <div class="flex flex-wrap items-end gap-3 print:hidden">
    <div class="w-48">
      <SelectBox :model-value="selected" :options="presetOptions" :label="t('report.range.label')" @update:model-value="onPresetChange" />
    </div>
    <template v-if="selected === 'custom'">
      <div class="w-44"><DatePicker v-model="customFrom" :label="t('report.range.from')" /></div>
      <div class="w-44"><DatePicker v-model="customTo" :label="t('report.range.to')" :min="customFrom" /></div>
      <BaseButton :disabled="!canApply" @click="applyCustom">{{ t('report.range.apply') }}</BaseButton>
    </template>
    <p v-else class="pb-2.5 text-sm text-text-muted">{{ formatRange(state.range.value) }}</p>
  </div>
</template>
