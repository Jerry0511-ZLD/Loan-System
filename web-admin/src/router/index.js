import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layout/MainLayout.vue'

/**
 * 路由表 = “网址 -> 显示哪个页面”的对应关系。
 * 注意 component: () => import(...) 这种写法叫懒加载，
 * 只有访问到这个地址时才去下载对应的页面代码，首屏会更快。
 */
const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    component: MainLayout, // 带左侧菜单的整体框架
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '工作台' }
      },
      {
        path: 'loans',
        name: 'loanList',
        component: () => import('@/views/LoanList.vue'),
        meta: { title: '贷款申请' }
      },
      {
        path: 'loans/:id',
        name: 'loanDetail',
        component: () => import('@/views/LoanDetail.vue'),
        meta: { title: '申请详情' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

/**
 * 全局前置守卫：每次跳转前都会执行。
 * 作用：没登录的人不能进后台页面；已登录的人不用再看登录页。
 */
router.beforeEach((to) => {
  const token = localStorage.getItem('token')

  if (to.name !== 'login' && !token) {
    return { name: 'login' } // 打回登录页
  }
  if (to.name === 'login' && token) {
    return { name: 'dashboard' } // 已登录就别回登录页了
  }

  document.title = to.meta.title ? `${to.meta.title} - 个贷风控系统` : '个贷风控系统'
  return true
})

export default router