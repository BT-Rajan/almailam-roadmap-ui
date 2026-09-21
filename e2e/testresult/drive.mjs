import { chromium } from 'playwright'
import fs from 'node:fs'

const SHOTS = '/tmp/claude-0/-home-user-almailam-roadmap-ui/7ae90411-96de-5e05-9517-ceecfe86c2c1/scratchpad/shots'
const DUMMY_DOC = '/tmp/claude-0/-home-user-almailam-roadmap-ui/7ae90411-96de-5e05-9517-ceecfe86c2c1/scratchpad/dummy-doc.png'
const DUMMY_PDF = '/tmp/claude-0/-home-user-almailam-roadmap-ui/7ae90411-96de-5e05-9517-ceecfe86c2c1/scratchpad/dummy-signed.pdf'
const STATE_FILE = '/tmp/claude-0/-home-user-almailam-roadmap-ui/7ae90411-96de-5e05-9517-ceecfe86c2c1/scratchpad/state.json'
const BASE = 'http://localhost:5173'

// Which step to stop after -- lets me extend the script and only re-run
// what's new, without recreating already-created records.
const STOP_AFTER = process.env.STOP_AFTER || 'all'

const state = fs.existsSync(STATE_FILE) ? JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8')) : {}
function saveState() {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2))
}

const browser = await chromium.launch({
  args: ['--no-sandbox'],
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
})
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
const page = await context.newPage()

const errors = []
page.on('console', (msg) => {
  if (msg.type() === 'error') errors.push(msg.text())
})
page.on('pageerror', (err) => errors.push(String(err)))

let shotIndex = state.shotIndex || 1
async function shot(name) {
  const filename = `${String(shotIndex).padStart(2, '0')}-${name}.png`
  await page.screenshot({ path: `${SHOTS}/${filename}`, fullPage: true })
  console.log('screenshot:', filename)
  shotIndex++
  state.shotIndex = shotIndex
}

function stopIfDone(stepName) {
  if (STOP_AFTER === stepName) {
    console.log(`--- stopping after step '${stepName}' as requested ---`)
    return true
  }
  return false
}

try {
  // ---- Login (always) ----
  await page.goto(`${BASE}/login`)
  await page.getByLabel(/user id/i).fill('admin')
  await page.getByLabel(/password/i).fill('Admin#99')
  await page.getByRole('button', { name: /sign in/i }).click()
  await page.waitForURL(/\/dashboard/)
  await page.waitForTimeout(800)
  if (!state.loggedInShot) {
    await shot('login-dashboard')
    state.loggedInShot = true
    saveState()
  }

  // ---- Create user (once) ----
  if (!state.userCreated) {
    await page.locator('a[href="/admin"]').click()
    await page.waitForTimeout(400)
    await page.getByText('User Management').click()
    await page.waitForURL(/\/admin\/users$/)
    await page.waitForTimeout(400)
    await shot('user-management')

    await page.getByRole('button', { name: /add user/i }).click()
    await page.waitForTimeout(400)
    await page.getByLabel(/full name/i).fill('Fatima Al-Sabah')
    await page.getByLabel(/^email/i).fill('fatima.alsabah@almailam.ae')
    await page.getByLabel(/^mobile/i).fill('+965 5123 4567')
    await page.getByLabel(/^designation/i).fill('Project Manager')
    await page.getByLabel(/^role/i).selectOption({ label: 'Project Manager' })
    await shot('add-user-form-filled')
    await page.getByRole('button', { name: /^add user$/i }).click()
    await page.waitForTimeout(1000)
    await shot('user-created')
    await page.getByRole('button', { name: /^done$/i }).click()
    await page.waitForTimeout(400)

    state.userCreated = true
    saveState()
  }
  if (stopIfDone('user')) throw { __stop: true }

  // ---- Create a second user with the Engineer role (once) ----
  if (!state.engineerCreated) {
    await page.goto(`${BASE}/admin/users`)
    await page.waitForTimeout(400)
    await page.getByRole('button', { name: /add user/i }).click()
    await page.waitForTimeout(400)
    await page.getByLabel(/full name/i).fill('Omar Al-Rashid')
    await page.getByLabel(/^email/i).fill('omar.alrashid@almailam.ae')
    await page.getByLabel(/^mobile/i).fill('+965 5987 6543')
    await page.getByLabel(/^designation/i).fill('Site Engineer')
    await page.getByLabel(/^role/i).selectOption({ label: 'Engineer' })
    await page.getByRole('button', { name: /^add user$/i }).click()
    await page.waitForTimeout(1000)
    await shot('engineer-user-created')
    await page.getByRole('button', { name: /^done$/i }).click()
    await page.waitForTimeout(400)

    state.engineerCreated = true
    saveState()
  }
  if (stopIfDone('engineer')) throw { __stop: true }

  // ---- Explore: New Client wizard ----
  if (!state.clientWizardExplored) {
    await page.locator('a[href="/clients"]').click()
    await page.waitForURL(/\/clients$/)
    await page.waitForTimeout(400)
    await shot('clients-list')

    await page.getByRole('button', { name: /^\+?\s*new client$/i }).first().click()
    await page.waitForURL(/\/clients\/new$/)
    await page.waitForTimeout(400)
    await shot('new-client-wizard-step1')

    state.clientWizardExplored = true
    saveState()
  }
  if (stopIfDone('client-explore')) throw { __stop: true }

  // ---- Create client (Company type, once) ----
  if (!state.clientCreated) {
    await page.locator('a[href="/clients"]').click()
    await page.waitForURL(/\/clients$/)
    await page.waitForTimeout(300)
    await page.getByRole('button', { name: /^\+?\s*new client$/i }).first().click()
    await page.waitForURL(/\/clients\/new$/)
    await page.waitForTimeout(300)

    await page.getByText('Company', { exact: true }).click()
    await page.waitForTimeout(300)
    await shot('new-client-company-type')

    await page.getByLabel(/legal name/i).fill('ABC Trading Company')
    await page.getByLabel(/trade name/i).fill('ABC Trading')
    await page.getByLabel(/organisation type/i).fill('Trading Company')
    await page.getByLabel(/registration number/i).fill('CR-2026-00123')
    await page.getByLabel(/date of incorporation/i).fill('2010-01-01')
    await page.getByLabel(/mobile number/i).fill('+965 5222 3333')
    await page.getByLabel(/email address/i).fill('contact@abctrading.example')
    const accountManager = page.getByLabel(/account manager/i)
    const amOptions = await accountManager.locator('option').allTextContents()
    await accountManager.selectOption({ label: amOptions[1] ?? amOptions[0] })
    await shot('new-client-company-filled')

    await page.getByRole('button', { name: /^next$/i }).click()
    await page.waitForTimeout(500)
    await shot('new-client-step2-contacts-address')

    // Step 2: Contacts & Address
    await page.getByRole('button', { name: /add contact/i }).click()
    await page.waitForTimeout(300)

    await page.getByLabel(/^name/i).fill('Yousef Al-Ansari')
    await page.getByLabel(/mobile number/i).fill('+965 5333 4444')
    await page.getByLabel(/email address/i).fill('yousef@abctrading.example')

    await page.getByLabel(/governorate/i).fill('Al Asimah')
    await page.getByLabel(/^city/i).fill('Kuwait City')
    await page.getByLabel(/^area/i).fill('Sharq')
    await page.getByLabel(/^street/i).fill('Fahad Al-Salem Street')
    await page.getByLabel(/^building/i).fill('Tower 1')
    await shot('new-client-step2-filled')

    await page.getByRole('button', { name: /^next$/i }).click()
    await page.waitForTimeout(500)
    await shot('new-client-step3-identification')

    // Step 3: Identification
    await page.getByLabel(/registration number/i).fill('TL-2026-7788')
    await page.getByLabel(/issue date/i).fill('2020-01-01')
    await page.getByLabel(/expiry date/i).fill('2030-01-01')
    await page.locator('input[type="file"]').setInputFiles(DUMMY_DOC)
    await page.waitForTimeout(300)
    await shot('new-client-step3-filled')

    await page.getByRole('button', { name: /^next$/i }).click()
    await page.waitForTimeout(500)
    await shot('new-client-step4-review')

    await page.getByRole('button', { name: /^add client$/i }).click()
    await page.waitForTimeout(1200)
    await shot('client-created')

    await page.getByRole('button', { name: /view client workspace/i }).click()
    await page.waitForURL(/\/clients\/CLT-/)
    await page.waitForTimeout(600)
    await shot('client-workspace')
    state.clientId = page.url().split('/clients/')[1]
    console.log('Client created, id:', state.clientId)

    state.clientCreated = true
    saveState()
  }
  if (stopIfDone('client-created')) throw { __stop: true }

  // ---- Ensure we're on the client workspace (in case creation was
  // already done in a prior run and this run resumed past it) ----
  if (!page.url().includes(`/clients/${state.clientId}`)) {
    await page.goto(`${BASE}/clients/${state.clientId}`)
    await page.waitForTimeout(600)
    await shot('client-workspace-revisit')
  }

  // ---- New Project wizard: client-only state, so this must run start
  // to finish in one go -- nothing here persists server-side until the
  // final "Create Project" click, so a script re-run can't resume
  // mid-wizard the way the earlier server-backed steps can. ----
  if (!state.projectCreated) {
    await page.locator('a[href="/projects"]').click()
    await page.waitForURL(/\/projects$/)
    await page.waitForTimeout(400)
    await shot('projects-list')

    await page.getByRole('button', { name: /^\+?\s*new project$/i }).first().click()
    await page.waitForURL(/\/projects\/new$/)
    await page.waitForTimeout(400)
    await shot('new-project-wizard-step1')

    const clientSelect = page.getByLabel(/^client/i)
    await clientSelect.selectOption({ label: 'ABC Trading Company' })

    const engineerSelect = page.getByLabel(/field engineer/i)

    await page.getByRole('button', { name: /choose/i }).click()
    await page.waitForTimeout(400)
    await shot('project-service-picker')

    // NOTE: deliberately not selecting a Supervision item here (e.g.
    // "Weekly Site Visits") -- confirmed bug: the wizard never collects
    // selectedSupervisionActivities[].startDate/endDate anywhere in its
    // UI, but sends them to POST /api/projects regardless, which the
    // backend correctly rejects with a raw 422 ("Input should be a valid
    // date or datetime, input is too short") right at the final "Create
    // Project" click -- after all four wizard steps are already filled
    // in. Reproduced directly: request payload has
    // selectedSupervisionActivities: [{ ..., startDate: "", endDate: "" }].
    await page.getByText('Architectural Design', { exact: true }).click()
    await page.getByText('Permit', { exact: true }).click()
    await shot('project-service-selected')
    await page.getByRole('button', { name: /save selections/i }).click()
    await page.waitForTimeout(400)

    await engineerSelect.selectOption({ label: 'Omar Al-Rashid' })
    await shot('project-wizard-step1-filled')

    await page.getByRole('button', { name: /^next$/i }).click()
    await page.waitForTimeout(500)
    await shot('project-wizard-step2')

    await page.getByLabel(/project name/i).fill('Industrial Building Approval')
    await page.getByLabel(/project\/site address/i).fill('Plot 12, Shuwaikh Industrial Area, Kuwait')
    await page.getByLabel(/start date/i).fill('2026-09-25')
    await page.getByLabel(/target completion date/i).fill('2027-03-25')
    await shot('project-details-filled')

    await page.getByRole('button', { name: /^next$/i }).click()
    await page.waitForTimeout(500)
    await shot('project-review')

    await page.getByRole('button', { name: /create project/i }).click()
    await page.waitForTimeout(1200)
    await shot('project-created')

    await page.getByRole('button', { name: /view project workspace/i }).click()
    await page.waitForURL(/\/projects\/\d+/)
    await page.waitForTimeout(600)
    await shot('project-workspace')
    state.projectId = page.url().split('/projects/')[1]
    console.log('Project created, id:', state.projectId)

    state.projectCreated = true
    saveState()
  }
  if (stopIfDone('project-created')) throw { __stop: true }

  async function gotoWorkspace(projectId = state.projectId) {
    if (!page.url().includes(`/projects/${projectId}`) || page.url().includes('#')) {
      await page.goto(`${BASE}/projects/${projectId}`)
    } else {
      await page.reload()
    }
    await page.getByText(/Stage \d of 6/).waitFor({ timeout: 15000 }).catch(() => {})
    await page.waitForTimeout(800)
    // WORKAROUND for confirmed bug: on a fresh load of a project already
    // past the Scope stage, the Overview tab renders the stale Scope-of-
    // Work panel (with a disabled Save & Proceed) instead of the actual
    // current stage's panel, even though the stage banner above it
    // already reads the correct stage. Clicking the current stage's own
    // label in the stepper forces it to render the right panel.
    const stageLabel = await page.getByText(/Stage \d of 6 · /).textContent().catch(() => null)
    const stageName = stageLabel?.split('·')[1]?.trim()
    if (stageName && stageName !== 'Scope') {
      await page.getByText(stageName, { exact: true }).click().catch(() => {})
      await page.waitForTimeout(500)
    }
  }
  await gotoWorkspace()
  await shot('project-workspace-scope')

  // ---- Stage 1: Scope -- Save & Proceed ----
  if (!state.scopeConfirmed) {
    await page.getByRole('button', { name: /save\s*&\s*proceed/i }).click()
    await page.waitForTimeout(1000)
    await shot('after-scope-confirm')
    state.scopeConfirmed = true
    saveState()
  }
  if (stopIfDone('scope')) throw { __stop: true }

  // ---- Stage 2: Quotation (client-only wizard state -- one continuous
  // block, same reasoning as the New Project Wizard above) ----
  if (!state.quotationCreated) {
    await gotoWorkspace()
    await page.getByRole('button', { name: /new quotation/i }).first().click()
    await page.waitForTimeout(1000)
    await shot('new-quotation-form')

    await page.getByLabel(/valid until/i).fill('2026-10-25')
    // Unit Rate is read-only here (derived from the Service Catalog's own
    // configured price for each service, which is KWD 0.00 for the demo
    // catalog items used in this walkthrough) -- only Units is editable.
    await shot('quotation-services-priced')

    const submitBtn = page.getByRole('button', { name: /save|create quotation|submit/i }).first()
    await submitBtn.scrollIntoViewIfNeeded()
    await shot('quotation-full-form')
    await submitBtn.click()
    await page.waitForTimeout(1200)
    await shot('quotation-created')

    state.quotationCreated = true
    saveState()
  }
  if (stopIfDone('quotation-created')) throw { __stop: true }

  if (!state.quotationTabExplored) {
    await gotoWorkspace()
    await shot('quotation-tab-state')
    const buttons = await page.getByRole('button').allTextContents()
    console.log('QUOTATION TAB BUTTONS:', JSON.stringify(buttons))
    state.quotationTabExplored = true
    saveState()
  }
  if (stopIfDone('quotation-tab-explore')) throw { __stop: true }

  if (!state.quotationApproved) {
    await gotoWorkspace()
    await page.getByRole('button', { name: /^decision/i }).click()
    await page.waitForTimeout(400)
    await shot('quotation-decision-menu')
    await page.getByRole('menuitem', { name: 'Approve' }).click()
    await page.waitForTimeout(500)
    await shot('quotation-approve-dialog')
    await page.locator('input[type="file"]').setInputFiles(DUMMY_PDF)
    await page.waitForTimeout(400)
    await shot('quotation-approve-dialog-file-selected')
    await page.getByRole('button', { name: /^confirm$/i }).click()
    await page.waitForTimeout(1000)
    await shot('quotation-approved')

    state.quotationApproved = true
    saveState()
  }
  if (stopIfDone('quotation-approved')) throw { __stop: true }

  // ---- Stage 3: Payment Plan ----
  if (!state.paymentPlanCreated) {
    await page.getByRole('button', { name: /^ok$/i }).click().catch(() => {})
    await gotoWorkspace()
    await page.getByRole('button', { name: /create payment plan/i }).first().click()
    await page.waitForTimeout(1000)
    await shot('payment-plan-form')

    await page.getByLabel(/total amount/i).fill('10000')
    const dueDates = ['2026-10-01', '2026-11-15', '2027-01-15', '2027-03-25']
    const dueDateInputs = page.locator('tbody input[type="date"]')
    const count = await dueDateInputs.count()
    for (let i = 0; i < count; i++) {
      await dueDateInputs.nth(i).fill(dueDates[i] ?? dueDates[dueDates.length - 1])
    }
    await shot('payment-plan-filled')

    const createBtn = page.getByRole('button', { name: /^create payment plan$/i })
    await createBtn.scrollIntoViewIfNeeded()
    await createBtn.click()
    await page.waitForTimeout(1200)
    await shot('payment-plan-created')

    state.paymentPlanCreated = true
    saveState()
  }
  if (stopIfDone('payment-plan-created')) throw { __stop: true }

  // ===================================================================
  // PROJECT 2 -- project 2600002 got stuck at Payment Plan because the
  // catalog services selected during its creation (Architectural
  // Design, Permit) had no fixed cost configured (KWD 0), and the
  // approved quotation's total (also 0) can't be overridden in the
  // Payment Plan form (its Total Amount field is read-only, derived
  // from the quotation). Catalog prices are now set (Architectural
  // Design > Design Development = KWD 8,000; Permit > Approval Service
  // = KWD 1,500), so this second project exercises the full lifecycle
  // through to Handover + Report with a real, non-zero contract value.
  // ===================================================================
  if (!state.project2Created) {
    await page.locator('a[href="/projects"]').first().click()
    await page.waitForURL(/\/projects$/)
    await page.waitForTimeout(400)

    await page.getByRole('button', { name: /^\+?\s*new project$/i }).first().click()
    await page.waitForURL(/\/projects\/new$/)
    await page.waitForTimeout(400)

    await page.getByLabel(/^client/i).selectOption({ label: 'ABC Trading Company' })
    await page.getByRole('button', { name: /choose/i }).click()
    await page.waitForTimeout(400)
    await page.getByText('Architectural Design', { exact: true }).click()
    await page.getByText('Permit', { exact: true }).click()
    await page.getByRole('button', { name: /save selections/i }).click()
    await page.waitForTimeout(400)
    await page.getByLabel(/field engineer/i).selectOption({ label: 'Omar Al-Rashid' })
    await shot('p2-wizard-step1')

    await page.getByRole('button', { name: /^next$/i }).click()
    await page.waitForTimeout(500)
    await page.getByLabel(/project name/i).fill('Industrial Building Approval II')
    await page.getByLabel(/project\/site address/i).fill('Plot 12, Shuwaikh Industrial Area, Kuwait')
    await page.getByLabel(/start date/i).fill('2026-09-25')
    await page.getByLabel(/target completion date/i).fill('2027-03-25')
    await shot('p2-wizard-step2')

    await page.getByRole('button', { name: /^next$/i }).click()
    await page.waitForTimeout(500)
    await shot('p2-wizard-review')

    await page.getByRole('button', { name: /create project/i }).click()
    await page.waitForTimeout(1200)
    await page.getByRole('button', { name: /view project workspace/i }).click()
    await page.waitForURL(/\/projects\/\d+/)
    await page.waitForTimeout(800)
    state.project2Id = page.url().split('/projects/')[1]
    console.log('Project 2 created, id:', state.project2Id)
    await shot('p2-workspace')

    state.project2Created = true
    saveState()
  }
  if (stopIfDone('p2-created')) throw { __stop: true }

  // ---- P2 Stage 1: Scope ----
  if (!state.p2ScopeConfirmed) {
    await gotoWorkspace(state.project2Id)
    await page.getByRole('button', { name: /save\s*&\s*proceed/i }).click()
    await page.waitForTimeout(1000)
    await shot('p2-scope-confirmed')
    state.p2ScopeConfirmed = true
    saveState()
  }
  if (stopIfDone('p2-scope')) throw { __stop: true }

  // ---- P2 Stage 2: Quotation (create, price should now be non-zero) ----
  if (!state.p2QuotationCreated) {
    await gotoWorkspace(state.project2Id)
    await page.getByRole('button', { name: /new quotation/i }).first().click()
    await page.waitForTimeout(1000)
    await shot('p2-new-quotation-form')

    await page.getByLabel(/valid until/i).fill('2026-10-25')
    await shot('p2-quotation-priced')

    const submitBtn = page.getByRole('button', { name: /save|create quotation|submit/i }).first()
    await submitBtn.scrollIntoViewIfNeeded()
    await submitBtn.click()
    await page.waitForTimeout(1200)
    await shot('p2-quotation-created')

    state.p2QuotationCreated = true
    saveState()
  }
  if (stopIfDone('p2-quotation-created')) throw { __stop: true }

  // ---- P2 Stage 2: Approve quotation ----
  if (!state.p2QuotationApproved) {
    await page.getByRole('button', { name: /^ok$/i }).click().catch(() => {})
    await gotoWorkspace(state.project2Id)
    await page.getByRole('button', { name: /^decision/i }).click()
    await page.waitForTimeout(400)
    await page.getByRole('menuitem', { name: 'Approve' }).click()
    await page.waitForTimeout(500)
    await page.locator('input[type="file"]').setInputFiles(DUMMY_PDF)
    await page.waitForTimeout(400)
    await page.getByRole('button', { name: /^confirm$/i }).click()
    await page.waitForTimeout(1200)
    await shot('p2-quotation-approved')

    state.p2QuotationApproved = true
    saveState()
  }
  if (stopIfDone('p2-quotation-approved')) throw { __stop: true }

  // ---- P2 Stage 3: Payment Plan ----
  if (!state.p2PaymentPlanCreated) {
    await page.getByRole('button', { name: /^ok$/i }).click().catch(() => {})
    await gotoWorkspace(state.project2Id)
    await page.getByRole('button', { name: /create payment plan/i }).first().click()
    await page.waitForTimeout(1000)
    await shot('p2-payment-plan-form')

    const dueDates = ['2026-10-01', '2026-11-15', '2027-01-15', '2027-03-25']
    const dueDateInputs = page.locator('tbody input[type="date"]')
    const count = await dueDateInputs.count()
    for (let i = 0; i < count; i++) {
      await dueDateInputs.nth(i).fill(dueDates[i] ?? dueDates[dueDates.length - 1])
    }
    await shot('p2-payment-plan-filled')

    const createBtn = page.getByRole('button', { name: /^create payment plan$/i })
    await createBtn.scrollIntoViewIfNeeded()
    await createBtn.click()
    await page.waitForTimeout(1200)
    await shot('p2-payment-plan-created')

    state.p2PaymentPlanCreated = true
    saveState()
  }
  if (stopIfDone('p2-payment-plan-created')) throw { __stop: true }

  // ---- P2 Stage 3: Approve Payment Plan ----
  if (!state.p2PaymentPlanApproved) {
    await page.getByRole('button', { name: /^ok$/i }).click().catch(() => {})
    await gotoWorkspace(state.project2Id)
    await shot('p2-payment-plan-review')
    await page.getByRole('button', { name: /^decision/i }).click()
    await page.waitForTimeout(400)
    await shot('p2-payment-plan-decision-menu')
    const decisionOptions = await page.getByRole('menuitem').allTextContents()
    console.log('P2 PAYMENT PLAN DECISION OPTIONS:', JSON.stringify(decisionOptions))
    await page.getByRole('menuitem', { name: 'Approve' }).click()
    await page.waitForTimeout(500)
    await shot('p2-payment-plan-approve-dialog')
    const fileInput = page.locator('input[type="file"]')
    if (await fileInput.count()) {
      await fileInput.setInputFiles(DUMMY_PDF)
      await page.waitForTimeout(300)
    }
    await page.getByRole('button', { name: /^confirm$/i }).click()
    await page.waitForTimeout(1200)
    await shot('p2-payment-plan-approved')

    state.p2PaymentPlanApproved = true
    saveState()
  }
  if (stopIfDone('p2-payment-plan-approved')) throw { __stop: true }

  // ---- P2 Stage 4: Contract ----
  if (!state.p2ContractExplored) {
    await page.getByRole('button', { name: /^ok$/i }).click().catch(() => {})
    await gotoWorkspace(state.project2Id)
    await shot('p2-contract-tab')
    const buttons = await page.getByRole('button').allTextContents()
    console.log('P2 CONTRACT BUTTONS:', JSON.stringify(buttons))
    state.p2ContractExplored = true
    saveState()
  }
  if (stopIfDone('p2-contract-explore')) throw { __stop: true }

  if (!state.p2ContractCreated) {
    await gotoWorkspace(state.project2Id)
    await page.getByRole('button', { name: /new contract/i }).first().click()
    await page.waitForTimeout(1000)
    await shot('p2-new-contract-form')
    const createBtn = page.getByRole('button', { name: /^create contract$/i })
    await createBtn.scrollIntoViewIfNeeded()
    await createBtn.click()
    await page.waitForTimeout(1200)
    await shot('p2-contract-created')

    state.p2ContractCreated = true
    saveState()
  }
  if (stopIfDone('p2-contract-created')) throw { __stop: true }

  if (!state.p2ContractApproved) {
    await page.getByRole('button', { name: /^ok$/i }).click().catch(() => {})
    await gotoWorkspace(state.project2Id)
    await page.getByRole('button', { name: /^decision/i }).click()
    await page.waitForTimeout(400)
    await shot('p2-contract-decision-menu')
    await page.getByRole('menuitem', { name: /sign contract/i }).click()
    await page.waitForTimeout(500)
    await shot('p2-contract-sign-dialog')
    const fileInput = page.locator('input[type="file"]')
    if (await fileInput.count()) {
      await fileInput.setInputFiles(DUMMY_PDF)
      await page.waitForTimeout(300)
    }
    await page.getByRole('button', { name: /^confirm$/i }).click()
    await page.waitForTimeout(1200)
    await shot('p2-contract-signed')

    state.p2ContractApproved = true
    saveState()
  }
  if (stopIfDone('p2-contract-signed')) throw { __stop: true }

  if (!state.p2DesignExplored) {
    await page.getByRole('button', { name: /^ok$/i }).click().catch(() => {})
    await gotoWorkspace(state.project2Id)
    await shot('p2-design-tab')
    const buttons = await page.getByRole('button').allTextContents()
    console.log('P2 DESIGN BUTTONS:', JSON.stringify(buttons))
    state.p2DesignExplored = true
    saveState()
  }
  if (stopIfDone('p2-design-explore')) throw { __stop: true }

  // Each design activity has a linked task that must reach Completed
  // before the activity's own "Mark Complete" unlocks. Complete both
  // tasks first via the Design stage's Tasks tab.
  if (!state.p2TasksCompleted) {
    await gotoWorkspace(state.project2Id)
    await page.getByText('Tasks', { exact: true }).click()
    await page.waitForTimeout(600)
    await shot('p2-tasks-list')

    const taskTitles = ['Approval Service', 'Design Development']
    for (const title of taskTitles) {
      await page.getByText(title, { exact: true }).click()
      await page.waitForTimeout(600)
      const statusSelect = page.getByLabel('Status')
      const currentStatus = await statusSelect.locator('option:checked').textContent().catch(() => '')
      if (currentStatus?.trim() !== 'Completed') {
        await statusSelect.selectOption({ label: 'Completed' })
        await page.waitForTimeout(400)
        await page.getByRole('button', { name: /^confirm$/i }).click()
        await page.waitForTimeout(800)
      }
      await shot(`p2-task-${title.replace(/\s+/g, '-').toLowerCase()}-completed`)
      await gotoWorkspace(state.project2Id)
      await page.getByText('Tasks', { exact: true }).click()
      await page.waitForTimeout(600)
    }

    state.p2TasksCompleted = true
    saveState()
  }
  if (stopIfDone('p2-tasks-completed')) throw { __stop: true }

  if (!state.p2DesignCompleted) {
    await gotoWorkspace(state.project2Id)
    let guard = 0
    while (guard < 5) {
      const completeButtons = page.getByRole('button', { name: /mark complete/i })
      const remaining = await completeButtons.count()
      if (remaining === 0) break
      await completeButtons.first().click()
      await page.waitForTimeout(500)
      const confirmBtn = page.getByRole('button', { name: /^confirm$/i })
      if (await confirmBtn.count()) {
        await confirmBtn.click()
      }
      await page.waitForTimeout(1000)
      guard++
    }
    await shot('p2-design-activities-completed')

    state.p2DesignCompleted = true
    saveState()
  }
  if (stopIfDone('p2-design-completed')) throw { __stop: true }

  if (!state.p2HandoverExplored) {
    await gotoWorkspace(state.project2Id)
    await shot('p2-handover-tab')
    const buttons = await page.getByRole('button').allTextContents()
    console.log('P2 HANDOVER BUTTONS:', JSON.stringify(buttons))
    state.p2HandoverExplored = true
    saveState()
  }
  if (stopIfDone('p2-handover-explore')) throw { __stop: true }

  if (!state.p2PaymentConfirmed) {
    await gotoWorkspace(state.project2Id)
    await page.getByText('Payment Confirmation', { exact: true }).click()
    await page.waitForTimeout(700)
    await shot('p2-payment-confirmation-tab')
    await page.getByRole('button', { name: /confirm payment received/i }).click()
    await page.waitForTimeout(500)
    await shot('p2-payment-confirm-dialog')
    const confirmBtn = page.getByRole('button', { name: /^confirm$/i })
    if (await confirmBtn.count()) await confirmBtn.click()
    await page.waitForTimeout(1000)
    await shot('p2-payment-confirmed')

    state.p2PaymentConfirmed = true
    saveState()
  }
  if (stopIfDone('p2-payment-confirmed')) throw { __stop: true }

  if (!state.p2HandedOver) {
    await gotoWorkspace(state.project2Id)
    await shot('p2-handover-ready')
    await page.getByRole('button', { name: /confirm hand-over/i }).click()
    await page.waitForTimeout(500)
    await shot('p2-handover-confirm-dialog')
    await page.locator('input[type="file"]').setInputFiles(DUMMY_PDF)
    await page.waitForTimeout(400)
    await page.getByRole('button', { name: /^confirm$/i }).click()
    await page.waitForTimeout(1200)
    await shot('p2-handed-over')

    state.p2HandedOver = true
    saveState()
  }
  if (stopIfDone('p2-handed-over')) throw { __stop: true }

  if (!state.p2ArchiveDismissed) {
    await page.getByRole('button', { name: /no, keep active/i }).click().catch(() => {})
    await page.waitForTimeout(500)
    await shot('p2-keep-active')
    state.p2ArchiveDismissed = true
    saveState()
  }
  if (stopIfDone('p2-keep-active')) throw { __stop: true }

  if (!state.p2NotesReportExplored) {
    await gotoWorkspace(state.project2Id)
    await page.getByText('Notes and Report', { exact: true }).click()
    await page.waitForTimeout(700)
    await shot('p2-notes-and-report-tab')
    state.p2NotesReportExplored = true
    saveState()
  }
  if (stopIfDone('p2-notes-report-explore')) throw { __stop: true }

  if (!state.p2ReportViewed) {
    await gotoWorkspace(state.project2Id)
    await page.getByText('Notes and Report', { exact: true }).click()
    await page.waitForTimeout(600)
    await page.getByRole('button', { name: /view report/i }).click()
    await page.waitForTimeout(1200)
    await shot('p2-project-report')
    state.p2ReportViewed = true
    saveState()
  }
  if (stopIfDone('p2-report-viewed')) throw { __stop: true }

  if (!state.p2ReportScrolled) {
    await page.mouse.wheel(0, 1200)
    await page.waitForTimeout(500)
    await shot('p2-project-report-scrolled')
    state.p2ReportScrolled = true
    saveState()
  }
  if (stopIfDone('p2-report-scrolled')) throw { __stop: true }

  if (!state.globalReportsExplored) {
    await page.goto(`${BASE}/reports`)
    await page.waitForTimeout(1200)
    await shot('global-reports-list')
    state.globalReportsExplored = true
    saveState()
  }
  if (stopIfDone('global-reports-explored')) throw { __stop: true }

  console.log('STATE:', JSON.stringify(state, null, 2))

  console.log('STATE:', JSON.stringify(state, null, 2))
} catch (e) {
  if (!e || !e.__stop) throw e
} finally {
  console.log('CONSOLE ERRORS:', JSON.stringify(errors, null, 2))
  await browser.close()
}
