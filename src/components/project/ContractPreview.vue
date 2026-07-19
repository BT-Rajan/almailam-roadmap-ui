<script setup lang="ts">
import { FileSignature } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import Divider from '@/components/common/Divider.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { getContractStatusVariant } from '@/utils/contractHelpers'
import type { Client } from '@/types/Client'
import type { Contract } from '@/types/Contract'
import type { Project } from '@/types/Project'

interface Props {
  contract: Contract
  project: Project
  client?: Client
}

withDefaults(defineProps<Props>(), {
  client: undefined,
})
</script>

<template>
  <Card class="print:shadow-none" :padded="true">
    <div id="contract-print-area" class="flex flex-col gap-6">
      <div class="flex flex-col gap-4 tablet:flex-row tablet:items-start tablet:justify-between">
        <div class="flex items-center gap-3">
          <span class="flex h-11 w-11 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
            <FileSignature class="h-5 w-5" />
          </span>
          <div>
            <p class="text-sm font-semibold text-neutral-800">Almailam Engineering Consultants</p>
            <p class="text-xs text-neutral-500">Engineering Design & Government Approvals</p>
          </div>
        </div>

        <div class="flex flex-col gap-1 tablet:items-end">
          <div class="flex items-center gap-2">
            <h2 class="text-lg font-semibold text-neutral-800">{{ contract.contractNo }}</h2>
            <StatusBadge :label="contract.status" :variant="getContractStatusVariant(contract.status)" />
          </div>
          <p class="text-xs text-neutral-500">Revision {{ contract.revision }} · {{ contract.templateName }}</p>
        </div>
      </div>

      <Divider />

      <div class="grid grid-cols-1 gap-6 tablet:grid-cols-3">
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Client</p>
          <p class="text-sm font-semibold text-neutral-800">{{ client?.companyName ?? 'Unknown Client' }}</p>
          <p class="text-sm text-neutral-500">Represented by {{ contract.clientRepresentative }}</p>
        </div>
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Project</p>
          <p class="text-sm font-semibold text-neutral-800">{{ project.projectName }}</p>
          <p class="text-sm text-neutral-500">{{ project.projectNo }} · {{ project.service }}</p>
        </div>
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Dates</p>
          <p class="text-sm text-neutral-500">Issued: {{ formatDate(contract.issueDate) }}</p>
          <p v-if="contract.signedDate" class="text-sm text-neutral-500">
            Signed: {{ formatDate(contract.signedDate) }}
          </p>
          <p class="text-sm text-neutral-500">Expires: {{ formatDate(contract.expiryDate) }}</p>
        </div>
      </div>

      <Divider />

      <div class="flex flex-col gap-2">
        <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Scope Summary</p>
        <p class="text-sm leading-relaxed text-neutral-600">{{ contract.scopeSummary }}</p>
      </div>

      <div class="flex items-center justify-between rounded-lg bg-bg-secondary px-4 py-3">
        <span class="text-sm font-medium text-neutral-600">Contract Value</span>
        <span class="text-lg font-semibold text-primary-700">
          {{ formatCurrency(contract.contractValue, contract.currency) }}
        </span>
      </div>

      <div class="flex flex-col gap-4">
        <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Clauses</p>
        <div
          v-for="(clause, index) in contract.clauses"
          :key="clause.id"
          class="flex flex-col gap-1 border-b border-border-light pb-4 last:border-0 last:pb-0"
        >
          <p class="text-sm font-semibold text-neutral-800">{{ index + 1 }}. {{ clause.title }}</p>
          <p class="text-sm leading-relaxed text-neutral-600">{{ clause.content }}</p>
        </div>
      </div>

      <p class="no-print text-center text-xs text-neutral-400">
        This is a prototype preview. Final legal documents are prepared and issued outside this system.
      </p>
    </div>
  </Card>
</template>
