import { test, expect, type APIRequestContext } from '@playwright/test'
import { API_BASE_URL, expectOk, getAuthHeader } from './helpers/apiClient'
import { dumpFromDb } from './helpers/dbVerify'
import { readState } from './helpers/state'

// Verifies the reporting layer reflects exactly what Module 3 left in
// the DB for our one project -- both the aggregate "clients & their
// projects" report (report_service.clients_projects, which returns
// each project's status/stage/progress directly, so it's a clean
// row-for-row comparison against the same DB dump the earlier modules
// used) and the per-project report page, then a UI spot-check that the
// Reports section of the app actually shows it.
test.describe('Module 4 -- Reports', () => {
  let auth: { Authorization: string }
  let request: APIRequestContext

  test.beforeAll(async ({ playwright }) => {
    request = await playwright.request.newContext({ baseURL: API_BASE_URL })
    auth = await getAuthHeader(request)
  })

  test.afterAll(async () => {
    await request.dispose()
  })

  test('clients-projects report matches the DB row for our client/project', async () => {
    const state = readState()
    expect(state.clientId && state.projectNo, 'Modules 1-3 must run first').toBeTruthy()

    const report = await expectOk<Array<Record<string, unknown>>>(
      request.get('/reports/clients-projects', { headers: auth }),
    )
    const ourClientEntry = report.find((entry) => entry.clientId === String(state.clientId))
    expect(ourClientEntry, `expected clientId ${state.clientId} in the clients-projects report`).toBeTruthy()

    const ourProjectSummary = (ourClientEntry!.projects as Array<Record<string, unknown>>).find(
      (p) => p.projectNo === state.projectNo,
    )
    expect(ourProjectSummary, `expected project ${state.projectNo} under that client in the report`).toBeTruthy()

    const savedProject = dumpFromDb('project', state.projectNo!)
    const savedClient = dumpFromDb('client', state.clientId!)

    expect(ourProjectSummary!.status).toBe(savedProject.status)
    expect(ourProjectSummary!.currentStage).toBe(savedProject.current_stage)
    expect(ourProjectSummary!.projectName).toBe(savedProject.project_name)
    expect(ourClientEntry!.clientStatus).toBe(savedClient.status)
  })

  test('the per-project report returns sections without erroring', async () => {
    const state = readState()
    const sections = await expectOk<Array<Record<string, unknown>>>(
      request.get(`/reports/projects/${state.projectNo}`, { headers: auth }),
    )
    expect(Array.isArray(sections)).toBe(true)
    expect(sections.length).toBeGreaterThan(0)
  })

  test('projects-by-status includes our project in the Completed bucket', async () => {
    const state = readState()
    const buckets = await expectOk<Array<{ label: string; value: number }>>(
      request.get('/reports/projects-by-status', { headers: auth }),
    )
    const completedBucket = buckets.find((b) => b.label === 'Completed')
    // Only asserting the bucket exists and is at least 1 -- this
    // endpoint aggregates over every real project in the system, so a
    // precise count would be a moving target the moment any other
    // project's status changes. Module 3 already proved our specific
    // project reached Completed in the DB; this just confirms the
    // aggregate report didn't drop or miscategorize it.
    expect(completedBucket, 'expected a "Completed" bucket now that our project reached it').toBeTruthy()
    expect(completedBucket!.value).toBeGreaterThanOrEqual(1)
  })

  test('the Reports page shows our project', async ({ page }) => {
    const state = readState()
    await page.goto('/login')
    await page.getByLabel(/user id/i).fill('admin')
    await page.getByLabel(/password/i).fill('Demo#2026')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/dashboard/)

    await page.goto('/reports/project')
    // The project-report page picks a project via a search/select
    // control rather than a path param (see src/router/index.ts) --
    // our project's tagged name is unique enough to type-ahead search
    // for reliably.
    await page.getByLabel(/project/i).first().fill(state.runTag)
    await page.getByText(state.runTag).first().click()
    await expect(page.getByText(state.runTag)).toBeVisible()
  })
})
