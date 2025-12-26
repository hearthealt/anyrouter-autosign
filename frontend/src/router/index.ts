import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn } from '../utils/auth'
import Dashboard from '../views/Dashboard.vue'
import Settings from '../views/Settings.vue'
import AccountDetail from '../views/AccountDetail.vue'
import SignLogs from '../views/SignLogs.vue'
import Statistics from '../views/Statistics.vue'
import Login from '../views/Login.vue'

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
    }
  ]
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth && !isLoggedIn()) {
    // 需要认证但未登录，跳转到登录页
    next('/login')
  } else if (to.path === '/login' && isLoggedIn()) {
    // 已登录访问登录页，跳转到首页
    next('/')
  } else {
    next()
  }
})

export default router
