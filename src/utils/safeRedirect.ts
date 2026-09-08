// Guards the ?redirect= query param the router's auth guard attaches
// before bouncing to a login page (see router/index.ts). Vue Router
// already re-runs its guards on whatever this resolves to, so this
// isn't a real open-redirect today -- but a bare string handed straight
// to router.push() is one router-config change away from becoming one.
// Only a same-app path ('/something', never '//host/...' which browsers
// and some router configs treat as protocol-relative) is trusted; anything
// else falls back to the caller's own default route.
export function safeRedirectPath(redirect: string | undefined): string | undefined {
  if (!redirect) return undefined
  if (!redirect.startsWith('/') || redirect.startsWith('//')) return undefined
  return redirect
}
