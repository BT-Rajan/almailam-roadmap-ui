<script setup lang="ts">
/**
 * Bilingual rendering of the "Supervision" letter: Arabic block
 * (verbatim) followed by its English translation, same document.
 */
import { computed } from 'vue'

import EditableList from '@/components/project/letters/EditableList.vue'
import EditableText from '@/components/project/letters/EditableText.vue'
import type { Contract } from '@/types/Contract'
import { formatDateNumeric } from '@/utils/dateFormatter'
import { amountToArabicWords, amountToEnglishWords } from '@/utils/numberToWords'

const props = defineProps<{
  contract: Contract
  editable: boolean
}>()

const emit = defineEmits<{ patch: [value: Partial<Contract>] }>()

const feeWordsAr = computed(() => amountToArabicWords(props.contract.contractValue))
const feeWordsEn = computed(() => amountToEnglishWords(props.contract.contractValue))
const feeAmountDisplay = computed(() =>
  props.contract.contractValue % 1 === 0
    ? props.contract.contractValue.toLocaleString('en-US')
    : props.contract.contractValue.toLocaleString('en-US', { minimumFractionDigits: 3 }),
)
</script>

<template>
  <div class="space-y-8">
    <!-- Arabic block -->
    <div dir="rtl" lang="ar" class="font-arabic space-y-4 text-[15px] leading-8 text-slate-900">
      <p class="text-center text-lg font-bold">عرض سعر</p>

      <p>التاريخ: <span class="font-medium">{{ formatDateNumeric(contract.issueDate) }}</span></p>

      <p class="flex flex-wrap justify-between gap-2">
        <span>
          السيد/
          <EditableText
            :model-value="contract.clientRepresentative"
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
          :model-value="contract.projectReference ?? ''"
          :editable="editable"
          placeholder="قسيمة رقم ... – قطعة ... - منطقة ..."
          @update:model-value="(v) => emit('patch', { projectReference: v })"
        />
      </p>

      <p>
        الموضوع:
        <EditableText
          :model-value="contract.subjectLineAr ?? ''"
          :editable="editable"
          placeholder="وصف الموضوع"
          @update:model-value="(v) => emit('patch', { subjectLineAr: v })"
        />.
      </p>

      <p>يسرنا أن نتقدم بعرض سعر للقيام بإصدار الأتي للمشروع المذكور أعلاه والتي تشمل</p>

      <div class="border border-slate-800 px-3 py-1 text-center font-bold">الإشراف:-</div>

      <EditableList
        :model-value="contract.scopeItemsAr"
        :editable="editable"
        @update:model-value="(v) => emit('patch', { scopeItemsAr: v })"
      />

      <div class="border border-slate-800 px-3 py-1 text-center font-bold">العرض المالي:-</div>

      <p class="text-center">
        الأتعاب الاستشارية طبقاً للمراحل المذكورة أعلاه ، هو مبلغ وقدره -/
        <span class="font-semibold">{{ feeAmountDisplay }}</span>
        د.ك
        <span v-if="contract.feeFrequency === 'Monthly'">شهرياً</span>
      </p>
      <p class="text-center">{{ feeWordsAr }}.</p>

      <div class="pt-4 text-left">
        <p class="font-semibold">مكتب عبد الهادي الميلم</p>
        <p class="font-semibold">للاستشارات الهندسية</p>
      </div>
    </div>

    <hr class="border-t-2 border-dashed border-slate-300" />

    <!-- English block -->
    <div dir="ltr" lang="en" class="space-y-4 text-[15px] leading-8 text-slate-900">
      <p class="text-center text-lg font-bold">Price Quotation</p>

      <p>Date: <span class="font-medium">{{ formatDateNumeric(contract.issueDate) }}</span></p>

      <p class="flex flex-wrap justify-between gap-2">
        <span>
          Mr/
          <EditableText
            :model-value="contract.clientRepresentative"
            :editable="editable"
            placeholder="Client name"
            @update:model-value="(v) => emit('patch', { clientRepresentative: v })"
          />
        </span>
        <span class="font-semibold">Dear Sir,</span>
      </p>

      <p>Greetings,</p>

      <p>
        Project:
        <EditableText
          :model-value="contract.projectReference ?? ''"
          :editable="editable"
          placeholder="Plot No. ... – Parcel ... - Area ..."
          @update:model-value="(v) => emit('patch', { projectReference: v })"
        />
      </p>

      <p>
        Subject:
        <EditableText
          :model-value="contract.subjectLineEn ?? ''"
          :editable="editable"
          placeholder="Subject description"
          @update:model-value="(v) => emit('patch', { subjectLineEn: v })"
        />.
      </p>

      <p>We are pleased to submit a price quotation to issue the following for the above-mentioned project, which includes:</p>

      <div class="border border-slate-800 px-3 py-1 text-center font-bold">Supervision:-</div>

      <EditableList
        :model-value="contract.scopeItemsEn"
        :editable="editable"
        @update:model-value="(v) => emit('patch', { scopeItemsEn: v })"
      />

      <div class="border border-slate-800 px-3 py-1 text-center font-bold">Financial Offer:-</div>

      <p class="text-center">
        The consultancy fees for the above-mentioned phases amount to KD
        <span class="font-semibold">{{ feeAmountDisplay }}</span>/-
        <span v-if="contract.feeFrequency === 'Monthly'">monthly</span>
      </p>
      <p class="text-center">{{ feeWordsEn }}.</p>

      <div class="pt-4 text-right">
        <p class="font-semibold">Office of Abdul Hadi Al-Mailam</p>
        <p class="font-semibold">Engineering Consultants</p>
      </div>
    </div>
  </div>
</template>
