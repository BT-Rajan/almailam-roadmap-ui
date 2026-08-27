<script setup lang="ts">
import { onMounted } from 'vue'

import Card from '@/components/common/Card.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { useGovernmentFormStore } from '@/stores/governmentFormStore'
import { useServiceCatalogStore } from '@/stores/serviceCatalogStore'
import { useToastStore } from '@/stores/toastStore'
import type { GovernmentForm } from '@/types/Government'

// The single source of truth for "which service needs which document" --
// a GovernmentForm's own serviceTags (see GovernmentFormFormDialog.vue's
// Tagged Services grid). This page is the same relationship viewed and
// edited from the other side: by service, instead of by form. There is
// deliberately no separate table or duplicate list behind this screen --
// toggling a checkbox here calls the exact same updateForm action the
// Government Forms admin screen uses, so the two screens can never drift
// out of sync with each other.
const governmentFormStore = useGovernmentFormStore()
const serviceCatalogStore = useServiceCatalogStore()
const toastStore = useToastStore()

onMounted(() => {
  if (governmentFormStore.forms.length === 0) governmentFormStore.loadForms()
  if (serviceCatalogStore.services.length === 0) serviceCatalogStore.loadServices()
})

const isLoading = () => governmentFormStore.isLoading || serviceCatalogStore.isLoading

function fillableForms(): GovernmentForm[] {
  return governmentFormStore.forms.filter((form) => form.status === 'Active' && Boolean(form.template))
}

function isTagged(form: GovernmentForm, serviceName: string): boolean {
  return (form.serviceTags ?? []).includes(serviceName)
}

async function toggle(form: GovernmentForm, serviceName: string): Promise<void> {
  const serviceTags = isTagged(form, serviceName)
    ? (form.serviceTags ?? []).filter((tag) => tag !== serviceName)
    : [...new Set([...(form.serviceTags ?? []), serviceName])]

  try {
    await governmentFormStore.updateForm(form.id, {
      authorityId: form.authorityId,
      formCode: form.formCode,
      title: form.title,
      version: form.version,
      language: form.language,
      category: form.category,
      description: form.description,
      requiredDocuments: form.requiredDocuments,
      lastUpdated: form.lastUpdated,
      status: form.status,
      previewUrl: form.previewUrl,
      template: form.template,
      serviceTags,
    })
  } catch (error) {
    toastStore.show('error', 'Failed to update', error instanceof Error ? error.message : 'Please try again.')
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader
      title="Service Document Map"
      subtitle="For each service, which fillable government forms/agreements a project needs. Staff fill these in from the project itself (Approvals & Permits) -- this only controls which ones are offered there."
    />

    <ErrorState v-if="governmentFormStore.error" :description="governmentFormStore.error" @retry="governmentFormStore.loadForms" />

    <template v-else-if="isLoading()">
      <div v-for="n in 3" :key="n" class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="3" />
      </div>
    </template>

    <EmptyState
      v-else-if="serviceCatalogStore.services.length === 0"
      title="No services in the catalog yet"
      description="Add services under Administration > Service Catalog first."
    />

    <EmptyState
      v-else-if="fillableForms().length === 0"
      title="No fillable forms yet"
      description="Add Template Content to a form under Administration > Government Forms Management to make it assignable here."
    />

    <div v-else class="flex flex-col gap-4">
      <Card v-for="service in serviceCatalogStore.services" :key="service.id">
        <template #header>
          <h3 class="text-sm font-semibold text-text-primary">{{ service.name }}</h3>
        </template>
        <div class="grid grid-cols-1 gap-1.5 tablet:grid-cols-2">
          <Checkbox
            v-for="form in fillableForms()"
            :key="form.id"
            :model-value="isTagged(form, service.name)"
            :label="`${form.formCode} · ${form.title}`"
            @update:model-value="toggle(form, service.name)"
          />
        </div>
      </Card>
    </div>
  </div>
</template>
