<script setup lang="ts">
/**
 * Verbatim rendering of the "Supervision" Arabic quotation letter.
 * Shares its overall structure with QuotationLetterDesignPermits but
 * the scope box is a single supervision line and the fee is a monthly
 * amount with no payment-milestone breakdown.
 */
import { computed } from 'vue'

import EditableList from '@/components/project/letters/EditableList.vue'
import EditableText from '@/components/project/letters/EditableText.vue'
import type { Quotation } from '@/types/Quotation'
import { formatDateNumeric } from '@/utils/dateFormatter'
import { amountToArabicWords } from '@/utils/numberToWords'

const props = defineProps<{
  quotation: Quotation
  editable: boolean
}>()

const emit = defineEmits<{ patch: [value: Partial<Quotation>] }>()

const feeWords = computed(() => amountToArabicWords(props.quotation.amount))
const feeAmountDisplay = computed(() =>
  props.quotation.amount % 1 === 0
    ? props.quotation.amount.toLocaleString('en-US')
    : props.quotation.amount.toLocaleString('en-US', { minimumFractionDigits: 3 }),
)
</script>

<template>
  <div dir="rtl" lang="ar" class="font-arabic space-y-4 text-[15px] leading-8 text-slate-900">
    <p class="text-center text-lg font-bold">عرض سعر</p>

    <p>
      التاريخ:
      <span class="font-medium">{{ formatDateNumeric(quotation.issueDate) }}</span>
    </p>

    <p class="flex flex-wrap justify-between gap-2">
      <span>
        السيد/
        <EditableText
          :model-value="quotation.clientRepresentative ?? ''"
          :editable="editable"
          placeholder="اسم العميل"
          @update:model-value="(v) => emit('patch', { clientRepresentative: v })"
        />
      </span>
      <span class="font-semibold">المحترم،،،</span>
    </p>

    <p>تحية طيبة وبعد،،،</p>

    <p>
      المشروع:
      <EditableText
        :model-value="quotation.projectReference ?? ''"
        :editable="editable"
        placeholder="قسيمة رقم ... – قطعة ... - منطقة ..."
        @update:model-value="(v) => emit('patch', { projectReference: v })"
      />
    </p>

    <p>
      الموضوع:
      <EditableText
        :model-value="quotation.subjectLine ?? ''"
        :editable="editable"
        placeholder="وصف الموضوع"
        @update:model-value="(v) => emit('patch', { subjectLine: v })"
      />.
    </p>

    <p>يسرنا أن نتقدم بعرض سعر للقيام بإصدار الأتي للمشروع المذكور أعلاه والتي تشمل</p>

    <div class="border border-slate-800 px-3 py-1 text-center font-bold">الإشراف:-</div>

    <EditableList
      :model-value="quotation.scopeItems"
      :editable="editable"
      @update:model-value="(v) => emit('patch', { scopeItems: v })"
    />

    <div class="border border-slate-800 px-3 py-1 text-center font-bold">العرض المالي:-</div>

    <p class="text-center">
      الأتعاب الاستشارية طبقاً للمراحل المذكورة أعلاه ، هو مبلغ وقدره -/
      <span class="font-semibold">{{ feeAmountDisplay }}</span>
      د.ك
      <span v-if="quotation.feeFrequency === 'Monthly'">شهرياً</span>
    </p>
    <p class="text-center">{{ feeWords }}.</p>

    <div class="pt-8 text-left">
      <p class="font-semibold">مكتب عبد الهادي الميلم</p>
      <p class="font-semibold">للاستشارات الهندسية</p>
    </div>
  </div>
</template>
