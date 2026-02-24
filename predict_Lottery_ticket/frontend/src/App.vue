<template>
  <div class="app-container">
    <header class="header">
      <div class="header-content">
        <h1 class="logo" @click="$router.push('/')">
          <span class="icon">🎯</span>
          彩票预测系统
        </h1>
        <nav class="nav">
          <router-link to="/" class="nav-item">首页</router-link>
          <router-link to="/predict" class="nav-item">预测</router-link>
          <router-link to="/analysis" class="nav-item">数据分析</router-link>
          <router-link to="/verify" class="nav-item">验证</router-link>
        </nav>
      </div>
    </header>

    <main class="main">
      <router-view />
    </main>

    <footer class="footer">
      <p>本系统仅供学习研究娱乐使用，不构成任何投注建议</p>
      <p>彩票开奖是完全随机的概率事件，请理性购彩</p>
    </footer>
  </div>
</template>

<script setup>
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  font-size: 22px;
  font-weight: 700;
  color: #667eea;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo .icon {
  font-size: 28px;
}

.nav {
  display: flex;
  gap: 8px;
}

.nav-item {
  padding: 8px 20px;
  border-radius: 20px;
  text-decoration: none;
  color: #333;
  font-weight: 500;
  transition: all 0.3s;
}

.nav-item:hover {
  background: #f0f0f0;
}

.nav-item.router-link-active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.main {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 30px 20px;
}

.footer {
  background: rgba(0, 0, 0, 0.3);
  color: rgba(255, 255, 255, 0.8);
  text-align: center;
  padding: 20px;
  font-size: 14px;
}

.footer p {
  margin: 5px 0;
}
</style>
