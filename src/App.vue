<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { invoke } from '@tauri-apps/api/core'
import { useService } from './composables/useService'
import { useConfig } from './composables/useConfig'
import { useLogs } from './composables/useLogs'
import ConnectionCard from './components/ConnectionCard.vue'
import LogsPanel from './components/LogsPanel.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import AiIntegrateModal from './components/AiIntegrateModal.vue'
import LogDetailModal from './components/LogDetailModal.vue'
import type { LogItem } from './composables/useLogs'

const { t } = useI18n()
const { loadStatus } = useService()
const { config, loadConfig } = useConfig()
const { loadLogs } = useLogs()

const appRoot = ref('')

const activeTab = ref('monitoring')
const showAiIntegrate = ref(false)
const showLogDetail = ref(false)
const selectedLog = ref<LogItem | null>(null)

const viewLogDetail = (log: LogItem) => {
  selectedLog.value = log
  showLogDetail.value = true
}

onMounted(async () => {
  // 并行加载，不互相阻塞
  Promise.all([loadStatus(), loadConfig(), loadLogs()])

  // 获取应用根目录
  try {
    appRoot.value = await invoke<string>('get_app_root')
  } catch (e) {
    console.error('Failed to get app root:', e)
  }

  // Python 服务启动后会更新局域网 IP，5 秒后刷新并标记就绪
  setTimeout(() => {
    loadStatus(true)
  }, 5000)
})
</script>

<template>
  <div class="app">
    <!-- Header -->
    <header class="header">
      <h1 class="header-title">{{ t('app.title') }}</h1>
      <div class="tabs">
        <button
          :class="['tab-btn', { active: activeTab === 'monitoring' }]"
          @click="activeTab = 'monitoring'"
        >
          {{ t('app.monitoring') }}
        </button>
        <button
          :class="['tab-btn', { active: activeTab === 'settings' }]"
          @click="activeTab = 'settings'"
        >
          {{ t('app.settings') }}
        </button>
      </div>
    </header>

    <main class="main">
      <!-- 监控面板 -->
      <div v-if="activeTab === 'monitoring'" class="monitoring-panel">
        <ConnectionCard @open-ai-integrate="showAiIntegrate = true" />
        <LogsPanel @view-detail="viewLogDetail" />
      </div>

      <!-- 设置面板 -->
      <SettingsPanel v-else />
    </main>

    <!-- AI集成弹窗 -->
    <AiIntegrateModal
      :visible="showAiIntegrate"
      :config="config"
      :app-root="appRoot"
      @close="showAiIntegrate = false"
    />

    <!-- 日志详情弹窗 -->
    <LogDetailModal
      :visible="showLogDetail"
      :log="selectedLog"
      @close="showLogDetail = false"
    />
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  background: var(--sc-bg-primary);
  display: flex;
  flex-direction: column;
}

/* Header */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--sc-space-4) var(--sc-space-6);
  background: var(--sc-bg-primary);
  border-bottom: 1px solid var(--sc-border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.5px;
  color: var(--sc-text-primary);
}

.tabs {
  display: flex;
  gap: var(--sc-space-2);
}

.tab-btn {
  padding: var(--sc-space-2) var(--sc-space-4);
  border: none;
  background: transparent;
  color: var(--sc-text-tertiary);
  border-radius: var(--sc-radius-sm);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  background: var(--sc-bg-secondary);
  color: var(--sc-text-primary);
}

.tab-btn.active {
  background: var(--sc-text-primary);
  color: var(--sc-bg-primary);
}

/* Main */
.main {
  flex: 1;
  padding: var(--sc-space-6);
  overflow: auto;
}

/* 监控面板 */
.monitoring-panel {
  display: flex;
  flex-direction: column;
  gap: var(--sc-space-4);
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    gap: var(--sc-space-3);
    padding: var(--sc-space-4);
  }
}
</style>
