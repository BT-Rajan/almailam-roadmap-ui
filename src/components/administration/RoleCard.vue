<script setup lang="ts">
import Card from '@/components/common/Card.vue'
import PermissionMatrix from '@/components/administration/PermissionMatrix.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { RoleDefinition } from '@/types/Role'

interface Props {
  definition: RoleDefinition
  userCount: number
}

defineProps<Props>()
</script>

<template>
  <Card>
    <template #header>
      <div class="flex items-center justify-between gap-2">
        <h3 class="text-sm font-semibold text-neutral-800">{{ definition.role }}</h3>
        <StatusBadge :label="`${userCount} ${userCount === 1 ? 'user' : 'users'}`" variant="neutral" />
      </div>
    </template>

    <p class="mb-4 text-sm text-neutral-500">{{ definition.description }}</p>
    <PermissionMatrix :permissions="definition.permissions" />
  </Card>
</template>
