// 金价相关 API
import http from './index'

export const apiGoldLatest = () => http.get('/api/gold/latest')
export const apiGoldHistory = (range = '24h') =>
  http.get('/api/gold/history', { params: { range } })
export const apiGoldConfig = () => http.get('/api/gold/config')
export const apiUpdateGoldConfig = (payload) =>
  http.put('/api/gold/config', payload)
export const apiGoldRefresh = () => http.post('/api/gold/refresh')
