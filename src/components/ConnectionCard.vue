<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useService } from '../composables/useService'

const { t } = useI18n()
const { status, toggleService, copyToken, regenerateToken } = useService()

const collapsed = ref(false)

const emit = defineEmits<{
  openAiIntegrate: []
}>()
</script>

<template>
  <div class="card-section" :class="{ collapsed }">
    <div class="section-header" @click="collapsed = !collapsed">
      <div class="section-title">
        <svg class="collapse-icon" :class="{ rotated: collapsed }" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M6 9l6 6 6-6"/>
        </svg>
        <span>{{ t('service.connectionInfo') }}</span>
      </div>
      <div class="status-badge" :class="status.is_running ? 'running' : 'stopped'">
        <span class="status-dot"></span>
        {{ status.is_running ? t('service.running') : t('service.stopped') }}
      </div>
    </div>

    <div class="section-content connection-content" v-show="!collapsed">
      <div class="connection-grid">
        <div class="connection-item">
          <span class="connection-label">{{ t('service.localAddress') }}</span>
          <code class="connection-value">http://127.0.0.1:{{ status.port }}</code>
        </div>
        <div class="connection-item">
          <span class="connection-label">{{ t('service.lanAddress') }}</span>
          <code class="connection-value">http://{{ status.local_ip }}:{{ status.port }}</code>
        </div>
        <div class="connection-item token-item">
          <span class="connection-label">{{ t('service.token') }}</span>
          <div class="token-row">
            <code class="token-value">{{ status.token }}</code>
            <button class="btn-icon" @click.stop="copyToken" :title="t('common.copy')">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
            </button>
            <button class="btn-icon btn-icon-accent" @click.stop="regenerateToken" :title="t('settings.server.regenerate')">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 2v6h-6"></path>
                <path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path>
                <path d="M3 22v-6h6"></path>
                <path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div class="service-control">
        <button class="btn-ai-integrate" @click="emit('openAiIntegrate')">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
            <path d="M2 17l10 5 10-5"></path>
            <path d="M2 12l10 5 10-5"></path>
          </svg>
          {{ t('aiIntegrate.button') }}
        </button>
        <button
          class="btn-service"
          :class="status.is_running ? 'btn-stop' : 'btn-start'"
          @click="toggleService"
        >
          {{ status.is_running ? t('service.stop') : t('service.start') }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card-section {
  background: var(--sc-bg-elevated);
  border-radius: var(--sc-radius-lg);
  box-shadow: var(--sc-shadow-sm);
  overflow: hidden;
  flex-shrink: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--sc-space-4) var(--sc-space-5);
  cursor: pointer;
  background: var(--sc-bg-secondary);
  transition: background 0.2s;
  user-select: none;
}

.section-header:hover {
  background: var(--sc-bg-tertiary);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--sc-space-2);
  font-weight: 600;
  color: var(--sc-text-primary);
  font-size: 14px;
}

.collapse-icon {
  transition: transform 0.2s ease;
  color: var(--sc-text-tertiary);
}

.collapse-icon.rotated {
  transform: rotate(-90deg);
}

.status-badge {
  display: flex;
  align-items: center;
  gap: var(--sc-space-2);
  padding: var(--sc-space-1) var(--sc-space-3);
  border-radius: var(--sc-radius-full);
  font-size: 13px;
  font-weight: 500;
}

.status-badge.running {
  background: rgba(5, 150, 105, 0.1);
  color: var(--sc-success);
}

.status-badge.stopped {
  background: rgba(220, 38, 38, 0.1);
  color: var(--sc-danger);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.status-badge.running .status-dot {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.connection-content {
  padding: var(--sc-space-5);
  animation: slideDown 0.2s ease;
}

.connection-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sc-space-4);
  margin-bottom: var(--sc-space-4);
}

.connection-item {
  display: flex;
  flex-direction: column;
  gap: var(--sc-space-1);
}

.connection-label {
  font-size: 12px;
  color: var(--sc-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.connection-value {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 14px;
  color: var(--sc-text-primary);
  background: var(--sc-bg-secondary);
  padding: var(--sc-space-2) var(--sc-space-3);
  border-radius: var(--sc-radius-sm);
}

.token-item {
  grid-column: 1 / -1;
}

.token-row {
  display: flex;
  align-items: center;
  gap: var(--sc-space-2);
}

.token-value {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 12px;
  color: var(--sc-text-primary);
  background: var(--sc-bg-secondary);
  padding: var(--sc-space-2) var(--sc-space-3);
  border-radius: var(--sc-radius-sm);
  flex: 1;
  word-break: break-all;
}

.btn-icon {
  padding: var(--sc-space-2);
  background: transparent;
  border: 1px solid var(--sc-border-strong);
  border-radius: var(--sc-radius-sm);
  color: var(--sc-text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-icon:hover {
  background: var(--sc-bg-secondary);
  color: var(--sc-text-primary);
}

.btn-icon-accent:hover {
  background: var(--sc-accent-glow);
  border-color: var(--sc-accent);
  color: var(--sc-accent);
}

.service-control {
  display: flex;
  justify-content: flex-end;
  gap: var(--sc-space-3);
}

.btn-ai-integrate {
  display: flex;
  align-items: center;
  gap: var(--sc-space-2);
  padding: var(--sc-space-2) var(--sc-space-4);
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: var(--sc-radius-md);
  color: #e5e5e5;
  font-weight: 500;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-ai-integrate:hover {
  background: #2a2a2a;
  border-color: #444;
}

.btn-service {
  padding: var(--sc-space-3) var(--sc-space-6);
  border: none;
  border-radius: var(--sc-radius-md);
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-start {
  background: var(--sc-success);
  color: white;
}

.btn-start:hover {
  background: #047857;
  transform: translateY(-1px);
}

.btn-stop {
  background: var(--sc-danger);
  color: white;
}

.btn-stop:hover {
  background: #b91c1c;
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .connection-grid {
    grid-template-columns: 1fr;
  }
}
</style>
