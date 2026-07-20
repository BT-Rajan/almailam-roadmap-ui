<script setup lang="ts">
import { Mail, Phone } from '@lucide/vue'

import Avatar from '@/components/common/Avatar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { AppUser } from '@/types/User'
import { getUserRoleVariant, getUserStatusVariant } from '@/utils/userHelpers'

interface Props {
  user: AppUser
}

defineProps<Props>()
</script>

<template>
  <div class="flex flex-col gap-4 rounded-xl border border-border-light bg-bg-card p-5 shadow-soft">
    <div class="flex items-start gap-4">
      <Avatar :name="user.name" size="lg" />
      <div class="min-w-0 flex-1">
        <p class="text-base font-semibold text-neutral-900">{{ user.name }}</p>
        <p class="text-sm text-neutral-500">{{ user.designation }}</p>
        <div class="mt-2 flex flex-wrap items-center gap-2">
          <StatusBadge :label="user.role" :variant="getUserRoleVariant(user.role)" />
          <StatusBadge :label="user.status" :variant="getUserStatusVariant(user.status)" show-dot />
        </div>
      </div>
    </div>

    <div class="flex flex-col gap-2 border-t border-border-light pt-4 text-sm text-neutral-600">
      <div class="flex items-center gap-2">
        <Mail :size="15" class="text-neutral-400" />
        {{ user.email }}
      </div>
      <div class="flex items-center gap-2">
        <Phone :size="15" class="text-neutral-400" />
        {{ user.mobile }}
      </div>
    </div>
  </div>
</template>
