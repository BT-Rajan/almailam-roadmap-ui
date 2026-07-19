<script setup lang="ts">
import Card from '@/components/common/Card.vue'

interface DetailItem {
  label: string
  value: string
}

interface Props {
  title: string
  items: DetailItem[]
}

defineProps<Props>()
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-neutral-800">{{ title }}</h3>
    </template>
    <dl class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
      <div v-for="item in items" :key="item.label">
        <dt class="text-xs font-medium uppercase tracking-wide text-neutral-400">{{ item.label }}</dt>
        <dd class="mt-0.5 text-sm text-neutral-800">{{ item.value }}</dd>
      </div>
    </dl>
  </Card>
</template>
