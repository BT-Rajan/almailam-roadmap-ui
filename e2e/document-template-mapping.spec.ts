import { test, expect } from '@playwright/test'
import { execFileSync } from 'node:child_process'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

// Covers two bugs in the admin-uploaded Quotation/Contract .docx
// template pipeline (Administration > Documents > Templates ->
// "Map fields"), both in backend/app/services/document_template_service.py:
//
// 1. Saving a field mapping used to destroy any embedded picture in the
//    uploaded template (e.g. a letterhead logo) -- _set_paragraph_text
//    rewrote every paragraph down to one plain-text run, image runs
//    included, and the mapper's Save always sends back every paragraph
//    in the document, not just the ones the admin actually edited.
// 2. Entered/merged values (the real quotation data) rendered in
//    whatever plain formatting the placeholder happened to have, with
//    no way to make them visually stand out from the template's own
//    static wording.
//
// This test drives the real upload -> map fields -> save -> download
// flow through the actual UI, then inspects the downloaded .docx's own
// XML (via the `unzip` CLI -- a .docx is a zip archive, and this avoids
// pulling in a zip-parsing npm dependency for one test) to assert both
// fixes actually hold in a real generated file, not just in a unit
// test against the service function directly.
const FIXTURE = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixtures', 'quotation-template-with-logo.docx')

function readDocumentXml(docxPath: string): string {
  return execFileSync('unzip', ['-p', docxPath, 'word/document.xml'], { encoding: 'utf-8' })
}

test.describe('Document template mapping preserves logos and bolds merge tokens', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/user id/i).fill('admin')
    await page.getByLabel(/password/i).fill('Demo#2026')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('upload, map a field, save, and download a template with an embedded logo', async ({ page }) => {
    // Click through instead of page.goto('/admin/documents') -- a hard
    // navigation reloads the SPA and this app's auth session doesn't
    // survive that (see StaffLoginForm/authStore), so this must stay
    // client-side routing all the way from the dashboard. The sidebar
    // is icon-only (no visible/accessible text label) at this
    // viewport, so target by href rather than accessible name.
    await page.locator('a[href="/admin"]').click()
    await page.getByRole('link', { name: 'Documents' }).click()
    await page.getByRole('tab', { name: /templates/i }).click()

    // --- Upload the fixture template for Quotation / English ---
    // "Upload .docx" appears once per document-type card (Quotation,
    // Contract); Quotation's is first since it's listed first.
    await page.getByRole('button', { name: 'Upload .docx' }).first().click()
    await page.getByLabel(/language/i).selectOption('English')
    await page.locator('input[type="file"]').setInputFiles(FIXTURE)
    await page.getByRole('button', { name: /^upload$/i }).click()
    await expect(page.getByText('Template uploaded', { exact: true })).toBeVisible()

    const uploadedRow = page.locator('li', { hasText: 'quotation-template-with-logo.docx' }).first()
    await expect(uploadedRow).toBeVisible()

    // --- Open Map Fields and place one merge-field token ---
    await uploadedRow.getByLabel(/map fields/i).click()
    const mapperDialog = page.getByRole('dialog')
    await expect(mapperDialog).toBeVisible()
    await expect(mapperDialog).toContainText(/map fields/i)

    // The fixture's two blank paragraphs come after the letterhead
    // (image) paragraphs -- click into the first blank editor, then
    // insert the Client Name token from the palette.
    const editors = mapperDialog.getByRole('textbox')
    await editors.nth(2).click()
    await mapperDialog.getByRole('button', { name: /client name/i }).click()

    await mapperDialog.getByRole('button', { name: /save mapping/i }).click()
    await expect(page.getByText(/fields mapped/i)).toBeVisible()

    // --- Download the now-mapped template and inspect the real file ---
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      uploadedRow.getByLabel(/download template/i).click(),
    ])
    const outDir = mkdtempSync(path.join(tmpdir(), 'template-download-'))
    const savedPath = path.join(outDir, 'downloaded.docx')
    await download.saveAs(savedPath)

    const xml = readDocumentXml(savedPath)

    // Bug 1: both the image-only letterhead paragraph and the mixed
    // text+image paragraph must still have their picture after the
    // mapping was saved.
    const drawingCount = (xml.match(/<w:drawing/g) ?? []).length
    expect(drawingCount).toBe(2)

    // Bug 2: the merge-field token we just placed must live in a run
    // that carries bold (<w:b/>), separate from any static wording --
    // i.e. the *entered value* will render bold once a real quotation
    // is merged into this template, without the static label text
    // around it being forced bold too.
    const tokenRunMatch = xml.match(/<w:r>(?:(?!<w:r>).)*?\{\{\s*client_name\s*\}\}(?:(?!<\/w:r>).)*?<\/w:r>/s)
    expect(tokenRunMatch, 'expected a run containing the {{ client_name }} token').not.toBeNull()
    expect(tokenRunMatch![0]).toMatch(/<w:b\s*\/>/)
  })
})
