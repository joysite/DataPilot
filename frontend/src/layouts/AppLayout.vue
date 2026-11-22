
<script setup lang="ts">
import logo from '../assets/datapilot-logo.svg'

const navigationItems = [
  { label: '概览', path: '/', icon: 'grid' },
  { label: 'Agent 对话', path: '/agent', icon: 'message' },
  { label: '数据管理', path: '/data-management', icon: 'database' },
  { label: '业务分析', path: '/analytics', icon: 'chart' },
  { label: '异常检测', path: '/anomalies', icon: 'anomaly' },
]
</script>

<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="brand">
        <img :src="logo" alt="DataPilot Logo" class="brand-logo" />
        <div class="brand-info">
          <span class="brand-name">DataPilot</span>
          <span class="brand-subtitle">Business Intelligence</span>
        </div>
      </div>

      <div class="nav-section">
        <span class="nav-heading">工作台</span>

        <nav class="nav-list">
          <RouterLink
            v-for="item in navigationItems"
            :key="item.path"
            :to="item.path"
            class="nav-item"
            active-class="active"
          >
            <span class="nav-icon">
              {{
                item.icon === 'grid'
                  ? '▦'
                  : item.icon === 'message'
                    ? '✉'
                    : item.icon === 'chart'
                      ? '▥'
                      : item.icon === 'anomaly'
                        ? '⌁'
                        : '▤'
              }}
            </span>
            <span>{{ item.label }}</span>
          </RouterLink>
        </nav>
      </div>

      <div class="sidebar-footer">
        <span class="status-dot"></span>
        <span>本地分析环境</span>
      </div>
    </aside>

    <div class="main-area">
      <header class="topbar">
        <div class="topbar-title">DataPilot 智能分析平台</div>
        <div class="topbar-right">
          <span class="environment-label">Local Workspace</span>
        </div>
      </header>

      <main class="page-content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  width: 100%;
  min-height: 100vh;
}

.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 10;
  display: flex;
  width: 248px;
  flex-direction: column;
  padding: 24px 16px 18px;
  background: var(--color-sidebar);
  color: #fff;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 10px 30px;
}

.brand-logo {
  width: 42px;
  height: 42px;
  object-fit: contain;
}

.brand-info {
  display: flex;
  flex-direction: column;
}

.brand-name {
  color: #fff;
  font-size: 19px;
  font-weight: 700;
  letter-spacing: 0.2px;
}

.brand-subtitle {
  margin-top: 2px;
  color: var(--color-sidebar-text);
  font-size: 10px;
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.nav-heading {
  padding: 0 12px;
  color: #8190a8;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1px;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 13px;
  border-radius: var(--radius-md);
  color: var(--color-sidebar-text);
  font-size: 13px;
  transition: background 0.2s, color 0.2s;
}

.nav-item:hover,
.nav-item.active {
  background: var(--color-sidebar-hover);
  color: #fff;
}

.nav-item.active {
  box-shadow: inset 3px 0 #60a5fa;
}

.nav-icon {
  width: 18px;
  text-align: center;
  font-size: 17px;
}

.sidebar-footer {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-top: auto;
  padding: 14px 12px 4px;
  border-top: 1px solid rgb(255 255 255 / 10%);
  color: var(--color-sidebar-text);
  font-size: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
}

.main-area {
  display: flex;
  min-width: 0;
  min-height: 100vh;
  flex: 1;
  flex-direction: column;
  margin-left: 248px;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  min-height: 64px;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  border-bottom: 1px solid var(--color-border);
  background: rgb(255 255 255 / 95%);
}

.topbar-title {
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
}

.environment-label {
  padding: 5px 10px;
  border-radius: 20px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-size: 11px;
}

.page-content {
  width: 100%;
  max-width: 1600px;
  flex: 1;
  margin: 0 auto;
  padding: 30px 32px;
}

@media (max-width: 768px) {
  .sidebar {
    width: 68px;
    align-items: center;
    padding: 18px 8px;
  }

  .brand {
    padding: 0 0 28px;
  }

  .brand-info,
  .nav-heading,
  .nav-item > span:last-child,
  .sidebar-footer > span:last-child {
    display: none;
  }

  .nav-item {
    justify-content: center;
    padding: 12px;
  }

  .main-area {
    margin-left: 68px;
  }

  .topbar {
    padding: 0 16px;
  }

  .page-content {
    padding: 22px 16px;
  }
}
</style>
