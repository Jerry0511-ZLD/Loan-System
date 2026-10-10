<!-- 登录页 -->
<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2 class="title">互联网个人贷款风控系统</h2>
      <p class="subtitle">审批管理端</p>

      <!--
        el-form 的 ref="formRef" 拿到的是表单实例，
        调用 formRef.value.validate() 就能触发表单校验
      -->
      <el-form ref="formRef" :model="form" :rules="rules" @keyup.enter="handleSubmit">
        <el-form-item prop="username">
          <el-input v-model="form.username" size="large" placeholder="用户名：admin">
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            size="large"
            type="password"
            show-password
            placeholder="密码：admin123"
          >
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-button type="primary" size="large" :loading="loading" class="submit" @click="handleSubmit">
          登 录
        </el-button>
      </el-form>

      <p class="tip">综设 I 演示版：账号 admin，密码 admin123（数据为本地模拟数据）</p>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login } from '@/api/user'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

// reactive：把普通对象变成“响应式”的，改了它页面会跟着变
const form = reactive({
  username: '',
  password: ''
})

// 表单校验规则
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ]
}

async function handleSubmit() {
  // 校验不通过就直接返回
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const data = await login(form)
    // 管理端只允许管理员登录（后端 user.role 为 admin / user）
    if (data.user && data.user.role && data.user.role !== 'admin') {
      ElMessage.error('该账号不是管理员，无法进入管理端')
      return
    }
    localStorage.setItem('token', data.token)
    localStorage.setItem('userName', data.user?.name || '管理员')
    ElMessage.success('登录成功')
    router.replace('/dashboard')
  } catch (error) {
    ElMessage.error(error.message || '登录失败')
  } finally {
    // finally 无论成功失败都会执行，用来关掉 loading
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: linear-gradient(135deg, #1c3d6e 0%, #2f7fd1 100%);
}

.login-card {
  width: 380px;
  padding: 8px 12px;
  border-radius: 10px;
}

.title {
  margin: 8px 0 4px;
  font-size: 20px;
  text-align: center;
}

.subtitle {
  margin: 0 0 24px;
  color: #909399;
  font-size: 13px;
  text-align: center;
}

.submit {
  width: 100%;
}

.tip {
  margin: 16px 0 4px;
  color: #a8abb2;
  font-size: 12px;
  text-align: center;
}
</style>