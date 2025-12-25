import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Settings from '../views/Settings.vue'
import AccountDetail from '../views/AccountDetail.vue'
import SignLogs from '../views/SignLogs.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/logs',
      name: 'sign-logs',
      component: SignLogs
    },
    {
      path: '/settings',
      name: 'settings',
      component: Settings
    },
    {
      path: '/account/:id',
      name: 'account-detail',
      component: AccountDetail
    }
  ]
})

export default router
