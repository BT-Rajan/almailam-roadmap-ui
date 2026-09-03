import type { AppLanguage } from '@/types/CompanySettings'

export type DocumentTemplateType = 'Quotation' | 'Contract'

export interface DocumentTemplate {
  id: string
  documentType: DocumentTemplateType
  // Each (documentType, language) pair can have its own default (see
  // backend document_template_service.set_default) -- English and
  // Arabic templates for the same document type are independent, not
  // mutually exclusive.
  language: AppLanguage
  originalFilename: string
  fileSizeBytes: number
  isDefault: boolean
  uploadedBy: string
  uploadedAt: string
}

// One entry from the backend's merge-field catalog (see
// document_template_service.MERGE_FIELD_CATALOG) -- what the field
// mapping screen's palette offers for a document type. 'text' inserts
// {{ key }} at a clicked spot; 'repeatingTable' marks a table row as the
// repeating one, with one sub-field per column (each inserts {{
// loopVar.column }}); 'repeatingList' marks a paragraph as the
// repeating one (inserts {{ loopVar }}).
export type MergeFieldKind = 'text' | 'repeating_table' | 'repeating_list'

export interface MergeFieldColumn {
  key: string
  label: string
}

export interface MergeField {
  key: string
  label: string
  kind: MergeFieldKind
  loopVar?: string
  columns?: MergeFieldColumn[]
}

export interface TemplateCell {
  cellIndex: number
  text: string
}

export interface TemplateRow {
  rowIndex: number
  cells: TemplateCell[]
  // Set on at most one row across the whole template.
  repeatingField: string | null
}

// One paragraph or table from the template body, in document order.
// text/repeatingField apply to a 'paragraph' block; rows to a 'table'
// block. Same shape is used both for the extracted layout (GET) and the
// edited-back mapping (POST).
export interface TemplateBlock {
  kind: 'paragraph' | 'table'
  blockIndex: number
  text?: string
  repeatingField?: string | null
  rows?: TemplateRow[]
}

export interface TemplateLayout {
  blocks: TemplateBlock[]
}
