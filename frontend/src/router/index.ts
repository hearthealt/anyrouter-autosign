import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn } from '../utils/auth'

const Login = () => import('../views/Login.vue')
const Dashboard = () => import('../views/Dashboard.vue')
const Accounts = () => import('../views/Accounts.vue')
const AccountDetail = () => import('../views/AccountDetail.vue')
const SignLogs = () => import('../views/SignLogs.vue')
const Statistics = () => import('../views/Statistics.vue')
const Platforms = () => import('../views/Platforms.vue')
const Settings = () => import('../views/Settings.vue')
const UiLab = () => import('../views/UiLab.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Login,
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard,
      meta: { requiresAuth: true }
    },
    {
      path: '/accounts',
      name: 'accounts',
      component: Accounts,
      meta: { requiresAuth: true }
    },
    {
      path: '/logs',
      name: 'sign-logs',
      component: SignLogs,
      meta: { requiresAuth: true }
    },
    {
      path: '/statistics',
      name: 'statistics',
      component: Statistics,
      meta: { requiresAuth: true }
    },
    {
      path: '/platforms',
      name: 'platforms',
      component: Platforms,
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'settings',
      component: Settings,
      meta: { requiresAuth: true }
    },
    {
      path: '/account/:id',
      name: 'account-detail',
      component: AccountDetail,
      meta: { requiresAuth: true }
    },
    {
      // 设计系统实验室。开发期工具，不挂进导航，改令牌或原语后先看这里。
      // 生产构建里 import.meta.env.DEV 为 false，这条路由不会注册。
      ...(import.meta.env.DEV
        ? { path: '/ui-lab', name: 'ui-lab', component: UiLab, meta: { requiresAuth: false } }
        : { path: '/ui-lab', redirect: '/' }),
    }
  ]
})

router.beforeEach((to, _from, next) => {
  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth && !isLoggedIn()) {
    next({ path: '/login', query: to.path !== '/' ? { redirect: to.fullPath } : undefined })
  } else if (to.path === '/login' && isLoggedIn()) {
    next('/')
  } else {
    next()
  }
})

export default router
