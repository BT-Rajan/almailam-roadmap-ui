import { test, expect, type APIRequestContext } from '@playwright/test'
import { API_BASE_URL, expectOk, getAuthHeader } from './helpers/apiClient'
import { dumpFromDb } from './helpers/dbVerify'
import { readState, writeState } from './helpers/state'

// This module walks the ONE project from Module 2 through the real
// workflow state machine end to end: Requirement -> Quotation ->
// Payment Plan -> Contract -> Design -> Handover -> Completed (see
// backend/app/services/project_service.py's _assert_stage_exit_criteria
// and _auto_advance_target, and backend/app/core/status_transitions.py).
//
// This is deliberately API-driven (backend testing), not a UI click-
// through of the Quotation/Contract/Payment-Plan forms -- those are
// each their own substantial wizard and the thing actually under test
// here is the workflow engine's transition rules and exit criteria,
// which are enforced identically regardless of which caller triggers
// them. The UI is still checked at the end of the run (frontend
// testing) -- the Project Workspace page must show the stage/status
// the backend now has on file.
//
// A quotation/contract/agreement/payment sub-record is created here at
// the absolute functional minimum needed to satisfy each stage's exit
// criteria (one line item, one financial agreement, no milestones) --
// this stream verifies the workflow transitions themselves, not every
// field of those sub-modules (that belongs in their own dedicated
// tests, same reasoning as Module 1 not covering the Organisation
// client-type branch).
test.describe('Module 3 -- Project Workflow', () => {
  let auth: { Authorization: string }
  let request: APIRequestContext

  test.beforeAll(async ({ playwright }) => {
    request = await playwright.request.newContext({ baseURL: API_BASE_URL })
    auth = await getAuthHeader(request)
  })

  test.afterAll(async () => {
    await request.dispose()
  })

  test('drives the project from Requirement to Completed and the DB reflects every hop', async () => {
    const state = readState()
    expect(state.projectNo, 'Module 2 must run first and record a projectNo').toBeTruthy()
    const projectNo = state.projectNo!

    // --- Sanity: starts in Requirement/Active, as Module 2 asserted ---
    let project = await expectOk<Record<string, unknown>>(
      request.get(`/projects/${projectNo}`, { headers: auth }),
    )
    expect(project.currentStage).toBe('Requirement')

    // --- Requirement -> Quotation ---
    // Needs the client's identification on file (Module 1 deliberately
    // left this blank -- it's optional at client-creation time, real
    // and blocking here) and a non-empty scope, which project creation
    // already filled in via buildScopeText().
    await expectOk(
      request.post(`/clients/${state.clientId}/identifications`, {
        headers: auth,
        data: {
          documentType: 'Civil ID',
          documentNumber: `${state.runTag}-ID`,
          issueDate: '2020-01-01',
          expiryDate: '2030-01-01',
          issuingCountry: 'Kuwait',
        },
      }),
    )
    await expectOk(request.post(`/projects/${projectNo}/requirement/confirm-scope`, { headers: auth }))

    project = await expectOk(request.get(`/projects/${projectNo}`, { headers: auth }))
    expect(project.currentStage).toBe('Quotation')
    expect(dumpFromDb('project', projectNo).current_stage).toBe('Quotation')

    // --- Quotation -> (approve) -> auto-advances to Payment Plan ---
    const quotation = await expectOk<Record<string, unknown>>(
      request.post(`/quotations`, {
        headers: auth,
        data: {
          projectId: projectNo,
          validity: futureDate(30),
          lineItems: [{ description: `${state.runTag} verification line item`, quantity: 1, unitPrice: 500 }],
        },
      }),
    )
    const quotationNo = quotation.id as string
    writeState({ quotationNo })

    await expectOk(request.post(`/quotations/${quotationNo}/finalize`, { headers: auth }))
    await expectOk(
      request.patch(`/quotations/${quotationNo}/status`, { headers: auth, data: { status: 'Approved' } }),
    )

    project = await expectOk(request.get(`/projects/${projectNo}`, { headers: auth }))
    expect(project.currentStage).toBe('Payment Plan')
    const savedQuotation = dumpFromDb('quotation', quotationNo)
    expect(savedQuotation.status).toBe('Approved')

    // --- Payment Plan -> (approve the Design agreement) -> auto-advances to Contract ---
    const agreement = await expectOk<Record<string, unknown>>(
      request.post(`/financial-agreements`, {
        headers: auth,
        data: {
          projectId: projectNo,
          stream: 'Design',
          contractAmount: 500,
          contractStartDate: futureDate(1),
          agreementDate: futureDate(0),
          paymentMode: 'Bank Transfer',
          paymentFrequency: 'One-time',
        },
      }),
    )
    const agreementId = agreement.id as string
    writeState({ agreementId })
    await expectOk(request.post(`/financial-agreements/${agreementId}/approve`, { headers: auth }))

    project = await expectOk(request.get(`/projects/${projectNo}`, { headers: auth }))
    expect(project.currentStage).toBe('Contract')
    expect(dumpFromDb('agreement', agreementId).status).toBe('Approved')

    // --- Contract -> (sign) -> auto-advances to Design (the only track this project includes) ---
    const contract = await expectOk<Record<string, unknown>>(
      request.post(`/contracts`, {
        headers: auth,
        data: {
          projectId: projectNo,
          quotationId: quotationNo,
          contractValue: 500,
          expiryDate: futureDate(365),
          clientRepresentative: `${state.runTag} Signatory`,
          scopeSummary: `${state.runTag} verification scope`,
        },
      }),
    )
    const contractNo = contract.id as string
    writeState({ contractNo })
    await expectOk(request.post(`/contracts/${contractNo}/finalize`, { headers: auth }))
    await expectOk(
      request.post(`/contracts/${contractNo}/confirm-signing`, {
        headers: auth,
        multipart: { file: minimalPdf('signed-contract.pdf') },
      }),
    )

    project = await expectOk(request.get(`/projects/${projectNo}`, { headers: auth }))
    expect(project.currentStage).toBe('Design')
    expect(dumpFromDb('contract', contractNo).status).toMatch(/Signed|Active/)

    // --- Design -> (close the one selected activity) -> auto-advances to Handover ---
    // Closed as Cancelled rather than Complete: Complete would also
    // require every task linked to the activity to already be
    // Completed, which is a separate module's workflow (task
    // management) this stream doesn't drive. Cancelled satisfies the
    // same Handover exit criterion ("every Design activity closed --
    // Complete or Cancelled").
    const selectedActivities = dumpFromDb('project', projectNo).selectedActivities as Array<Record<string, unknown>>
    expect(selectedActivities.length).toBeGreaterThan(0)
    const activityId = selectedActivities[0].id
    await expectOk(
      request.post(`/projects/${projectNo}/design-activities/${activityId}/close`, {
        headers: auth,
        data: { status: 'Cancelled', overrideNoDocument: true },
      }),
    )

    project = await expectOk(request.get(`/projects/${projectNo}`, { headers: auth }))
    expect(project.currentStage).toBe('Handover')
    expect(dumpFromDb('project', projectNo).current_stage).toBe('Handover')

    // --- Handover: confirm payment, then the client's signed acknowledgment -> status: Completed ---
    await expectOk(request.post(`/projects/${projectNo}/handover/confirm-payment`, { headers: auth }))
    await expectOk(
      request.post(`/projects/${projectNo}/handover/confirm`, {
        headers: auth,
        multipart: { file: minimalPdf('handover-ack.pdf') },
      }),
    )

    project = await expectOk(request.get(`/projects/${projectNo}`, { headers: auth }))
    expect(project.status).toBe('Completed')
    const finalDbState = dumpFromDb('project', projectNo)
    expect(finalDbState.status).toBe('Completed')
    expect(finalDbState.current_stage).toBe('Handover')
  })

  test('the Project Workspace page reflects the completed workflow', async ({ page }) => {
    const state = readState()
    await page.goto('/login')
    await page.getByLabel(/user id/i).fill('admin')
    await page.getByLabel(/password/i).fill('Demo#2026')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/dashboard/)

    await page.goto(`/projects/${state.projectNo}`)
    await expect(page.getByText('Completed', { exact: false })).toBeVisible()
    await expect(page.getByText('Handover', { exact: false }).first()).toBeVisible()
  })
})

function futureDate(daysFromNow: number): string {
  const date = new Date()
  date.setDate(date.getDate() + daysFromNow)
  return date.toISOString().slice(0, 10)
}

/** The smallest byte sequence that still passes a real PDF magic-byte
 * check (see backend/app/core/file_storage.py's save_upload) -- the
 * confirm-signing / handover-confirm endpoints treat the upload as
 * evidence, not a document to render, so content beyond a valid header
 * and EOF marker doesn't matter here. */
function minimalPdf(name: string): { name: string; mimeType: string; buffer: Buffer } {
  const content = '%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF'
  return { name, mimeType: 'application/pdf', buffer: Buffer.from(content, 'utf-8') }
}
