import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

interface RouteMeta {
  auth?: boolean
  admin?: boolean
  guest?: boolean
}

const routes: Array<{ path: string; name?: string; component: () => Promise<unknown>; meta?: RouteMeta }> = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { guest: true },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { auth: true },
  },
  {
    path: '/tickets/create',
    name: 'CreateTicket',
    component: () => import('@/views/CreateTicketView.vue'),
    meta: { auth: true },
  },
  {
    path: '/tickets/:id',
    name: 'TicketDetail',
    component: () => import('@/views/TicketDetailView.vue'),
    meta: { auth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { auth: true },
  },
  {
    path: '/admin',
    name: 'AdminCabinet',
    component: () => import('@/views/AdminCabinetView.vue'),
    meta: { auth: true, admin: true },
  },
  {
    path: '/admin/tickets',
    name: 'AdminDashboard',
    component: () => import('@/views/AdminDashboardView.vue'),
    meta: { auth: true, admin: true },
  },
  {
    path: '/admin/tickets/:id',
    name: 'AdminTicketDetail',
    component: () => import('@/views/AdminTicketDetailView.vue'),
    meta: { auth: true, admin: true },
  },
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: () => import('@/views/AdminUsersView.vue'),
    meta: { auth: true, admin: true },
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPasswordView.vue'),
    meta: { guest: true },
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('@/views/ResetPasswordView.vue'),
    meta: { guest: true },
  },
  {
    path: '/admin/audit',
    name: 'AdminAuditLog',
    component: () => import('@/views/AdminAuditLogView.vue'),
    meta: { auth: true, admin: true },
  },
  {
    path: '/verify-email',
    name: 'VerifyEmail',
    component: () => import('@/views/VerifyEmailView.vue'),
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('@/views/AboutView.vue'),
  },
  {
    path: '/error',
    name: 'Error',
    component: () => import('@/views/ErrorView.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes: routes as any,
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta?.auth && !auth.isAuthenticated) {
    next('/login')
  } else if (to.meta?.admin && !auth.isAdmin) {
    next('/dashboard')
  } else if (to.meta?.guest && auth.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
