import { test, expect } from '@playwright/test'
import { dumpFromDb } from './helpers/dbVerify'
import { readState, writeState } from './helpers/state'

// Builds on the client from 01-client-creation.spec.ts -- one project,
// for that one client, with exactly one Design service selected (the
// first available service, selected as a "whole service" via its
// top-level checkbox so this doesn't depend on the real catalog's
// specific names/activities). Same "capture the real POST, compare to
// the real DB row" shape as Module 1.
test.describe('Module 2 -- Project Creation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/user id/i).fill('admin')
    await page.getByLabel(/password/i).fill('Demo#2026')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('creates one project for the Module 1 client and the DB row matches what was sent', async ({ page }) => {
    const state = readState()
    expect(state.clientId, 'Module 1 must run first and record a clientId').toBeTruthy()
    const tag = state.runTag
    const projectName = `${tag} Verification Project`
    const siteAddress = 'Plot 1, E2E Verification Zone'

    let sentPayload: Record<string, unknown> | undefined
    await page.route('**/api/projects', async (route) => {
      const request = route.request()
      if (request.method() === 'POST') {
        sentPayload = request.postDataJSON()
      }
      await route.continue()
    })

    await page.goto('/projects/new')

    // --- Step 1: Client & Service ---
    // Our test client's name is unique (tagged) -- select it by
    // matching the option text rather than by position, so this can't
    // accidentally pick a real client if one happens to sort first.
    const clientSelect = page.getByLabel(/^client$/i)
    const clientOptionValue = await clientSelect
      .locator('option')
      .filter({ hasText: state.clientCode ?? tag })
      .first()
      .getAttribute('value')
    expect(clientOptionValue, `expected an option for our tagged client (${state.clientCode ?? tag})`).toBeTruthy()
    await clientSelect.selectOption(clientOptionValue!)

    await page.locator('#service-picker-button').click()
    const dialog = page.getByRole('dialog')
    await expect(dialog).toBeVisible()
    // First Design service's own top-level checkbox selects it as a
    // whole ("all activities"), regardless of what it's actually
    // called in this environment's catalog.
    await dialog.getByRole('checkbox').first().check()
    await dialog.getByRole('button', { name: /save selections/i }).click()

    await page.getByLabel(/field engineer/i).selectOption({ index: 1 })
    await page.getByRole('button', { name: /^next$/i }).click()

    // --- Step 2: Project Details ---
    await page.getByLabel(/project name/i).fill(projectName)
    await page.getByLabel(/site address/i).fill(siteAddress)
    const startDate = new Date()
    startDate.setDate(startDate.getDate() + 7)
    const targetDate = new Date()
    targetDate.setDate(targetDate.getDate() + 60)
    await page.getByLabel(/start date/i).fill(startDate.toISOString().slice(0, 10))
    await page.getByLabel(/target date/i).fill(targetDate.toISOString().slice(0, 10))
    await page.getByRole('button', { name: /^next$/i }).click()

    // --- Step 3: Review & Confirm ---
    await expect(page.getByText(projectName)).toBeVisible()
    await page.getByRole('button', { name: /create project/i }).click()

    await expect(page.getByText('Project Created', { exact: false })).toBeVisible({ timeout: 15_000 })
    await page.getByRole('button', { name: /view project workspace/i }).click()
    await expect(page).toHaveURL(/\/projects\/.+/)
    const projectNo = decodeURIComponent(page.url().split('/projects/')[1] ?? '')
    expect(projectNo, 'expected a project number in the post-create redirect URL').toBeTruthy()

    writeState({ projectNo })

    expect(sentPayload, 'expected to capture the POST /api/projects request body').toBeTruthy()

    // --- Compare sent vs saved ---
    const saved = dumpFromDb('project', projectNo)
    expect(saved.project_name).toBe(sentPayload!.projectName)
    expect(saved.site_address).toBe(siteAddress)
    expect(String(saved.client_id)).toBe(String(state.clientId))
    expect(saved.service).toBe(sentPayload!.service)
    expect(saved.current_stage).toBe('Requirement')
    expect(saved.status).toBe('Active')

    const savedActivities = saved.selectedActivities as Array<Record<string, unknown>>
    const sentActivities = sentPayload!.selectedActivities as Array<Record<string, unknown>>
    expect(savedActivities.length).toBe(sentActivities.length)
  })
})
