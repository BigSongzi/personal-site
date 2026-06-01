// 文档相关 API
import http from './index'

export const apiListDocs = (params) => http.get('/api/docs', { params })
export const apiCategories = () => http.get('/api/docs/categories')
export const apiGetDoc = (id) => http.get(`/api/docs/${id}`)
export const apiCreateDoc = (payload) => http.post('/api/docs', payload)
export const apiUpdateDoc = (id, payload) => http.put(`/api/docs/${id}`, payload)
export const apiDeleteDoc = (id) => http.delete(`/api/docs/${id}`)

// 上传图片(供 Markdown 编辑器自定义上传钩子使用)
export const apiUpload = (file) => {
  const fd = new FormData()
  fd.append('file', file)
  return http.post('/api/upload', fd, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
