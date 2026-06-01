// Pinia store:管理 token + 用户名,localStorage 持久化
import { defineStore } from 'pinia'

const KEY = 'site_auth'

export const useAuthStore = defineStore('auth', {
  state: () => {
    const raw = localStorage.getItem(KEY)
    if (raw) {
      try { return JSON.parse(raw) } catch { /* ignore */ }
    }
    return { token: '', username: '' }
  },
  getters: {
    isLoggedIn: (s) => !!s.token
  },
  actions: {
    save(token, username) {
      this.token = token
      this.username = username
      localStorage.setItem(KEY, JSON.stringify({ token, username }))
    },
    clear() {
      this.token = ''
      this.username = ''
      localStorage.removeItem(KEY)
    }
  }
})
