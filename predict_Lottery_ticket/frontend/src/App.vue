<template>
  <div class="app-container">
    <!-- macOS 风格顶部导航栏 -->
    <header class="mac-header">
      <div class="mac-header-left">
        <div class="app-icon">
          <svg viewBox="0 0 24 24" fill="none" width="20" height="20">
            <circle cx="12" cy="12" r="10" fill="#007AFF"/>
            <circle cx="8" cy="10" r="2" fill="white"/>
            <circle cx="16" cy="10" r="2" fill="white"/>
            <path d="M8 14 Q12 18 16 14" stroke="white" stroke-width="2" fill="none"/>
          </svg>
        </div>
        <span class="app-title">彩票预测</span>
      </div>

      <nav class="mac-nav">
        <router-link to="/" class="mac-nav-item" :class="{ active: $route.path === '/' }">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
            <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
          </svg>
          首页
        </router-link>
        <router-link to="/predict" class="mac-nav-item" :class="{ active: $route.path === '/predict' }">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
          </svg>
          预测
        </router-link>
        <router-link to="/analysis" class="mac-nav-item" :class="{ active: $route.path === '/analysis' }">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
          </svg>
          分析
        </router-link>
        <router-link to="/verify" class="mac-nav-item" :class="{ active: $route.path === '/verify' }">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
          </svg>
          验证
        </router-link>
      </nav>

      <div class="mac-header-right">
        <div class="window-controls">
          <div class="window-btn close" @click="handleClose"></div>
          <div class="window-btn minimize" @click="handleMinimize"></div>
          <div class="window-btn maximize" @click="handleMaximize"></div>
        </div>
      </div>
    </header>

    <!-- 主要内容区 -->
    <main class="mac-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 底部提示 -->
    <footer class="mac-footer">
      <p>本系统仅供学习研究娱乐使用，不构成任何投注建议</p>
      <p>彩票开奖是完全随机的概率事件，请理性购彩</p>
    </footer>
  </div>
</template>

<script setup>
const handleClose = () => {
  // 可以添加关闭确认
}

const handleMinimize = () => {
  // 最小化逻辑
}

const handleMaximize = () => {
  // 最大化逻辑
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* macOS 风格顶部导航 */
.mac-header {
  height: 52px;
  background: rgba(30, 30, 30, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  position: sticky;
  top: 0;
  z-index: 1000;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.mac-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.app-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-title {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

/* 导航栏 */
.mac-nav {
  display: flex;
  gap: 4px;
  background: rgba(255, 255, 255, 0.1);
  padding: 4px;
  border-radius: 8px;
}

.mac-nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.mac-nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.mac-nav-item.active {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.mac-header-right {
  display: flex;
  align-items: center;
}

/* macOS 窗口按钮 */
.window-controls {
  display: flex;
  gap: 8px;
}

.window-btn {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  cursor: pointer;
  transition: opacity 0.2s;
}

.window-btn:hover {
  opacity: 0.8;
}

.window-btn.close {
  background: #ff5f57;
}

.window-btn.minimize {
  background: #febc2e;
}

.window-btn.maximize {
  background: #28c840;
}

/* 主要内容区 */
.mac-main {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 30px 20px;
}

/* 底部 */
.mac-footer {
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
  padding: 16px;
  font-size: 12px;
}

.mac-footer p {
  margin: 4px 0;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
