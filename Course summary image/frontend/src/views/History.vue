<template>
  <div class="history-view">
    <el-card class="history-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><Clock /></el-icon>
          <span>任务历史</span>
          <el-button
            v-if="tasks.length"
            type="danger"
            size="small"
            text
            @click="handleBatchDelete"
          >
            清空历史
          </el-button>
        </div>
      </template>

      <div v-if="loading" class="loading-container">
        <el-icon class="loading-spinner"><Loading /></el-icon>
        <p>加载中...</p>
      </div>

      <div v-else-if="!tasks.length" class="empty-container">
        <el-icon size="64" color="#ccc"><Document /></el-icon>
        <p>暂无任务记录</p>
        <el-button type="primary" @click="goHome">开始生成</el-button>
      </div>

      <div v-else class="task-list">
        <div
          v-for="task in tasks"
          :key="task.id"
          class="task-item"
          @click="viewTaskDetail(task)"
        >
          <div class="task-status" :class="task.status">
            <el-icon v-if="task.status === 'pending'"><Clock /></el-icon>
            <el-icon v-else-if="task.status === 'processing'"><Loading /></el-icon>
            <el-icon v-else-if="task.status === 'completed'"><Check /></el-icon>
            <el-icon v-else><Close /></el-icon>
          </div>

          <div class="task-info">
            <h4 class="task-title">
              {{ task.content?.title || getSourceLabel(task) }}
            </h4>
            <p class="task-meta">
              <el-tag :type="getStatusType(task.status)" size="small">
                {{ getStatusLabel(task.status) }}
              </el-tag>
              <span class="time">{{ formatTime(task.created_at) }}</span>
            </p>
          </div>

          <div class="task-actions" @click.stop>
            <el-button
              v-if="task.status === 'completed'"
              type="primary"
              size="small"
              @click="viewTaskDetail(task)"
            >
              查看
            </el-button>
            <el-button
              v-if="task.status === 'failed'"
              type="warning"
              size="small"
              @click="retryTask(task)"
            >
              重试
            </el-button>
            <el-popconfirm
              title="确定要删除此任务吗？"
              @confirm="deleteTask(task.id)"
            >
              <template #reference>
                <el-button type="danger" size="small" text>
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Task Detail Dialog -->
    <el-dialog
      v-model="detailVisible"
      title="任务详情"
      width="800px"
      destroy-on-close
    >
      <div v-if="selectedTask" class="task-detail">
        <div class="detail-header">
          <h3>{{ selectedTask.content?.title || '任务详情' }}</h3>
          <el-tag :type="getStatusType(selectedTask.status)">
            {{ getStatusLabel(selectedTask.status) }}
          </el-tag>
        </div>

        <div v-if="selectedTask.images?.length" class="detail-images">
          <el-carousel :interval="5000" type="card" height="300px">
            <el-carousel-item v-for="img in selectedTask.images" :key="img.id">
              <img
                :src="`/files/outputs/${img.local_path?.split('/').pop()}`"
                class="carousel-image"
              />
              <div class="carousel-label">{{ img.theme === 'light' ? '极简白底' : '深色主题' }}</div>
            </el-carousel-item>
          </el-carousel>
        </div>

        <div v-if="selectedTask.content" class="detail-content">
          <h4>提取内容</h4>
          <div v-for="(item, index) in selectedTask.content.items" :key="index">
            <h5>{{ index + 1 }}. {{ item.title }}</h5>
            <ul>
              <li v-for="(point, pIndex) in item.points" :key="pIndex">
                {{ point }}
              </li>
            </ul>
          </div>
        </div>

        <div v-if="selectedTask.error_message" class="detail-error">
          <el-alert
            :title="selectedTask.error_message"
            type="error"
            show-icon
          />
        </div>
      </div>

      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button
          v-if="selectedTask?.status === 'completed'"
          type="primary"
          @click="downloadCurrentImage"
        >
          下载当前主题
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useTaskStore } from '@/stores/task'
import {
  Clock, Loading, Check, Close, Document, Delete
} from '@element-plus/icons-vue'

const router = useRouter()
const taskStore = useTaskStore()

const loading = ref(true)
const tasks = ref([])
const detailVisible = ref(false)
const selectedTask = ref(null)
const currentPreviewTheme = ref('light')

onMounted(async () => {
  await loadTasks()
})

async function loadTasks() {
  loading.value = true
  try {
    await taskStore.fetchTasks()
    tasks.value = taskStore.tasks
  } catch (e) {
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

function getSourceLabel(task) {
  if (task.source_url) return task.source_url
  if (task.source_filename) return task.source_filename
  return '未知来源'
}

function getStatusLabel(status) {
  const labels = {
    pending: '等待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return labels[status] || status
}

function getStatusType(status) {
  const types = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

function viewTaskDetail(task) {
  selectedTask.value = task
  currentPreviewTheme.value = task.images?.[0]?.theme || 'light'
  detailVisible.value = true
}

async function retryTask(task) {
  try {
    // For now, just reload
    await loadTasks()
    ElMessage.success('已重新提交任务')
  } catch (e) {
    ElMessage.error('重试失败')
  }
}

async function deleteTask(taskId) {
  try {
    await taskStore.deleteTask(taskId)
    tasks.value = tasks.value.filter(t => t.id !== taskId)
    ElMessage.success('删除成功')
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

async function handleBatchDelete() {
  // Delete all tasks
  for (const task of tasks.value) {
    try {
      await taskStore.deleteTask(task.id)
    } catch (e) {
      // Continue with others
    }
  }
  tasks.value = []
  ElMessage.success('已清空历史记录')
}

function goHome() {
  router.push('/')
}

function downloadCurrentImage() {
  if (!selectedTask.value?.images?.length) return

  const img = selectedTask.value.images.find(
    i => i.theme === currentPreviewTheme.value
  )
  if (!img) return

  const link = document.createElement('a')
  link.href = `/files/outputs/${img.local_path?.split('/').pop()}`
  link.download = `summary-${currentPreviewTheme.value}-${Date.now()}.png`
  link.click()
}
</script>

<style lang="scss" scoped>
.history-view {
  max-width: 900px;
  margin: 0 auto;
}

.history-card {
  :deep(.el-card__header) {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #f8fafc;
    padding: 12px 20px;

    .card-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      color: #334155;
    }
  }
}

.loading-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #94a3b8;

  .loading-spinner {
    font-size: 48px;
    animation: spin 1s linear infinite;
    margin-bottom: 16px;
  }

  p {
    margin: 16px 0 0;
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: #f1f5f9;
    transform: translateX(4px);
  }

  .task-status {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;

    &.pending {
      background: #e0f2fe;
      color: #0284c7;
    }

    &.processing {
      background: #fef3c7;
      color: #d97706;
    }

    &.completed {
      background: #dcfce7;
      color: #16a34a;
    }

    &.failed {
      background: #fee2e2;
      color: #dc2626;
    }
  }

  .task-info {
    flex: 1;

    .task-title {
      margin: 0 0 8px;
      font-size: 15px;
      color: #1e293b;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .task-meta {
      display: flex;
      align-items: center;
      gap: 12px;
      margin: 0;

      .time {
        color: #94a3b8;
        font-size: 12px;
      }
    }
  }

  .task-actions {
    display: flex;
    gap: 8px;
  }
}

.task-detail {
  .detail-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid #e2e8f0;

    h3 {
      margin: 0;
      color: #1e293b;
    }
  }

  .detail-images {
    margin-bottom: 20px;

    .carousel-image {
      width: 100%;
      height: 100%;
      object-fit: contain;
      border-radius: 8px;
    }

    .carousel-label {
      position: absolute;
      bottom: 10px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(0, 0, 0, 0.7);
      color: white;
      padding: 4px 12px;
      border-radius: 4px;
      font-size: 12px;
    }
  }

  .detail-content {
    max-height: 300px;
    overflow-y: auto;
    padding: 16px;
    background: #f8fafc;
    border-radius: 8px;

    h4 {
      margin: 0 0 16px;
      color: #334155;
    }

    h5 {
      margin: 12px 0 8px;
      color: #3b82f6;
    }

    ul {
      padding-left: 20px;
      margin: 0;

      li {
        margin-bottom: 6px;
        color: #475569;
        font-size: 14px;
      }
    }
  }

  .detail-error {
    margin-top: 16px;
  }
}
</style>
