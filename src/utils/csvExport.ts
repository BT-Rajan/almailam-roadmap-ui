import { triggerBlobDownload } from '@/utils/fileDownload'

export type CsvCell = string | number | null | undefined

export interface CsvSection {
  /** Optional heading row written above this section's table. */
  title?: string
  headers: string[]
  rows: CsvCell[][]
}

function escapeCell(cell: CsvCell): string {
  if (cell === null || cell === undefined) return ''
  if (typeof cell === 'number') return Number.isFinite(cell) ? String(cell) : ''
  // Text starting with = + - @ (or a tab/CR) is run as a formula by
  // spreadsheet apps -- prefix it so a name like "=HYPERLINK(...)" stays text.
  const text = /^[=+\-@\t\r]/.test(cell) ? `'${cell}` : cell
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
}

/** Downloads one CSV file; several sections are separated by a blank line. */
export function downloadCsv(filename: string, sections: CsvSection[]): void {
  const lines: string[] = []
  sections.forEach((section, index) => {
    if (index > 0) lines.push('')
    if (section.title) lines.push(escapeCell(section.title))
    lines.push(section.headers.map(escapeCell).join(','))
    for (const row of section.rows) lines.push(row.map(escapeCell).join(','))
  })
  // BOM so Excel opens UTF-8 (Arabic names) correctly.
  const blob = new Blob(['﻿' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8;' })
  triggerBlobDownload(blob, filename)
}
