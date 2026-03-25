<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import './style.css'

interface ServiceStatus {
  is_running: boolean
  port: number
  local_ip: string
  token: string
}

export default {
  name: 'App'
  setup() {
    const status = ref<ServiceStatus>({
      is_running: false,
      port: 12261,
      local_ip: '127.0.0.1',
      token: ''
    })

    const activeTab = ref('monitoring')
    const logs = ref<any[]>(    const logsLoading = ref(false)
    const logsError = ref('')

    const loadStatus = async () => {
      try {
        const statusResult = await invoke<ServiceStatus>('get_service_status')
        status.value = statusResult
      } catch (error) {
        console.error('Failed to load service status:', error)
      }
    }

    const loadLogs = async () => {
      logsLoading.value = true
      try {
        const result = await invoke<any[]>      logs.value = result
      } catch (error) {
        logsError.value = String(error)
      } finally {
        logsLoading.value = false
      }
    }

    const toggleService = async () => {
      if (status.value.is_running) {
        await invoke('stop_service')
      } else {
        await invoke('start_service')
      }
      await loadStatus()
    }

    const copyToken = () => {
      navigator.clipboard.writeText(status.value.token)
    }

    onMounted(() => {
      loadStatus()
      loadLogs()
    })
  })
</script>

<template>
  <div class="app">
    <header class="header">
      <h1>ScreenClaw</h1>
      <div class="tabs">
        <button
          :class="{ active: activeTab === 'monitoring' }"
          @click="activeTab = 'monitoring'"
        >
          {{ $t('app.monitoring') }}
        </button>
        <button
          :class="{ active: activeTab === 'settings' }"
          @click="activeTab = 'settings'"
        >
          {{ $t('app.settings') }}
        </button>
      </div>
    </header>

    <main class="main">
      <div v-if="activeTab === 'monitoring'" class="monitoring-panel">
        <div class="service-status">
          <div class="status-indicator">
            <span class="dot" :class="{ running: status.is_running }"></span>
            <span>{{ status.is_running ? $t('service.running') : $t('service.stopped') }}</span>
          </div </          <div class="addresses">
            <div class="address">
              <span class="label">{{ $t('service.localAddress') }}:</span>
              <span class="value">http://127.0.0.1:{{ status.port }}</            </div>
            <div class="address">
              <span class="label">{{ $t('service.lanAddress') }}:</span>
              <span class="value">http://{{ status.local_ip }}:{{ status.port }}</            </div>
          </div>

          <div class="service-control">
            <button
              class="btn"
              :class="{ btnStop: status.is_running }"
              @click="toggleService"
            >
              {{ status.is_running ? $t('service.stop') : $t('service.start') }}
            </button>
          </div>

          <div class="token-section">
            <span class="label">{{ $t('service.token') }}:</span>
            <div class="token-display">
              <code class="token">{{ status.token }}</code>
              <button class="btn-copy" @click="copyToken">
                {{ $t('common.copy') }}
              </button>
            </div>
          </div>

          <div class="logs-section">
            <div class="logs-header">
              <h3>{{ $t('logs.title') }}</h3>
              <div class="logs-filters">
                <select v-model="filter.aiApp">
                  <option value="">All AI Apps</option>
                </select>
                <select v-model="filter.session">
                  <option value="">All Sessions</option>
                </select>
                <input
                  type="date"
                  v-model="filter.date"
                  :placeholder="Date"
                />
              </div>
              <input
                type="text"
                v-model="searchKeyword"
                :placeholder="Search logs..."
                @input="loadLogs"
              />
            </div>

            <div class="logs-list" v-if="!logsLoading">
              <div
                v-for="log in logs"
                :key="log.timestamp"
                class="log-item"
                @click="showLogDetail(log)"
              >
                <div class="log-time">{{ formatTime(log.timestamp) }}</div>
                <div class="log-process">{{ log.process_name }}</div>
                <div class="log-instruction">{{ log.instruction }}</div>
                <div
                  class="log-result"
                  :class="{ success: log.result.success, error: !log.result.success }"
                >
                  {{ log.result.success ? '✓' : '✗' }}
                </div>
              </div>
            </div>

            <div v-if="logsLoading" class="logs-loading">
              Loading...
            </div>
          </div>
        </div>

        <div v-else class="settings-panel">
          <h2>Settings</h2>
          <p>Settings panel coming soon...</p>
        </div>
      </div>
    </main>
  </div>

  <div v-if="showDetail" class="modal" @click="showDetail = null">
    <div class="modal-content" @click.stop>
      <h3>Log Detail</h3>
      <pre>{{ JSON.stringify(selectedLog, null, 2) }}</pre>
      <button @click="showDetail = false">Close</button>
    </div>
  </div>
</template>

<style scoped>
.app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.tabs {
  display: flex;
  gap: 8px;
}

.tabs button {
  padding: 8px 16px;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.tabs button.active {
  background: white;
  color: #667eea;
}

.tabs button:hover:not(.active) {
  background: rgba(255, 255, 255, 0.3);
}

.main {
  padding: 20px;
}

.service-status {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #ef4444;
}

.dot.running {
  background: #22c55e;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.addresses {
  display: flex;
  gap: 20px;
  flex: 1;
}

.address {
  flex: 1;
}

.address .label {
  font-size: 12px;
  color: #666;
  display: block;
  margin-bottom: 4px;
}

.address .value {
  font-family: monospace;
  font-size: 14px;
  color: #333;
  background: white;
  padding: 8px 12px;
  border-radius: 4px;
}

.service-control {
  margin-left: auto;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-start {
  background: #22c55e;
  color: white;
}

.btn-start:hover {
  background: #16a34a;
}

.btn-stop {
  background: #ef4444;
  color: white;
}

.btn-stop:hover {
  background: #dc2626;
}

.token-section {
  margin-top: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.token-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.token {
  font-family: monospace;
  font-size: 12px;
  background: white;
  padding: 8px 12px;
  border-radius: 4px;
  flex: 1;
  word-break: break-all;
}

.btn-copy {
  padding: 8px 12px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.logs-section {
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-top: 20px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.logs-filters {
  display: flex;
  gap: 12px;
}

.logs-filters select,
.logs-filters input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.logs-list {
  max-height: 400px;
  overflow-y: auto;
}

.log-item {
  display: grid;
  grid-template-columns: 100px 150px 100px 50px;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background 0.2s;
}

.log-item:hover {
  background: #f8f9fa;
}

.log-time {
  font-family: monospace;
  font-size: 12px;
  color: #666;
}

.log-process {
  font-size: 13px;
  color: #333;
}

.log-instruction {
  font-size: 13px;
  font-weight: 500;
}

.log-result {
  text-align: center;
  font-weight: bold;
}

.log-result.success {
  color: #22c55e;
}

.log-result.error {
  color: #ef4444;
}

.logs-loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 1, 1, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  background: white;
  padding: 24px;
  border-radius: 8px;
  max-width: 600px;
  max-height: 80vh;
  overflow: auto;
}

.modal-content pre {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 4px;
  overflow: auto;
  font-size: 12px;
}
</style>
