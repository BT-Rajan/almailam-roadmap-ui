<script setup lang="ts">
import { Bell, Calendar, ChevronLeft, ChevronRight, Menu, MessageSquare, Search, Sparkles } from '@lucide/vue'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import UserMenu from '@/components/navigation/UserMenu.vue'
import { useLocale } from '@/composables/useLocale'
import { useRbac } from '@/composables/useRbac'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useKnowledgeStore } from '@/stores/knowledgeStore'
import { useNavigationStore } from '@/stores/navigationStore'
import { useNotificationStore } from '@/stores/notificationStore'
import { useSearchStore } from '@/stores/searchStore'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isRtl } = useLocale()
const navigationStore = useNavigationStore()
const notificationStore = useNotificationStore()
const searchStore = useSearchStore()
const knowledgeStore = useKnowledgeStore()
const { can } = useRbac()

// The separator points the way the breadcrumb trail reads, which
// reverses with reading direction.
const separatorIcon = computed(() => (isRtl.value ? ChevronLeft : ChevronRight))

onMounted(() => {
  void notificationStore.loadNotifications()
  if (knowledgeStore.isEnabled === undefined) void knowledgeStore.loadStatus()
})
</script>

<template>
  <div class="flex shrink-0 flex-col">
    <header class="flex h-16 shrink-0 items-center gap-4 border-b border-[var(--color-border-default)] bg-bg-header px-4 shadow-glass-sm lg:px-6">
      <div class="flex items-center gap-3">
        <button
          type="button"
          class="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)] lg:hidden"
          :aria-label="t('common.openNavigationMenu')"
          @click="navigationStore.openMobileSidebar"
        >
          <Menu :size="20" />
        </button>

        <button
          type="button"
          class="relative hidden w-72 items-center rounded-lg border border-[var(--color-border-default)] bg-bg-secondary py-2 ps-9 pe-3 text-start text-sm text-[var(--color-text-muted)] transition-colors duration-fast hover:border-accent-400 md:flex"
          @click="searchStore.open"
        >
          <Search :size="16" class="pointer-events-none absolute start-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" />
          <span class="flex-1 truncate">{{ t('common.searchGlobalPlaceholder') }}</span>
          <kbd class="rounded border border-[var(--color-border-default)] bg-[var(--color-bg-card)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--color-text-muted)]">
            Ctrl K
          </kbd>
        </button>
      </div>

      <div class="ms-auto flex items-center gap-2">
        <button
          v-if="can('knowledgebase.view') && knowledgeStore.isEnabled !== false"
          type="button"
          class="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--color-text-secondary)] transition-colors duration-fast hover:bg-[var(--color-bg-hover)]"
          :aria-label="t('common.knowledgeAssistant')"
          @click="knowledgeStore.toggleDrawer"
        >
          <Sparkles :size="18" />
        </button>

        <button
          v-if="can('activity.view')"
          type="button"
          class="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--color-text-secondary)] transition-colors duration-fast hover:bg-[var(--color-bg-hover)]"
          :aria-label="t('common.activityCalendar')"
          @click="router.push({ name: ROUTE_NAMES.ADMIN_ACTIVITY_CALENDAR })"
        >
          <Calendar :size="18" />
        </button>

        <button
          type="button"
          class="relative flex h-9 w-9 items-center justify-center rounded-lg text-[var(--color-text-secondary)] transition-colors duration-fast hover:bg-[var(--color-bg-hover)]"
          :aria-label="t('common.notifications')"
          @click="notificationStore.toggleDrawer"
        >
          <Bell :size="18" />
          <span
            v-if="notificationStore.hasUnread"
            class="absolute end-1.5 top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-danger-500 px-1 text-[10px] font-semibold leading-none text-white"
            aria-hidden="true"
          >
            {{ notificationStore.unreadCount > 9 ? '9+' : notificationStore.unreadCount }}
          </span>
        </button>

        <button
          type="button"
          class="flex h-9 w-9 items-center justify-center rounded-lg text-[var(--color-text-secondary)] transition-colors duration-fast hover:bg-[var(--color-bg-hover)]"
          :aria-label="t('common.messageCentre')"
          @click="router.push({ name: ROUTE_NAMES.MESSAGE_CENTRE })"
        >
          <MessageSquare :size="18" />
        </button>

        <UserMenu />
      </div>
    </header>

    <!-- Its own row below the header now, instead of sharing the h-16
         row -- sharing made the trail compete for space with the search
         box and icon cluster and get squeezed. -->
    <nav
      v-if="route.meta.breadcrumbs?.length"
      :aria-label="t('common.breadcrumbNav')"
      class="hidden min-w-0 items-center gap-1.5 truncate border-b border-[var(--color-border-default)] bg-bg-header px-4 py-2 text-sm lg:flex lg:px-6"
    >
      <template v-for="(crumb, index) in route.meta.breadcrumbs" :key="`${crumb.label}-${index}`">
        <component :is="separatorIcon" v-if="index > 0" :size="14" class="shrink-0 text-[var(--color-text-muted)]" aria-hidden="true" />
        <RouterLink
          v-if="crumb.routeName"
          :to="{ name: crumb.routeName }"
          class="truncate text-[var(--color-text-secondary)] transition-colors duration-fast hover:text-[var(--color-text-primary)]"
        >
          {{ t(crumb.label) }}
        </RouterLink>
        <span v-else class="truncate font-medium text-[var(--color-text-primary)]">
          {{ t(crumb.label) }}
        </span>
      </template>
    </nav>
  </div>
</template>
