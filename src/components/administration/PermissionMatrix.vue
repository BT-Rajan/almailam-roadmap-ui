<script setup lang="ts">
import { Check, Minus } from '@lucide/vue'

import type { RolePermission } from '@/types/Role'

interface Props {
  permissions: RolePermission[]
}

defineProps<Props>()
</script>

<template>
  <table class="w-full border-collapse text-sm">
    <thead>
      <tr class="border-b border-border-light">
        <th class="py-2 text-left text-xs font-semibold uppercase tracking-wide text-neutral-500">Module</th>
        <th class="py-2 text-center text-xs font-semibold uppercase tracking-wide text-neutral-500">View</th>
        <th class="py-2 text-center text-xs font-semibold uppercase tracking-wide text-neutral-500">Edit</th>
        <th class="py-2 text-center text-xs font-semibold uppercase tracking-wide text-neutral-500">Delete</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="permission in permissions" :key="permission.module" class="border-b border-border-light last:border-0">
        <td class="py-2 text-neutral-700">{{ permission.module }}</td>
        <td class="py-2 text-center">
          <Check v-if="permission.view" :size="15" class="mx-auto text-success-600" />
          <Minus v-else :size="15" class="mx-auto text-neutral-300" />
        </td>
        <td class="py-2 text-center">
          <Check v-if="permission.edit" :size="15" class="mx-auto text-success-600" />
          <Minus v-else :size="15" class="mx-auto text-neutral-300" />
        </td>
        <td class="py-2 text-center">
          <Check v-if="permission.delete" :size="15" class="mx-auto text-success-600" />
          <Minus v-else :size="15" class="mx-auto text-neutral-300" />
        </td>
      </tr>
    </tbody>
  </table>
</template>
