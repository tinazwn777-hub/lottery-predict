import axios from 'axios'

const API_BASE = '/api/v1'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000
})

// Task APIs
export const taskApi = {
  // Create a new task
  createTask(data) {
    return api.post('/tasks', data)
  },

  // Get task details
  getTask(taskId) {
    return api.get(`/tasks/${taskId}`)
  },

  // Get task status
  getTaskStatus(taskId) {
    return api.get(`/tasks/${taskId}/status`)
  },

  // List all tasks
  listTasks(params = { limit: 20, offset: 0 }) {
    return api.get('/tasks', { params })
  },

  // Regenerate image with theme
  regenerateImage(taskId, theme) {
    return api.post(`/tasks/${taskId}/regenerate/${theme}`)
  },

  // Delete task
  deleteTask(taskId) {
    return api.delete(`/tasks/${taskId}`)
  }
}

// Upload APIs
export const uploadApi = {
  uploadFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/uploads/file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  deleteFile(filename) {
    return api.delete(`/uploads/file/${filename}`)
  }
}

export default api
