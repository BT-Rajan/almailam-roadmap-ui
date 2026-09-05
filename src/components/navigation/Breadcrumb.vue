<script setup lang="ts">
import { ChevronRight } from '@lucide/vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

const route = useRoute()
const { t } = useI18n()
</script>

<template>
  <nav
    v-if="route.meta.breadcrumbs?.length"
    :aria-label="t('common.breadcrumbNav')"
    class="flex h-11 shrink-0 items-center gap-1.5 border-b border-[var(--color-border-light)] bg-bg-secondary px-4 text-sm lg:px-6"
  >
    <template v-for="(crumb, index) in route.meta.breadcrumbs" :key="`${crumb.label}-${index}`">
      <ChevronRight
        v-if="index > 0"
        :size="14"
        class="text-[var(--color-text-muted)]"
        aria-hidden="true"
      />
      <RouterLink
        v-if="crumb.routeName"
        :to="{ name: crumb.routeName }"
        class="text-[var(--color-text-secondary)] transition-colors duration-fast hover:text-[var(--color-text-primary)]"
      >
        {{ t(crumb.label) }}
      </RouterLink>
      <span v-else class="font-medium text-[var(--color-text-primary)]">
        {{ t(crumb.label) }}
      </span>
    </template>
  </nav>
</template>
