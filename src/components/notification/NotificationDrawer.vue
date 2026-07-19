<script setup lang="ts">
import { BellOff, CheckCheck } from '@lucide/vue'
import { useRouter } from 'vue-router'

import BaseDrawer from '@/components/common/BaseDrawer.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import Loader from '@/components/common/Loader.vue'
import NotificationItem from '@/components/notification/NotificationItem.vue'
import { useNotificationStore } from '@/stores/notificationStore'
import type { AppNotification } from '@/types/Notification'

const notificationStore = useNotificationStore()
const router = useRouter()

const handleSelect = async (notification: AppNotification): Promise<void> => {
  await notificationStore.markAsRead(notification.id)
  notificationStore.closeDrawer()
  if (notification.link) {
    router.push({ name: notification.link.routeName, params: notification.link.params })
  }
}
</script>

<template>
  <BaseDrawer
    :model-value="notificationStore.isDrawerOpen"
    title="Notifications"
    width="md"
    @update:model-value="notificationStore.closeDrawer"
  >
    <template v-if="notificationStore.hasUnread" #footer>
      <button
        type="button"
        class="flex w-full items-center justify-center gap-2 text-sm font-medium text-primary-600 hover:text-primary-700"
        @click="notificationStore.markAllAsRead"
      >
        <CheckCheck :size="16" />
        Mark all as read
      </button>
    </template>

    <Loader v-if="notificationStore.isLoading" label="Loading notifications..." />

    <ErrorState
      v-else-if="notificationStore.error"
      :description="notificationStore.error"
      @retry="notificationStore.loadNotifications"
    />

    <EmptyState
      v-else-if="notificationStore.notifications.length === 0"
      :icon="BellOff"
      title="No notifications yet"
      description="You're all caught up. New updates will show up here."
    />

    <div v-else class="flex flex-col gap-4">
      <section v-for="group in notificationStore.groupedNotifications" :key="group.label">
        <p class="mb-1 px-2 text-xs font-medium uppercase tracking-wide text-neutral-400">{{ group.label }}</p>
        <div class="flex flex-col divide-y divide-border-light">
          <NotificationItem
            v-for="notification in group.notifications"
            :key="notification.id"
            :notification="notification"
            @select="handleSelect"
          />
        </div>
      </section>
    </div>
  </BaseDrawer>
</template>
