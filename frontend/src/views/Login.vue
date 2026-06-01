<script setup>
// 管理员登录页
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiLogin } from '@/api/auth'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const formRef = ref(null)

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function onSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res = await apiLogin(form.username, form.password)
      auth.save(res.data.token, res.data.username)
      ElMessage.success('登录成功')
      const r = route.query.redirect || '/docs'
      router.push(r)
    } finally {
      loading.value = false
    }
  })
}
</script>

<template>
  <div style="height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#667eea,#764ba2);">
    <el-card style="width:360px;">
      <h2 style="text-align:center;margin:0 0 16px 0;">管理员登录</h2>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="0" @submit.prevent="onSubmit">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" :prefix-icon="'User'" autocomplete="username" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" :prefix-icon="'Lock'"
                    show-password autocomplete="current-password" @keyup.enter="onSubmit" />
        </el-form-item>
        <el-button type="primary" style="width:100%;" :loading="loading" @click="onSubmit">登 录</el-button>
      </el-form>
      <p style="color:#909399;font-size:12px;margin-top:12px;text-align:center;">
        默认账号见 backend/.env
      </p>
    </el-card>
  </div>
</template>
