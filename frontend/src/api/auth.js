// 鉴权相关 API
import http from './index'

export const apiLogin = (username, password) =>
  http.post('/api/auth/login', { username, password })

export const apiMe = () => http.get('/api/auth/me')
