<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import AuthorityFormsPanel from '@/components/government/AuthorityFormsPanel.vue'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { useProjectFormStore } from '@/stores/projectFormStore'
import type { GovernmentAuthority } from '@/types/Government'

const props = defineProps<{
  projectId: string
}>()

const governmentSubmissionStore = useGovernmentSubmissionStore()
const projectFormStore = useProjectFormStore()
const { t } = useI18n()

// One tab per authority admin has configured (Administration >
// Government Forms) -- add MEW, KFD, Baladia, or any other authority
// there and it shows up here automatically, no code change needed.
// Every tab behaves identically -- see AuthorityFormsPanel.vue, the one
// component rendered once per authority below.
const orderedAuthorities = computed<GovernmentAuthority[]>(() =>
  [...governmentSubmissionStore.authorities].sort((a, b) => a.name.localeCompare(b.name)),
)

const activeAuthorityId = ref<string | undefined>(undefined)

watch(
  orderedAuthorities,
  (authorities) => {
    if (!activeAuthorityId.value || !authorities.some((a) => a.id === activeAuthorityId.value)) {
      activeAuthorityId.value = authorities[0]?.id
    }
  },
  { immediate: true },
)

function loadData(): void {
  governmentSubmissionStore.loadSubmissions()
  projectFormStore.load(props.projectId)
}

onMounted(loadData)
watch(() => props.projectId, loadData)
</script>

<template>
  <div class="flex flex-col gap-4">
    <ErrorState
      v-if="governmentSubmissionStore.error || projectFormStore.error"
      :description="governmentSubmissionStore.error || projectFormStore.error"
      @retry="loadData"
    />

    <div v-else-if="governmentSubmissionStore.isLoading || projectFormStore.isLoading" class="rounded-xl border border-border-light bg-bg-card p-6">
      <SkeletonLoader :rows="8" />
    </div>

    <template v-else-if="orderedAuthorities.length === 0">
      <p class="text-sm text-text-muted">
        {{ t('project.governmentTab.noAuthoritiesConfigured') }}
      </p>
    </template>

    <template v-else>
      <div class="flex gap-1 overflow-x-auto border-b border-border-light no-print" role="tablist">
        <button
          v-for="authority in orderedAuthorities"
          :key="authority.id"
          type="button"
          role="tab"
          class="shrink-0 whitespace-nowrap rounded-t-md border-b-2 px-4 py-3 text-sm font-medium transition-colors duration-fast focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500"
          :class="
            activeAuthorityId === authority.id
              ? 'border-accent-500 text-accent-700 dark:text-accent-400'
              : 'border-transparent text-text-muted hover:text-text-primary'
          "
          :aria-selected="activeAuthorityId === authority.id"
          @click="activeAuthorityId = authority.id"
        >
          {{ authority.name }}
        </button>
      </div>

      <AuthorityFormsPanel
        v-if="activeAuthorityId"
        :key="activeAuthorityId"
        :project-id="projectId"
        :authority-id="activeAuthorityId"
      />
    </template>
  </div>
</template>
