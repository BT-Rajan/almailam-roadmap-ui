// SECURITY NOTE: This is demo-only, client-side "verification" with no
// backend counterpart -- there is no customer-portal auth endpoint in the
// FastAPI backend at all. The valid phone-number/project-ID pairs below
// ship in the JavaScript bundle and are checked entirely in the browser,
// so anyone who opens devtools (or just reads this page's own "Demo
// Project IDs" card) has every valid credential. This is fine for a demo
// build but must not be treated as real authentication -- a production
// version needs server-side verification (e.g. an OTP sent to the
// customer's phone, checked against a real customer/contact record) before
// this portal is exposed publicly.
export const DEMO_CUSTOMER_PORTAL_PROJECTS: { id: string; name: string; phone: string }[] = [
  { id: 'PROJ-2024-001', name: 'Metro Rail Phase 2', phone: '+91 9876543210' },
  { id: 'PROJ-2024-002', name: 'Highway Expansion', phone: '+91 9876543212' },
  { id: 'PROJ-2024-003', name: 'Water Treatment Plant', phone: '+91 9876543214' },
]

export const DEMO_CUSTOMER_PORTAL_CREDENTIALS: Record<string, string[]> = {
  'PROJ-2024-001': ['9876543210', '9876543211'],
  'PROJ-2024-002': ['9876543212', '9876543213'],
  'PROJ-2024-003': ['9876543214'],
}
