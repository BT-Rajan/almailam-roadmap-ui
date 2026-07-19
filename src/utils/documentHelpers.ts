import { Calculator, FileSignature, FileSpreadsheet, FileText, Landmark, Ruler } from '@lucide/vue'
import type { Component } from 'vue'

import type { BadgeVariant } from '@/types/Ui'
import type { DocumentStatus, DocumentType } from '@/types/Document'

const STATUS_VARIANTS: Record<DocumentStatus, BadgeVariant> = {
  Draft: 'neutral',
  'Under Review': 'warning',
  Approved: 'success',
  Rejected: 'danger',
}

const TYPE_ICONS: Record<DocumentType, Component> = {
  Drawing: Ruler,
  Report: FileText,
  Contract: FileSignature,
  Quotation: FileSpreadsheet,
  'Municipality Form': Landmark,
  'Calculation Sheet': Calculator,
}

export function getDocumentStatusVariant(status: DocumentStatus): BadgeVariant {
  return STATUS_VARIANTS[status]
}

export function getDocumentTypeIcon(type: DocumentType): Component {
  return TYPE_ICONS[type]
}
