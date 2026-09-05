<script setup lang="ts">
import { CheckCircle2, Circle } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import { CLIENT_ONBOARDING_REQUIREMENTS } from '@/constants/clientOptions'
import type { Client, ClientAddress, ClientContact, ClientDocument, ClientIdentification } from '@/types/Client'
import { evaluateOnboardingRequirements } from '@/utils/clientHelpers'

const props = defineProps<{
  client: Client
  documents: ClientDocument[]
  contacts: ClientContact[]
  addresses: ClientAddress[]
  identifications: ClientIdentification[]
}>()

const requirements = computed(() => CLIENT_ONBOARDING_REQUIREMENTS[props.client.clientType])

const summary = computed(() =>
  evaluateOnboardingRequirements({
    client: props.client,
    documents: props.documents,
    contacts: props.contacts,
    addresses: props.addresses,
    identifications: props.identifications,
  }),
)

function isRequirementMet(label: string): boolean {
  return summary.value.satisfiedByLabel[label] ?? false
}

const { t } = useI18n()
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('client.onboardingProgress') }}</h3>
    </template>
    <div class="flex flex-col gap-4">
      <ProgressBar :value="summary.completionPercentage" show-label />
      <ul class="flex flex-col divide-y divide-border-light">
        <li v-for="requirement in requirements" :key="requirement.label" class="flex items-center justify-between gap-3 py-2.5">
          <span class="inline-flex items-center gap-2 text-sm text-text-secondary">
            <CheckCircle2 v-if="isRequirementMet(requirement.label)" class="h-4 w-4 shrink-0 text-success-500" aria-hidden="true" />
            <Circle v-else class="h-4 w-4 shrink-0 text-text-muted" aria-hidden="true" />
            {{ t(requirement.labelKey) }}
            <!-- The icon alone only conveys met/not-met visually -- this
                 gives screen reader users the same information, since two
                 different icons next to identical text otherwise announce
                 nothing about which requirement is actually satisfied. -->
            <span class="sr-only">{{ isRequirementMet(requirement.label) ? t('client.onboardingComplete') : t('client.onboardingIncomplete') }}</span>
          </span>
          <span v-if="!requirement.required" class="text-xs text-text-muted">{{ t('common.optional') }}</span>
        </li>
      </ul>
    </div>
  </Card>
</template>
