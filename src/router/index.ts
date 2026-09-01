import { nextTick } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'

import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'
import { useToastStore } from '@/stores/toastStore'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login',
    },
    {
      path: '/login',
      name: ROUTE_NAMES.LOGIN,
      component: () => import('@/pages/LoginPage.vue'),
      meta: { layout: 'auth' },
    },
    {
      path: '/customer-portal',
      name: ROUTE_NAMES.CUSTOMER_PORTAL_LOGIN,
      component: () => import('@/pages/CustomerPortalLoginPage.vue'),
      meta: { layout: 'customer-portal' },
    },
    {
      // Landed on right after login -- auto-redirects straight into the
      // one project a customer has, or shows a picker when they have
      // more than one (see CustomerPortalProjectsPage.vue). Login no
      // longer carries a single project ID with it the way the old
      // mobile+projectId verify flow did.
      path: '/customer-portal/projects',
      name: ROUTE_NAMES.CUSTOMER_PORTAL_PROJECTS,
      component: () => import('@/pages/CustomerPortalProjectsPage.vue'),
      meta: { layout: 'customer-portal', requiresAuth: true },
    },
    {
      path: '/customer-portal/:projectId',
      name: ROUTE_NAMES.CUSTOMER_PORTAL_PROJECT,
      component: () => import('@/pages/CustomerProjectViewPage.vue'),
      meta: { layout: 'customer-portal', requiresAuth: true },
    },
    {
      path: '/site-portal',
      name: ROUTE_NAMES.SITE_PORTAL_LOGIN,
      component: () => import('@/pages/SitePortalLoginPage.vue'),
      meta: { layout: 'site-portal' },
    },
    {
      path: '/site-portal/report',
      name: ROUTE_NAMES.SITE_PORTAL_REPORT,
      component: () => import('@/pages/SitePortalReportPage.vue'),
      meta: { layout: 'site-portal', requiresAuth: true },
    },
    {
      path: '/site-portal/calendar',
      name: ROUTE_NAMES.SITE_PORTAL_CALENDAR,
      component: () => import('@/pages/SitePortalCalendarPage.vue'),
      meta: { layout: 'site-portal', requiresAuth: true },
    },
    {
      path: '/dashboard',
      name: ROUTE_NAMES.DASHBOARD,
      component: () => import('@/pages/DashboardPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard' }],
      },
    },
    {
      path: '/projects',
      name: ROUTE_NAMES.PROJECTS,
      component: () => import('@/pages/ProjectsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Projects' }],
      },
    },
    {
      path: '/projects/new',
      name: ROUTE_NAMES.PROJECT_NEW,
      component: () => import('@/pages/NewProjectWizardPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Projects', routeName: ROUTE_NAMES.PROJECTS },
          { label: 'New Project' },
        ],
      },
    },
    {
      path: '/projects/:projectId',
      name: ROUTE_NAMES.PROJECT_WORKSPACE,
      component: () => import('@/pages/ProjectWorkspacePage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Projects', routeName: ROUTE_NAMES.PROJECTS },
          { label: 'Project' },
        ],
      },
    },
    {
      path: '/clients',
      name: ROUTE_NAMES.CLIENTS,
      component: () => import('@/pages/ClientsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Clients' }],
      },
    },
    {
      path: '/clients/new',
      name: ROUTE_NAMES.CLIENT_NEW,
      component: () => import('@/pages/NewClientWizardPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Clients', routeName: ROUTE_NAMES.CLIENTS },
          { label: 'New Client' },
        ],
      },
    },
    {
      path: '/clients/:clientId',
      name: ROUTE_NAMES.CLIENT_WORKSPACE,
      component: () => import('@/pages/ClientWorkspacePage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Clients', routeName: ROUTE_NAMES.CLIENTS },
          { label: 'Client' },
        ],
      },
    },
    {
      path: '/government/forms',
      name: ROUTE_NAMES.GOVERNMENT_FORMS,
      component: () => import('@/pages/GovernmentFormsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Government Center' },
          { label: 'Forms' },
        ],
      },
    },
    {
      path: '/government/authorities',
      name: ROUTE_NAMES.GOVERNMENT_AUTHORITIES,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Authority Directory' },
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Government Center' },
          { label: 'Authorities' },
        ],
      },
    },
    {
      path: '/government/submissions',
      name: ROUTE_NAMES.GOVERNMENT_SUBMISSIONS,
      component: () => import('@/pages/GovernmentSubmissionsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Government Center' },
          { label: 'Submissions' },
        ],
      },
    },
    {
      path: '/government/submissions/:submissionNo',
      name: ROUTE_NAMES.SUBMISSION_WORKSPACE,
      component: () => import('@/pages/SubmissionWorkspacePage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Government Center' },
          { label: 'Submissions', routeName: ROUTE_NAMES.GOVERNMENT_SUBMISSIONS },
          { label: 'Submission' },
        ],
      },
    },
    {
      path: '/documents',
      name: ROUTE_NAMES.DOCUMENTS,
      component: () => import('@/pages/DocumentsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Documents' }],
      },
    },
    {
      path: '/documents/:documentId',
      name: ROUTE_NAMES.DOCUMENT_VIEWER,
      component: () => import('@/pages/DocumentViewerPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Documents', routeName: ROUTE_NAMES.DOCUMENTS },
          { label: 'Viewer' },
        ],
      },
    },
    {
      path: '/knowledge-base',
      name: ROUTE_NAMES.KNOWLEDGE_BASE,
      component: () => import('@/pages/KnowledgeBasePage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Knowledge Base' }],
      },
    },
    {
      path: '/tasks',
      name: ROUTE_NAMES.TASKS,
      component: () => import('@/pages/TasksPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Tasks' }],
      },
    },
    {
      path: '/tasks/my',
      name: ROUTE_NAMES.MY_TASKS,
      component: () => import('@/pages/MyTasksPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Tasks', routeName: ROUTE_NAMES.TASKS },
          { label: 'My Tasks' },
        ],
      },
    },
    {
      path: '/status-reports/inbox',
      name: ROUTE_NAMES.STATUS_REPORTS_INBOX,
      component: () => import('@/pages/StatusReportInboxPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Status Report Inbox' },
        ],
      },
    },
    {
      path: '/reports',
      name: ROUTE_NAMES.REPORTS,
      component: () => import('@/pages/ReportsListPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Reports' }],
      },
    },
    {
      path: '/reports/executive',
      name: ROUTE_NAMES.REPORT_EXECUTIVE,
      component: () => import('@/pages/ExecutiveReportPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Reports', routeName: ROUTE_NAMES.REPORTS },
          { label: 'Executive Summary' },
        ],
      },
    },
    {
      path: '/reports/project',
      name: ROUTE_NAMES.REPORT_PROJECT,
      component: () => import('@/pages/ProjectReportPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Reports', routeName: ROUTE_NAMES.REPORTS },
          { label: 'Project Performance' },
        ],
      },
    },
    {
      path: '/reports/workload',
      name: ROUTE_NAMES.REPORT_WORKLOAD,
      component: () => import('@/pages/WorkloadReportPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Reports', routeName: ROUTE_NAMES.REPORTS },
          { label: 'Team Workload' },
        ],
      },
    },
    {
      path: '/admin',
      name: ROUTE_NAMES.ADMIN,
      component: () => import('@/pages/AdministrationPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Administration' }],
      },
    },
    {
      path: '/admin/users',
      name: ROUTE_NAMES.ADMIN_USERS,
      component: () => import('@/pages/UserManagementPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'Users' },
        ],
      },
    },
    {
      path: '/admin/catalogs',
      name: ROUTE_NAMES.ADMIN_CATALOGS,
      component: () => import('@/pages/AdminCatalogsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'Catalogs' },
        ],
      },
    },
    {
      path: '/admin/documents',
      name: ROUTE_NAMES.ADMIN_DOCUMENTS,
      component: () => import('@/pages/AdminDocumentsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'Documents' },
        ],
      },
    },
    {
      path: '/admin/ai',
      name: ROUTE_NAMES.ADMIN_AI,
      component: () => import('@/pages/AdminAIPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        // Provider keys, the grounding prompt, and every other setting on
        // this page are administrator-only -- the backend already
        // enforces this (Administration permission on every /api/ai/*
        // route), but a non-admin who navigates here directly previously
        // still saw the page shell before its API calls failed. Redirect
        // before that happens instead.
        adminOnly: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'AI' },
        ],
      },
    },
    {
      path: '/admin/company',
      name: ROUTE_NAMES.ADMIN_COMPANY,
      component: () => import('@/pages/AdminCompanyPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'Company' },
        ],
      },
    },
    {
      path: '/admin/audit-log',
      name: ROUTE_NAMES.ADMIN_AUDIT_LOG,
      component: () => import('@/pages/AdminAuditLogPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'Audit Log' },
        ],
      },
    },
    {
      // Not nested under /admin -- every authenticated user lands here
      // (from the header icon), and the page itself shows only their own
      // activity unless they're an Administrator. See ActivityCalendarPage.vue.
      path: '/activity-calendar',
      name: ROUTE_NAMES.ADMIN_ACTIVITY_CALENDAR,
      component: () => import('@/pages/ActivityCalendarPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'Activity Calendar' },
        ],
      },
    },
    {
      // Reached from the header user menu ("My Profile"), not from the
      // sidebar -- every authenticated user gets one, editing only their
      // own account. See ProfilePage.vue.
      path: '/profile',
      name: ROUTE_NAMES.MY_PROFILE,
      component: () => import('@/pages/ProfilePage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'My Profile' },
        ],
      },
    },
    {
      path: '/messages',
      name: ROUTE_NAMES.MESSAGE_CENTRE,
      component: () => import('@/pages/MessageCentrePage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Message Centre' }],
      },
    },
    {
      path: '/payments',
      name: ROUTE_NAMES.PAYMENTS,
      component: () => import('@/pages/PaymentsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'Dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'Payments' }],
      },
    },
    {
      path: '/:pathMatch(.*)*',
      name: ROUTE_NAMES.NOT_FOUND,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { title: 'Page Not Found' },
      meta: { layout: 'auth' },
    },
  ],
})

router.beforeEach((to) => {
  const authStore = useAuthStore()

  // No session-restore-on-load here, deliberately -- a page refresh, a
  // reopened tab, or a freshly relaunched browser all start logged out.
  // (authStore no longer has a hydrate()/silent-cookie-restore step; see
  // its tryRefresh() comment.) Only genuine mid-session token renewal
  // (via httpClient's 401 retry, while the SPA is still running) uses the
  // refresh cookie.

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // Site/customer portal routes bounce to their own login, not the
    // staff one -- same session mechanism underneath, different entry
    // point, and someone hitting a bare portal link shouldn't land on
    // the staff sign-in screen.
    const loginRoute =
      to.meta.layout === 'site-portal'
        ? ROUTE_NAMES.SITE_PORTAL_LOGIN
        : to.meta.layout === 'customer-portal'
          ? ROUTE_NAMES.CUSTOMER_PORTAL_LOGIN
          : ROUTE_NAMES.LOGIN
    return { name: loginRoute, query: { redirect: to.fullPath } }
  }

  if (
    authStore.isAuthenticated &&
    (to.name === ROUTE_NAMES.LOGIN ||
      to.name === ROUTE_NAMES.SITE_PORTAL_LOGIN ||
      to.name === ROUTE_NAMES.CUSTOMER_PORTAL_LOGIN)
  ) {
    const homeRoute =
      to.name === ROUTE_NAMES.SITE_PORTAL_LOGIN
        ? ROUTE_NAMES.SITE_PORTAL_REPORT
        : to.name === ROUTE_NAMES.CUSTOMER_PORTAL_LOGIN
          ? ROUTE_NAMES.CUSTOMER_PORTAL_PROJECTS
          : ROUTE_NAMES.DASHBOARD
    return { name: homeRoute }
  }

  // Backend-enforced already (every /api/ai/* route requires the
  // Administration permission, which only the Administrator role has) --
  // this stops a non-admin from even seeing the page shell before its API
  // calls fail, rather than relying solely on that 403.
  if (to.meta.adminOnly && authStore.user?.role !== 'Administrator') {
    useToastStore().show('error', 'Access denied', 'This page is only available to administrators.')
    return { name: ROUTE_NAMES.DASHBOARD }
  }

  return true
})

router.afterEach((to, from, failure) => {
  // A beforeEach redirect (see above) fires afterEach twice -- once for the
  // aborted intermediate navigation (with a failure), once for the actual
  // destination -- so this only runs once, for wherever navigation really
  // landed.
  if (failure) return

  // Ignore navigations that only change query/hash on the same route (e.g.
  // filter state) -- nothing new was actually shown, so don't move focus.
  if (to.path === from.path) return

  void nextTick(() => {
    // Only take the focus landmark if nothing more specific already has
    // it (e.g. a page's own autofocus, like StaffLoginForm's ID field).
    // Since this runs after nextTick, it's safe regardless of whether it
    // resolves before or after the new page's own onMounted -- either way
    // the more specific element ends up focused.
    const active = document.activeElement
    if (active === document.body || active === document.documentElement || active === null) {
      document.getElementById('main-content')?.focus({ preventScroll: true })
    }
  })
})

export default router
