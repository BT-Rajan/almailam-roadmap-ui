import type { ROUTE_NAMES } from '@/constants/routeNames'

export type RouteNameValue = (typeof ROUTE_NAMES)[keyof typeof ROUTE_NAMES]

export type LayoutName = 'auth' | 'dashboard'

declare module 'vue-router' {
  interface RouteMeta {
    layout: LayoutName
  }
}
