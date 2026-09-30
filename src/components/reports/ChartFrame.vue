<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { formatValue, seriesColor, type ChartModel, type ChartValueFormat } from '@/components/reports/chartUtils'

// Legend, "show as table" twin and empty state shared by every report
// chart, so identity is never colour-alone and every value is readable
// without hovering.
const props = withDefaults(
  defineProps<{
    model: ChartModel
    format?: ChartValueFormat
    currency?: string
    /** Header for the category column of the table view. */
    categoryLabel?: string
    /** Adds a Total row to the table view (only for additive figures). */
    showTotal?: boolean
    /** 'line' keys the legend with a stroke instead of a swatch. */
    legendShape?: 'rect' | 'line'
  }>(),
  { format: 'number', currency: undefined, categoryLabel: '', showTotal: false, legendShape: 'rect' },
)

const { t } = useI18n()
const asTable = ref(false)

const isEmpty = computed(() => props.model.categories.length === 0 || props.model.series.every((series) => series.values.every((value) => !value)))
const totals = computed(() => props.model.series.map((series) => series.values.reduce((sum, value) => sum + value, 0)))
</script>

<template>
  <div class="flex flex-col gap-3">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <ul v-if="model.series.length > 1" class="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-text-secondary">
        <li v-for="(series, index) in model.series" :key="series.name" class="flex items-center gap-1.5">
          <span v-if="legendShape === 'line'" class="inline-block h-0.5 w-4 rounded-full" :style="{ background: seriesColor(series, index) }" />
          <span v-else class="inline-block h-2.5 w-2.5 rounded-sm" :style="{ background: seriesColor(series, index) }" />
          {{ series.name }}
        </li>
      </ul>
      <span v-else />
      <button
        v-if="!isEmpty"
        type="button"
        class="text-xs font-medium text-accent-600 hover:text-accent-700 print:hidden"
        @click="asTable = !asTable"
      >
        {{ asTable ? t('report.chart.showChart') : t('report.chart.showTable') }}
      </button>
    </div>

    <p v-if="isEmpty" class="py-10 text-center text-sm text-text-muted">{{ t('report.chart.noData') }}</p>

    <div v-else-if="asTable" class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-border-light text-left text-xs uppercase tracking-wide text-text-muted">
            <th class="py-2 pe-4 font-medium">{{ categoryLabel }}</th>
            <th v-for="series in model.series" :key="series.name" class="py-2 ps-4 text-end font-medium">{{ series.name }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(category, row) in model.categories" :key="category" class="border-b border-border-light/60">
            <td class="py-2 pe-4 text-text-primary">{{ category }}</td>
            <td v-for="series in model.series" :key="series.name" class="py-2 ps-4 text-end tabular-nums text-text-primary">
              {{ formatValue(series.values[row] ?? 0, format, currency) }}
            </td>
          </tr>
        </tbody>
        <tfoot v-if="showTotal">
          <tr class="font-semibold text-text-primary">
            <td class="py-2 pe-4">{{ t('report.chart.total') }}</td>
            <td v-for="(total, index) in totals" :key="index" class="py-2 ps-4 text-end tabular-nums">{{ formatValue(total, format, currency) }}</td>
          </tr>
        </tfoot>
      </table>
    </div>

    <div v-else class="relative">
      <slot />
    </div>
  </div>
</template>
