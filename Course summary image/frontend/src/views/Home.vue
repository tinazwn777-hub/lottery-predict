<template>
  <div class="home-view">
    <!-- Input Section -->
    <el-card class="input-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><Upload /></el-icon>
          <span>输入内容源</span>
        </div>
      </template>

      <el-tabs v-model="activeTab" class="source-tabs">
        <!-- URL Input -->
        <el-tab-pane label="网页URL" name="url">
          <el-form :model="urlForm" @submit.prevent="handleUrlSubmit">
            <el-form-item>
              <el-input
                v-model="urlForm.url"
                placeholder="请输入网页URL，例如：https://example.com/article"
                size="large"
                :prefix-icon="Link"
                clearable
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="processing"
                @click="handleUrlSubmit"
                :disabled="!urlForm.url"
              >
                <el-icon><Picture /></el-icon>
                生成总结图片
              </el-button>
              <el-button size="large" @click="urlForm.url = ''">
                清空
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- PDF Upload -->
        <el-tab-pane label="PDF文件" name="pdf">
          <el-upload
            class="pdf-uploader"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            accept=".pdf"
            :limit="1"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽PDF文件到此处，或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持PDF文件，大小不超过50MB
              </div>
            </template>
          </el-upload>

          <el-button
            v-if="selectedFile"
            type="primary"
            size="large"
            :loading="processing"
            @click="handleFileSubmit"
            style="margin-top: 16px"
          >
            <el-icon><Picture /></el-icon>
            生成总结图片
          </el-button>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- Processing Status -->
    <el-card v-if="processing" class="status-card" shadow="never">
      <div class="processing-status">
        <el-icon class="loading-spinner"><Loading /></el-icon>
        <div class="status-info">
          <h3>正在处理...</h3>
          <p>{{ statusMessage }}</p>
          <el-progress
            :percentage="progress"
            :stroke-width="10"
            :status="progress === 100 ? 'success' : ''"
          />
        </div>
      </div>
    </el-card>

    <!-- Result Section -->
    <div v-if="resultTask" class="result-section">
      <!-- Theme Selection -->
      <el-card class="theme-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><Brush /></el-icon>
            <span>选择主题风格</span>
          </div>
        </template>

        <div class="theme-options">
          <div
            class="theme-option"
            :class="{ active: selectedTheme === 'light' }"
            @click="selectedTheme = 'light'"
          >
            <div class="theme-preview light-preview">
              <span class="preview-number">1</span>
              <div class="preview-content">
                <span class="preview-title">极简白底</span>
                <span class="preview-dot"></span>
                <span class="preview-dot"></span>
              </div>
            </div>
            <span class="theme-name">极简白底</span>
            <el-icon v-if="selectedTheme === 'light'" class="check-icon"><Check /></el-icon>
          </div>

          <div
            class="theme-option"
            :class="{ active: selectedTheme === 'dark' }"
            @click="selectedTheme = 'dark'"
          >
            <div class="theme-preview dark-preview">
              <span class="preview-number">2</span>
              <div class="preview-content">
                <span class="preview-title">深色主题</span>
                <span class="preview-dot"></span>
                <span class="preview-dot"></span>
              </div>
            </div>
            <span class="theme-name">深色主题</span>
            <el-icon v-if="selectedTheme === 'dark'" class="check-icon"><Check /></el-icon>
          </div>
        </div>
      </el-card>

      <!-- Preview -->
      <el-card class="preview-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><View /></el-icon>
            <span>预览结果</span>
            <el-button
              v-if="currentImage"
              type="primary"
              size="small"
              @click="downloadImage"
            >
              <el-icon><Download /></el-icon>
              下载图片
            </el-button>
          </div>
        </template>

        <div class="preview-container">
          <img
            v-if="currentImage"
            :src="currentImage"
            alt="Preview"
            class="preview-image"
          />
          <div v-else class="preview-placeholder">
            <el-icon size="64" color="#ccc"><Picture /></el-icon>
            <p>图片生成中...</p>
          </div>
        </div>

        <!-- Navigation for multiple images -->
        <div v-if="resultTask.images?.length > 1" class="image-nav">
          <el-button
            v-for="img in resultTask.images"
            :key="img.id"
            :type="getImageTheme(img) === selectedTheme ? 'primary' : 'default'"
            size="small"
            @click="switchTheme(getImageTheme(img))"
          >
            {{ getImageTheme(img) === 'light' ? '白底' : '深色' }}
          </el-button>
        </div>
      </el-card>

      <!-- Content Preview -->
      <el-card class="content-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><Document /></el-icon>
            <span>提取的内容</span>
          </div>
        </template>

        <div v-if="resultTask.content" class="content-preview">
          <h3>{{ resultTask.content.title }}</h3>
          <div
            v-for="(item, index) in resultTask.content.items"
            :key="index"
            class="content-section"
          >
            <h4>{{ index + 1 }}. {{ item.title }}</h4>
            <ul>
              <li v-for="(point, pIndex) in item.points" :key="pIndex">
                {{ point }}
              </li>
            </ul>
          </div>
        </div>
      </el-card>

      <!-- Actions -->
      <div class="result-actions">
        <el-button type="primary" size="large" @click="startNew">
          <el-icon><Plus /></el-icon>
          生成新的总结
        </el-button>
        <el-button size="large" @click="goToHistory">
          <el-icon><Clock /></el-icon>
          查看历史记录
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useTaskStore } from '@/stores/task'
import {
  Upload, Link, Picture, UploadFilled, Loading,
  Brush, View, Download, Document, Plus, Clock, Check
} from '@element-plus/icons-vue'

const router = useRouter()
const taskStore = useTaskStore()

// Tab state
const activeTab = ref('url')

// Form state
const urlForm = ref({ url: '' })
const selectedFile = ref(null)
const processing = ref(false)
const progress = ref(0)
const statusMessage = ref('')
const selectedTheme = ref('light')

// Result state
const resultTask = ref(null)
let pollTimer = null

const currentImage = computed(() => {
  if (!resultTask.value?.images?.length) return null

  const themeImages = resultTask.value.images.filter(
    img => img.theme === selectedTheme.value
  )
  return themeImages[0]?.local_path
    ? `/files/outputs/${themeImages[0].local_path.split('/').pop()}`
    : null
})

function handleFileChange(file) {
  if (file.raw) {
    // Validate PDF
    if (file.raw.type !== 'application/pdf') {
      ElMessage.error('只支持PDF文件')
      return
    }
    selectedFile.value = file.raw
  }
}

function handleFileRemove() {
  selectedFile.value = null
}

async function handleUrlSubmit() {
  if (!urlForm.value.url) {
    ElMessage.warning('请输入URL')
    return
  }

  await processSource('web', urlForm.value.url)
}

async function handleFileSubmit() {
  if (!selectedFile.value) {
    ElMessage.warning('请先上传PDF文件')
    return
  }

  await processSource('pdf', null, selectedFile.value)
}

async function processSource(sourceType, url, file = null) {
  processing.value = true
  progress.value = 0
  statusMessage.value = '正在创建任务...'
  resultTask.value = null

  try {
    let task
    if (sourceType === 'web') {
      task = await taskStore.createTaskFromUrl(url, sourceType)
    } else {
      task = await taskStore.createTaskFromFile(file)
    }

    // Start polling for status
    statusMessage.value = '正在解析内容...'
    progress.value = 10

    await pollTaskStatus(task.id)

  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '处理失败')
    processing.value = false
  }
}

async function pollTaskStatus(taskId) {
  const poll = async () => {
    try {
      const response = await taskStore.pollTaskStatus(taskId, (status) => {
        progress.value = status.progress

        if (status.status === 'processing') {
          if (status.progress < 50) {
            statusMessage.value = '正在解析内容...'
          } else {
            statusMessage.value = '正在生成图片...'
          }
        }

        if (status.status === 'completed') {
          statusMessage.value = '处理完成！'
          progress.value = 100
        }

        if (status.status === 'failed') {
          statusMessage.value = status.error_message || '处理失败'
          ElMessage.error(status.error_message || '处理失败')
        }
      })

      if (response) {
        // Task completed or failed
        if (response.status === 'completed') {
          await refreshTaskDetail(taskId)
        }
        processing.value = false
        return
      }
    } catch (e) {
      processing.value = false
      ElMessage.error('获取状态失败')
    }
  }

  // Start polling every 2 seconds
  const startPoll = () => {
    pollTimer = setTimeout(async () => {
      const done = await poll()
      if (!done) {
        startPoll()
      }
    }, 2000)
  }
  startPoll()
}

async function refreshTaskDetail(taskId) {
  try {
    resultTask.value = await taskStore.fetchTaskDetail(taskId)
  } catch (e) {
    console.error('Failed to refresh task:', e)
  }
}

function switchTheme(theme) {
  selectedTheme.value = theme
}

function getImageTheme(image) {
  return image.theme
}

function downloadImage() {
  if (!currentImage.value) return

  const link = document.createElement('a')
  link.href = currentImage.value
  link.download = `summary-${selectedTheme.value}-${Date.now()}.png`
  link.click()
}

function startNew() {
  taskStore.clearCurrentTask()
  resultTask.value = null
  urlForm.value.url = ''
  selectedFile.value = null
  selectedTheme.value = 'light'
  progress.value = 0
}

function goToHistory() {
  router.push('/history')
}

onUnmounted(() => {
  if (pollTimer) {
    clearTimeout(pollTimer)
  }
})
</script>

<style lang="scss" scoped>
.home-view {
  max-width: 900px;
  margin: 0 auto;
}

.input-card {
  margin-bottom: 24px;

  :deep(.el-card__header) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 20px;

    .card-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 600;
    }
  }
}

.source-tabs {
  padding-top: 16px;

  :deep(.el-tabs__item) {
    font-size: 15px;
  }
}

.status-card {
  margin-bottom: 24px;
  background: #f0f9ff;
  border-color: #bae6fd;

  .processing-status {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 20px 0;

    .loading-spinner {
      font-size: 48px;
      color: #3b82f6;
      animation: spin 1s linear infinite;
    }

    .status-info {
      flex: 1;

      h3 {
        margin: 0 0 8px;
        color: #1e40af;
      }

      p {
        margin: 0 0 12px;
        color: #3b82f6;
        font-size: 14px;
      }
    }
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.theme-card {
  margin-bottom: 24px;

  :deep(.el-card__header) {
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

.theme-options {
  display: flex;
  gap: 24px;
  padding: 16px 0;
}

.theme-option {
  position: relative;
  cursor: pointer;

  .theme-preview {
    width: 200px;
    height: 120px;
    border-radius: 12px;
    border: 2px solid #e2e8f0;
    padding: 12px;
    transition: all 0.3s;

    &.light-preview {
      background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);

      .preview-number {
        color: #3b82f6;
      }
    }

    &.dark-preview {
      background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);

      .preview-number {
        color: #60a5fa;
      }

      .preview-title {
        color: #e2e8f0;
      }
    }

    .preview-number {
      font-size: 32px;
      font-weight: 700;
      display: block;
      margin-bottom: 8px;
    }

    .preview-content {
      .preview-title {
        font-size: 12px;
        display: block;
      }

      .preview-dot {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: currentColor;
        margin-right: 4px;
        margin-top: 4px;
        opacity: 0.5;
      }
    }
  }

  .theme-name {
    display: block;
    text-align: center;
    margin-top: 8px;
    font-size: 14px;
    color: #64748b;
  }

  .check-icon {
    position: absolute;
    top: 8px;
    right: 8px;
    color: #3b82f6;
    background: white;
    border-radius: 50%;
  }

  &:hover .theme-preview {
    border-color: #3b82f6;
    transform: translateY(-2px);
  }

  &.active .theme-preview {
    border-color: #3b82f6;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  }
}

.preview-card {
  margin-bottom: 24px;

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

.preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background: #f1f5f9;
  border-radius: 8px;
  overflow: hidden;

  .preview-image {
    max-width: 100%;
    max-height: 600px;
    object-fit: contain;
  }

  .preview-placeholder {
    text-align: center;
    color: #94a3b8;

    p {
      margin-top: 16px;
    }
  }
}

.image-nav {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.content-card {
  margin-bottom: 24px;

  :deep(.el-card__header) {
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

  .content-preview {
    max-height: 500px;
    overflow-y: auto;

    h3 {
      margin: 0 0 20px;
      color: #1e293b;
      text-align: center;
      padding-bottom: 16px;
      border-bottom: 1px solid #e2e8f0;
    }

    .content-section {
      margin-bottom: 20px;

      h4 {
        margin: 0 0 12px;
        color: #3b82f6;
        font-size: 15px;
      }

      ul {
        margin: 0;
        padding-left: 20px;

        li {
          margin-bottom: 8px;
          color: #475569;
          line-height: 1.6;
        }
      }
    }
  }
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 24px 0;
}

.pdf-uploader {
  :deep(.el-upload) {
    width: 100%;

    .el-upload-dragger {
      width: 100%;
      padding: 40px;
    }
  }
}
</style>
