import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { taskApi, uploadApi } from '@/api'

export const useTaskStore = defineStore('task', () => {
  // State
  const tasks = ref([])
  const currentTask = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const pendingTasks = computed(() =>
    tasks.value.filter(t => t.status === 'pending' || t.status === 'processing')
  )

  const completedTasks = computed(() =>
    tasks.value.filter(t => t.status === 'completed')
  )

  const failedTasks = computed(() =>
    tasks.value.filter(t => t.status === 'failed')
  )

  // Actions
  async function createTaskFromUrl(url, sourceType = 'web') {
    loading.value = true
    error.value = null

    try {
      const response = await taskApi.createTask({
        source_type: sourceType,
        source_url: url
      })
      currentTask.value = response.data
      tasks.value.unshift(response.data)
      return response.data
    } catch (e) {
      error.value = e.response?.data?.detail || '创建任务失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createTaskFromFile(file) {
    loading.value = true
    error.value = null

    try {
      // Upload file first
      const uploadResponse = await uploadApi.uploadFile(file)

      // Create task
      const response = await taskApi.createTask({
        source_type: 'pdf',
        source_filename: uploadResponse.data.filename
      })
      currentTask.value = response.data
      tasks.value.unshift(response.data)
      return response.data
    } catch (e) {
      error.value = e.response?.data?.detail || '上传文件失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchTasks() {
    loading.value = true
    try {
      const response = await taskApi.listTasks()
      tasks.value = response.data
    } catch (e) {
      error.value = e.response?.data?.detail || '获取任务列表失败'
    } finally {
      loading.value = false
    }
  }

  async function fetchTaskDetail(taskId) {
    loading.value = true
    try {
      const response = await taskApi.getTask(taskId)
      currentTask.value = response.data
      return response.data
    } catch (e) {
      error.value = e.response?.data?.detail || '获取任务详情失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function pollTaskStatus(taskId, onUpdate) {
    const poll = async () => {
      try {
        const response = await taskApi.getTaskStatus(taskId)
        onUpdate(response.data)

        if (response.data.status === 'completed' || response.data.status === 'failed') {
          return true // Done
        }

        // Continue polling
        setTimeout(poll, 2000)
        return false
      } catch (e) {
        throw e
      }
    }
    return poll()
  }

  async function regenerateImage(taskId, theme) {
    loading.value = true
    try {
      const response = await taskApi.regenerateImage(taskId, theme)
      return response.data
    } catch (e) {
      error.value = e.response?.data?.detail || '重新生成失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteTask(taskId) {
    loading.value = true
    try {
      await taskApi.deleteTask(taskId)
      tasks.value = tasks.value.filter(t => t.id !== taskId)
      if (currentTask.value?.id === taskId) {
        currentTask.value = null
      }
    } catch (e) {
      error.value = e.response?.data?.detail || '删除任务失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  function clearCurrentTask() {
    currentTask.value = null
  }

  return {
    // State
    tasks,
    currentTask,
    loading,
    error,
    // Getters
    pendingTasks,
    completedTasks,
    failedTasks,
    // Actions
    createTaskFromUrl,
    createTaskFromFile,
    fetchTasks,
    fetchTaskDetail,
    pollTaskStatus,
    regenerateImage,
    deleteTask,
    clearCurrentTask
  }
})
