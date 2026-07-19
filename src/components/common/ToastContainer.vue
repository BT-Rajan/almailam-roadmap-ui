<script setup lang="ts">
import { storeToRefs } from 'pinia'

import Toast from '@/components/common/Toast.vue'
import { useToastStore } from '@/stores/toastStore'

const toastStore = useToastStore()
const { toasts } = storeToRefs(toastStore)
</script>

<template>
  <Teleport to="body">
    <div class="fixed right-4 top-4 z-notification flex flex-col gap-3">
      <Toast
        v-for="toast in toasts"
        :key="toast.id"
        :toast="toast"
        @dismiss="toastStore.dismiss"
      />
    </div>
  </Teleport>
</template>
