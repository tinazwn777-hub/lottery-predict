<template>
  <el-config-provider :locale="locale">
    <div class="app-container">
      <header class="app-header">
        <div class="header-content">
          <h1 class="app-title">
            <el-icon><Picture /></el-icon>
            课程总结图片生成器
          </h1>
          <p class="app-desc">将学习内容自动生成美观的总结卡片</p>
        </div>
      </header>

      <main class="app-main">
        <router-view />
      </main>

      <footer class="app-footer">
        <p>Powered by Claude Code & FastAPI + Vue 3</p>
      </footer>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref } from 'vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

const locale = ref(zhCn)
</script>

<style lang="scss">
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.app-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 20px 0;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);

  .header-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    text-align: center;
  }

  .app-title {
    font-size: 28px;
    font-weight: 700;
    color: #1f2937;
    margin: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;

    svg {
      width: 32px;
      height: 32px;
    }
  }

  .app-desc {
    color: #6b7280;
    margin: 8px 0 0;
    font-size: 14px;
  }
}

.app-main {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 30px 20px;
}

.app-footer {
  text-align: center;
  padding: 20px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
}
</style>
