<!--
  MainLayout：后台的整体框架（左侧菜单 + 顶部栏 + 内容区）。
  子页面会被渲染到 <router-view /> 的位置，所以每个页面自己不用再写菜单。
-->
<template>
  <el-container class="layout">
    <!-- 左侧菜单 -->
    <el-aside width="220px" class="aside">
      <div class="logo">
        <el-icon><Coin /></el-icon>
        <span>个贷风控系统</span>
      </div>

      <!--
        点击菜单项由 handleSelect 统一处理：已开放的模块跳转，
        未开放的模块只给出提示；default-active 控制当前高亮哪一项
      -->
      <el-menu
        :default-active="activePath"
        background-color="#1f2d3d"
        text-color="#bfcbd9"
        active-text-color="#ffffff"
        @select="handleSelect"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/loans">
          <el-icon><Document /></el-icon>
          <span>贷款申请</span>
        </el-menu-item>
        <el-menu-item index="/repayment">
          <el-icon><Money /></el-icon>
          <span>还款管理</span>
        </el-menu-item>
        <el-menu-item index="/datasource">
          <el-icon><Connection /></el-icon>
          <span>数据源管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶部栏 -->
      <el-header class="header">
        <div class="title">{{ route.meta.title }}</div>

        <el-dropdown @command="handleCommand">
          <span class="user">
            <el-avatar :size="28" style="background-color: #409eff">{{ userName.slice(0, 1) }}</el-avatar>
            <span>{{ userName }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <!-- 内容区：每个页面的内容出现在这里 -->
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()

// 登录时存下来的用户名（没有就用默认值）
const userName = ref(localStorage.getItem('userName') || '管理员')

// /loans/LN2026... 详情页也要让“贷款申请”这个菜单保持高亮
const activePath = computed(() => {
  if (route.path.startsWith('/loans')) return '/loans'
  return route.path
})

// 还没开放的模块：点击只给出提示，不做跳转
function handleSelect(index) {
  if (index === '/repayment' || index === '/datasource') {
    ElMessage.info('该功能还未开发，敬请期待')
    return
  }
  router.push(index)
}

async function handleCommand(command) {
  if (command !== 'logout') return
  await ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' })
  localStorage.removeItem('token')
  router.replace('/login')
}
</script>

<style scoped>
.layout {
  height: 100%;
}

.aside {
  background-color: #1f2d3d;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 60px;
  color: #fff;
  font-size: 17px;
  font-weight: 600;
  background-color: #17222e;
}

/* 去掉菜单右侧自带的一条竖线，看起来更干净 */
.aside :deep(.el-menu) {
  border-right: none;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
}

.title {
  font-size: 17px;
  font-weight: 600;
}

.user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #606266;
  outline: none;
}

.main {
  padding: 16px;
  overflow-y: auto;
}
</style>