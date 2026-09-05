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
        breadcrumbs: [{ label: 'breadcrumb.dashboard' }],
      },
    },
    {
      path: '/projects',
      name: ROUTE_NAMES.PROJECTS,
      component: () => import('@/pages/ProjectsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'breadcrumb.projects' }],
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
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.projects', routeName: ROUTE_NAMES.PROJECTS },
          { label: 'breadcrumb.newProject' },
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
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.projects', routeName: ROUTE_NAMES.PROJECTS },
          { label: 'breadcrumb.project' },
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
        breadcrumbs: [{ label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'breadcrumb.clients' }],
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
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.clients', routeName: ROUTE_NAMES.CLIENTS },
          { label: 'breadcrumb.newClient' },
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
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.clients', routeName: ROUTE_NAMES.CLIENTS },
          { label: 'breadcrumb.client' },
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
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.governmentCenter' },
          { label: 'breadcrumb.forms' },
        ],
      },
    },
    {
      path: '/government/authorities',
      name: ROUTE_NAMES.GOVERNMENT_AUTHORITIES,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { titleKey: 'placeholder.authorityDirectory' },
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.governmentCenter' },
          { label: 'breadcrumb.authorities' },
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
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.governmentCenter' },
          { label: 'breadcrumb.submissions' },
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
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.governmentCenter' },
          { label: 'breadcrumb.submissions', routeName: ROUTE_NAMES.GOVERNMENT_SUBMISSIONS },
          { label: 'breadcrumb.submission' },
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
        breadcrumbs: [{ label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'breadcrumb.documents' }],
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
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.documents', routeName: ROUTE_NAMES.DOCUMENTS },
          { label: 'breadcrumb.viewer' },
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
        breadcrumbs: [{ label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'breadcrumb.knowledgeBase' }],
      },
    },
    {
      path: '/tasks',
      name: ROUTE_NAMES.TASKS,
      component: () => import('@/pages/TasksPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'breadcrumb.tasks' }],
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
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.tasks', routeName: ROUTE_NAMES.TASKS },
          { label: 'breadcrumb.myTasks' },
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
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.statusReportInbox' },
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
        breadcrumbs: [{ label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'breadcrumb.reports' }],
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
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.reports', routeName: ROUTE_NAMES.REPORTS },
          { label: 'breadcrumb.executiveSummary' },
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
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.reports', routeName: ROUTE_NAMES.REPORTS },
          { label: 'breadcrumb.projectPerformance' },
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
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.reports', routeName: ROUTE_NAMES.REPORTS },
          { label: 'breadcrumb.teamWorkload' },
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
        // Administration is Administrator-only, full stop -- the backend
        // already enforces this (every /api/users, /api/roles, etc. route
        // requires the Administration permission, which only the
        // Administrator role has by default), but the frontend previously
        // let any authenticated user navigate here and see the module
        // grid before its API calls 403'd. Same fix as adminOnly below
        // applied to the whole /admin/* subtree, not just AI.
        adminOnly: true,
        breadcrumbs: [{ label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'breadcrumb.administration' }],
      },
    },
    {
      path: '/admin/users',
      name: ROUTE_NAMES.ADMIN_USERS,
      component: () => import('@/pages/UserManagementPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        adminOnly: true,
        breadcrumbs: [
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'breadcrumb.users' },
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
        adminOnly: true,
        breadcrumbs: [
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'breadcrumb.catalogs' },
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
        adminOnly: true,
        breadcrumbs: [
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'breadcrumb.documents' },
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
        adminOnly: true,
        breadcrumbs: [
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'breadcrumb.ai' },
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
        adminOnly: true,
        breadcrumbs: [
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'breadcrumb.company' },
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
        adminOnly: true,
        breadcrumbs: [
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.administration', routeName: ROUTE_NAMES.ADMIN },
          { label: 'breadcrumb.auditLog' },
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
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.activityCalendar' },
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
          { label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD },
          { label: 'breadcrumb.myProfile' },
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
        breadcrumbs: [{ label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'breadcrumb.messageCentre' }],
      },
    },
    {
      path: '/payments',
      name: ROUTE_NAMES.PAYMENTS,
      component: () => import('@/pages/PaymentsPage.vue'),
      meta: {
        layout: 'dashboard',
        requiresAuth: true,
        breadcrumbs: [{ label: 'breadcrumb.dashboard', routeName: ROUTE_NAMES.DASHBOARD }, { label: 'breadcrumb.payments' }],
      },
    },
    {
      path: '/:pathMatch(.*)*',
      name: ROUTE_NAMES.NOT_FOUND,
      component: () => import('@/pages/PlaceholderPage.vue'),
      props: { titleKey: 'placeholder.pageNotFound' },
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
