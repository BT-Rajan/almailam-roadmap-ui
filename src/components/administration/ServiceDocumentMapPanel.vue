<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { useGovernmentFormStore } from '@/stores/governmentFormStore'
import { useServiceCatalogStore } from '@/stores/serviceCatalogStore'
import { useToastStore } from '@/stores/toastStore'
import type { GovernmentForm } from '@/types/Government'

// The single source of truth for "which service needs which document" --
// a GovernmentForm's own serviceTags (see GovernmentFormFormDialog.vue's
// Tagged Services grid). This panel is the same relationship viewed and
// edited from the other side: by service, instead of by form. There is
// deliberately no separate table or duplicate list behind this screen --
// toggling a checkbox here calls the exact same updateForm action the
// Government Forms panel uses, so the two panels can never drift out of
// sync with each other.
const { t } = useI18n()
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

// One form is tagged to several services at once, and checking several
// of its checkboxes in a normal, quick clicking pace is the expected
// workflow here -- but each toggle used to read form.serviceTags fresh
// from the store and PATCH a whole new array, with no serialization.
// Two toggles fired before either request resolved would both compute
// their new array from the SAME starting point, so whichever PATCH
// landed last silently discarded the other's change (confirmed live:
// checking two boxes for one form in quick succession only ever kept
// one). pendingTagsByFormId is the synchronous, always-current draft
// every checkbox reads/writes; saveChainByFormId serializes the actual
// network calls per form so a later save always starts from the
// latest draft rather than a stale snapshot, and out-of-order in-flight
// requests can't stomp each other's results either.
const pendingTagsByFormId = reactive<Record<string, string[]>>({})
const saveChainByFormId: Record<string, Promise<unknown>> = {}

function currentTags(form: GovernmentForm): string[] {
  return pendingTagsByFormId[form.id] ?? form.serviceTags ?? []
}

function isTagged(form: GovernmentForm, serviceName: string): boolean {
  return currentTags(form).includes(serviceName)
}

async function toggle(form: GovernmentForm, serviceName: string): Promise<void> {
  const tags = currentTags(form)
  const nextTags = tags.includes(serviceName) ? tags.filter((tag) => tag !== serviceName) : [...tags, serviceName]
  pendingTagsByFormId[form.id] = nextTags

  const previousSave = saveChainByFormId[form.id] ?? Promise.resolve()
  const thisSave = previousSave.catch(() => undefined).then(() =>
    governmentFormStore.updateForm(form.id, {
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
      // Read at execution time, not capture time -- picks up every
      // click queued ahead of it, including ones that landed after
      // this toggle() call returned.
      serviceTags: pendingTagsByFormId[form.id] ?? nextTags,
      fields: form.fields,
    }),
  )
  saveChainByFormId[form.id] = thisSave

  try {
    await thisSave
    // The store's own form.serviceTags now matches what was just saved
    // -- safe to drop the local override so future reads (including a
    // reload of this list) go back to the single source of truth.
    if (pendingTagsByFormId[form.id] === nextTags) delete pendingTagsByFormId[form.id]
  } catch (error) {
    delete pendingTagsByFormId[form.id]
    toastStore.show('error', t('administration.serviceDocumentMap.failedToUpdate'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  }
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <ErrorState v-if="governmentFormStore.error" :description="governmentFormStore.error" @retry="governmentFormStore.loadForms" />

    <template v-else-if="isLoading()">
      <div v-for="n in 3" :key="n" class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="3" />
      </div>
    </template>

    <EmptyState
      v-else-if="serviceCatalogStore.services.length === 0"
      :title="t('administration.serviceDocumentMap.noServicesYet')"
      :description="t('administration.serviceDocumentMap.noServicesYetDescription')"
    />

    <EmptyState
      v-else-if="fillableForms().length === 0"
      :title="t('administration.serviceDocumentMap.noFillableFormsYet')"
      :description="t('administration.serviceDocumentMap.noFillableFormsYetDescription')"
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
