<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import { ICONS } from '@/utils/icons'
import type { NavItem } from '@/types/Navigation'

const props = defineProps<{
  item: NavItem
  collapsed?: boolean
}>()

const route = useRoute()

const icon = computed(() => ICONS[props.item.icon])
const isActive = computed(() => route.path.startsWith(props.item.matchPath))
</script>

<template>
  <RouterLink
    :to="{ name: item.routeName }"
    class="group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-fast"
    :class="[
      isActive
        ? 'bg-[var(--color-bg-selected)] text-primary-700'
        : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-primary)]',
    ]"
  >
    <component :is="icon" :size="20" class="shrink-0" aria-hidden="true" />
    <span v-if="!collapsed" class="truncate">{{ item.label }}</span>
  </RouterLink>
</template>
