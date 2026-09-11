import { test, expect } from '@playwright/test'
import { dumpFromDb } from './helpers/dbVerify'
import { readState, writeState } from './helpers/state'

// Drives the real New Client wizard (Individual type, the simpler of
// the two branches -- Organisation is structurally the same "sent vs
// saved" check against different field names, and isn't duplicated
// here to keep this one module focused) end to end, capturing the
// exact POST body the wizard sends and then reading back the row this
// created straight from the DB via backend/scripts/e2e_verify.py.
//
// Only one contact, one address, no identification document upload --
// the goal is a deterministic, minimal, single record, not exercising
// every optional branch of the wizard (that's what src/utils/
// clientValidation.ts unit coverage is for, not this stream).
test.describe('Module 1 -- Client Creation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/user id/i).fill('admin')
    await page.getByLabel(/password/i).fill('Demo#2026')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('creates one Individual client and the DB row matches what was sent', async ({ page }) => {
    const state = readState()
    const tag = state.runTag
    const fullLegalName = `${tag} Verification Client`
    const mobile = '+965 5000 0001'
    const email = `${tag.toLowerCase()}@e2e-verify.invalid`
    const city = 'Kuwait City'

    // Capture the exact request the wizard sends -- this is the "data
    // sent" half of the comparison, taken from the real network call
    // rather than re-derived from what we typed into the form.
    // createClientFull (clientService.ts) posts multipart/form-data
    // with a single JSON-stringified `payload` field (not a JSON body),
    // since it also carries the optional identification file -- pull
    // that field back out of the raw multipart bytes.
    let sentPayload: { client: Record<string, unknown>; contacts: unknown[]; address?: Record<string, unknown> } | undefined
    await page.route('**/api/clients/full', async (route) => {
      const request = route.request()
      if (request.method() === 'POST') {
        const body = request.postData() ?? ''
        const match = body.match(/name="payload"\r?\n\r?\n([\s\S]*?)\r?\n--/)
        if (match) sentPayload = JSON.parse(match[1])
      }
      await route.continue()
    })

    await page.goto('/clients/new')

    // --- Step 1: Client Type ---
    await page.getByRole('radio', { name: 'Individual' }).check()
    await page.getByLabel(/full legal name/i).fill(fullLegalName)
    await page.getByLabel(/nationality/i).fill('Kuwaiti')
    await page.getByLabel(/date of birth/i).fill('1990-01-01')
    await page.getByLabel(/mobile number/i).fill(mobile)
    await page.getByLabel(/email address/i).fill(email)
    // First real option -- index 0 is the disabled placeholder.
    await page.getByLabel(/account manager/i).selectOption({ index: 1 })
    await page.getByRole('button', { name: /^next$/i }).click()

    // --- Step 2: Contacts & Address ---
    await page.getByLabel(/^name$/i).first().fill(fullLegalName)
    await page.getByLabel(/^mobile number$/i).first().fill(mobile)
    await page.getByLabel(/^email address$/i).first().fill(email)
    await page.getByLabel(/^country$/i).fill('Kuwait')
    await page.getByLabel(/^state$/i).fill('Al Asimah')
    await page.getByLabel(/^city$/i).fill(city)
    await page.getByRole('button', { name: /^next$/i }).click()

    // --- Step 3: Identification -- left blank, it's optional ---
    await page.getByRole('button', { name: /^next$/i }).click()

    // --- Step 4: Review & Confirm ---
    await expect(page.getByText(fullLegalName)).toBeVisible()
    await page.getByRole('button', { name: /add client/i }).click()

    await expect(page.getByText('Client Submitted', { exact: false })).toBeVisible({ timeout: 15_000 })
    const clientCodeMatch = await page.getByText(/^[A-Z]+-\d+$/).first().textContent()
    await page.getByRole('button', { name: /view client workspace/i }).click()
    await expect(page).toHaveURL(/\/clients\/\d+/)
    const clientId = page.url().match(/\/clients\/(\d+)/)?.[1]
    expect(clientId, 'expected a numeric client ID in the post-create redirect URL').toBeTruthy()

    writeState({ clientId, clientCode: clientCodeMatch ?? undefined })

    expect(sentPayload, 'expected to capture the POST /api/clients/full request body').toBeTruthy()
    const sentClient = sentPayload!.client

    // --- Compare sent vs saved ---
    const saved = dumpFromDb('client', clientId!)
    expect(saved.client_type).toBe('Individual')
    expect(saved.ind_full_legal_name).toBe(sentClient.companyName)
    expect(saved.mobile).toBe(sentClient.mobile)
    expect(saved.email).toBe(sentClient.email)
    expect(saved.city).toBe(sentClient.city)
    expect(saved.status).toBe('Active')

    const savedContacts = saved.contacts as Array<Record<string, unknown>>
    expect(savedContacts.length).toBeGreaterThanOrEqual(1)
    expect(savedContacts[0].mobile).toBe(mobile)
    expect(savedContacts[0].email).toBe(email)

    const savedAddresses = saved.addresses as Array<Record<string, unknown>>
    expect(savedAddresses.length).toBeGreaterThanOrEqual(1)
    expect(savedAddresses[0].city).toBe(city)
  })
})
