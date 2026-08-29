import DOMPurify from 'dompurify'

// Mirrors the backend allowlist (app/core/html_sanitizer.py) -- this is
// the client-side pass, run both on what the rich-text editor produces
// and again when rendering saved content back out, since content can
// have come from the API rather than from the editor itself.
const ALLOWED_TAGS = ['p', 'br', 'b', 'strong', 'i', 'em', 'u', 'span', 'ul', 'ol', 'li', 'img']
const ALLOWED_ATTR = ['style', 'src', 'alt']

DOMPurify.addHook('uponSanitizeAttribute', (node, data) => {
  if (data.attrName !== 'style') return
  if (node.nodeName !== 'SPAN') {
    data.keepAttr = false
    return
  }
  const match = /^font-size:\s*(\d{1,3})px;?$/i.exec(data.attrValue.trim())
  data.attrValue = match ? `font-size:${match[1]}px` : ''
  data.keepAttr = Boolean(match)
})

export function sanitizeHtml(value: string | null | undefined): string {
  if (!value) return ''
  return DOMPurify.sanitize(value, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOWED_URI_REGEXP: /^(?:https?|data):/i,
  })
}
