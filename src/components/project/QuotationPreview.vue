<script setup lang="ts">
import { FileText } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import Divider from '@/components/common/Divider.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import PricingSummary from '@/components/project/PricingSummary.vue'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { getQuotationStatusVariant } from '@/utils/quotationHelpers'
import type { Client } from '@/types/Client'
import type { Project } from '@/types/Project'
import type { Quotation } from '@/types/Quotation'

interface Props {
  quotation: Quotation
  project: Project
  client?: Client
}

withDefaults(defineProps<Props>(), {
  client: undefined,
})
</script>

<template>
  <Card class="print:shadow-none" :padded="true">
    <div id="quotation-print-area" class="flex flex-col gap-6">
      <div class="flex flex-col gap-4 tablet:flex-row tablet:items-start tablet:justify-between">
        <div class="flex items-center gap-3">
          <span class="flex h-11 w-11 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
            <FileText class="h-5 w-5" />
          </span>
          <div>
            <p class="text-sm font-semibold text-neutral-800">Almailam Engineering Consultants</p>
            <p class="text-xs text-neutral-500">Engineering Design & Government Approvals</p>
          </div>
        </div>

        <div class="flex flex-col gap-1 tablet:items-end">
          <div class="flex items-center gap-2">
            <h2 class="text-lg font-semibold text-neutral-800">{{ quotation.quotationNo }}</h2>
            <StatusBadge :label="quotation.status" :variant="getQuotationStatusVariant(quotation.status)" />
          </div>
          <p class="text-xs text-neutral-500">Revision {{ quotation.revision }}</p>
        </div>
      </div>

      <Divider />

      <div class="grid grid-cols-1 gap-6 tablet:grid-cols-3">
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Bill To</p>
          <p class="text-sm font-semibold text-neutral-800">{{ client?.companyName ?? 'Unknown Client' }}</p>
          <p class="text-sm text-neutral-500">{{ client?.contactPerson }}</p>
          <p class="text-sm text-neutral-500">{{ client?.city }}</p>
        </div>
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Project</p>
          <p class="text-sm font-semibold text-neutral-800">{{ project.projectName }}</p>
          <p class="text-sm text-neutral-500">{{ project.projectNo }} · {{ project.service }}</p>
        </div>
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Dates</p>
          <p class="text-sm text-neutral-500">Issued: {{ formatDate(quotation.issueDate) }}</p>
          <p class="text-sm text-neutral-500">Valid Until: {{ formatDate(quotation.validity) }}</p>
          <p class="text-sm text-neutral-500">Prepared By: {{ quotation.preparedBy }}</p>
        </div>
      </div>

      <Divider />

      <div class="overflow-x-auto">
        <table class="w-full border-collapse">
          <thead>
            <tr class="border-b border-border-light bg-bg-secondary">
              <th class="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Description
              </th>
              <th class="px-3 py-2.5 text-right text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Qty
              </th>
              <th class="px-3 py-2.5 text-right text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Unit Price
              </th>
              <th class="px-3 py-2.5 text-right text-xs font-semibold uppercase tracking-wide text-neutral-500">
                Amount
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in quotation.lineItems" :key="item.id" class="border-b border-border-light last:border-0">
              <td class="px-3 py-3 text-sm text-neutral-700">{{ item.description }}</td>
              <td class="px-3 py-3 text-right text-sm text-neutral-600">{{ item.quantity }}</td>
              <td class="px-3 py-3 text-right text-sm text-neutral-600">
                {{ formatCurrency(item.unitPrice, quotation.currency) }}
              </td>
              <td class="px-3 py-3 text-right text-sm font-medium text-neutral-800">
                {{ formatCurrency(item.quantity * item.unitPrice, quotation.currency) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="flex justify-end">
        <div class="w-full tablet:w-80">
          <PricingSummary :quotation="quotation" />
        </div>
      </div>

      <div v-if="quotation.notes" class="flex flex-col gap-1">
        <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Notes</p>
        <p class="text-sm text-neutral-600">{{ quotation.notes }}</p>
      </div>

      <div class="flex flex-col gap-2">
        <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Terms & Conditions</p>
        <ul class="flex flex-col gap-1">
          <li
            v-for="(term, index) in quotation.termsAndConditions"
            :key="index"
            class="flex gap-2 text-sm text-neutral-500"
          >
            <span class="text-neutral-300">•</span>
            <span>{{ term }}</span>
          </li>
        </ul>
      </div>
    </div>
  </Card>
</template>
