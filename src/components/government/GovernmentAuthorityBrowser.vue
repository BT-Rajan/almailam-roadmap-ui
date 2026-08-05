<script setup lang="ts">
import { Landmark } from '@lucide/vue'
import { computed, ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
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

const searchTerm = ref('')

const visibleAuthorities = computed<GovernmentAuthority[]>(() => {
  const term = searchTerm.value.trim().toLowerCase()
  if (term.length === 0) return store.authorities
  return store.authorities.filter(
    (authority) =>
      authority.name.toLowerCase().includes(term) || authority.category.toLowerCase().includes(term),
  )
})

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

  <FilterBar
    :search-value="searchTerm"
    search-placeholder="Search authorities by name or category"
    :has-active-filters="searchTerm.trim().length > 0"
    @update:search-value="searchTerm = $event"
    @clear="searchTerm = ''"
  />

  <ErrorState v-if="store.error" :description="store.error" @retry="loadData" />

  <div v-else-if="store.isLoading" class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
    <div v-for="placeholder in 6" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="5" />
    </div>
  </div>

  <EmptyState
    v-else-if="visibleAuthorities.length === 0"
    title="No authorities found"
    description="Try a different search, or add a government authority to get started."
    action-label="Add Authority"
    @action="emit('add')"
  />

  <div v-else class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
    <AuthorityCard
      v-for="authority in visibleAuthorities"
      :key="authority.id"
      :authority="authority"
      :form-count="authorityFormCounts[authority.id] ?? 0"
      @open="emit('open', authority)"
      @edit="emit('edit', authority)"
      @delete="emit('delete', authority)"
    />
  </div>
</template>
