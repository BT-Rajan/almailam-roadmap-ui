<script setup lang="ts">
import { Landmark } from '@lucide/vue'
import { computed } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import AuthorityCard from '@/components/government/AuthorityCard.vue'
import { useGovernmentFormStore } from '@/stores/governmentFormStore'
import type { GovernmentAuthority } from '@/types/Government'

const emit = defineEmits<{
  open: [authority: GovernmentAuthority]
  add: []
  edit: [authority: GovernmentAuthority]
  delete: [authority: GovernmentAuthority]
}>()

const store = useGovernmentFormStore()

const authorityFormCounts = computed<Record<string, number>>(() => {
  const counts: Record<string, number> = {}
  store.forms
    .filter((form) => form.status === 'Active')
    .forEach((form) => {
      counts[form.authorityId] = (counts[form.authorityId] ?? 0) + 1
    })
  return counts
})

function loadData(): void {
  store.loadForms()
}
</script>

<template>
  <PageHeader title="Government Forms Library" subtitle="Browse government authorities and their submission forms.">
    <template #actions>
      <BaseButton :icon="Landmark" @click="emit('add')">Add Authority</BaseButton>
    </template>
  </PageHeader>

  <ErrorState v-if="store.error" :description="store.error" @retry="loadData" />

  <div v-else-if="store.isLoading" class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
    <div v-for="placeholder in 6" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="5" />
    </div>
  </div>

  <EmptyState
    v-else-if="store.authorities.length === 0"
    title="No authorities found"
    description="Add a government authority to get started."
    action-label="Add Authority"
    @action="emit('add')"
  />

  <div v-else class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
    <AuthorityCard
      v-for="authority in store.authorities"
      :key="authority.id"
      :authority="authority"
      :form-count="authorityFormCounts[authority.id] ?? 0"
      @open="emit('open', authority)"
      @edit="emit('edit', authority)"
      @delete="emit('delete', authority)"
    />
  </div>
</template>
