<script setup lang="ts">
import { Download, Printer } from '@lucide/vue'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import BaseButton from '@/components/common/BaseButton.vue'
import { PUBLIC_LOGO_URL } from '@/services/companyService'
import { useCompanyStore } from '@/stores/companyStore'

const { t } = useI18n()
const companyStore = useCompanyStore()

// Unlike BrandMark's app-chrome usage, a report with no uploaded logo
// just shows its title alone -- no placeholder badge to fall back to.
const logoFailed = ref(false)
watch(() => companyStore.branding?.hasLogo, () => { logoFailed.value = false })

interface Props {
  title: string
  subtitle?: string
  generatedDate?: string
  showActions?: boolean
}

withDefaults(defineProps<Props>(), {
  subtitle: undefined,
  generatedDate: undefined,
  showActions: true,
})

defineEmits<{
  print: []
  download: []
}>()

const handlePrint = () => {
  window.print()
}
</script>

<template>
  <div class="space-y-4 pb-6 border-b border-border-light print:border-b-0">
    <div class="flex items-start justify-between gap-4">
      <div class="flex items-start gap-4">
        <img
          v-if="companyStore.branding?.hasLogo && !logoFailed"
          :src="PUBLIC_LOGO_URL"
          :alt="companyStore.branding.companyName"
          class="h-12 w-12 shrink-0 rounded-lg border border-border-light bg-white object-contain p-1"
          @error="logoFailed = true"
        />
        <div>
          <h1 class="font-display text-3xl font-semibold text-text-primary">{{ title }}</h1>
          <p v-if="subtitle" class="text-text-secondary mt-1">{{ subtitle }}</p>
          <p v-if="generatedDate" class="text-xs text-text-muted mt-2">{{ t('report.header.generatedLabel', { date: generatedDate }) }}</p>
        </div>
      </div>
      <div v-if="showActions" class="flex gap-2 print:hidden">
        <BaseButton variant="ghost" size="sm" @click="handlePrint">
          <Printer class="h-4 w-4" />
          {{ t('report.header.print') }}
        </BaseButton>
        <BaseButton variant="ghost" size="sm" @click="$emit('download')">
          <Download class="h-4 w-4" />
          {{ t('report.header.export') }}
        </BaseButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
@media print {
  :deep(button) {
    display: none;
  }
}
</style>
