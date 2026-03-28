<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { LogItem } from '../composables/useLogs'

const { t } = useI18n()

const props = defineProps<{
  visible: boolean
  log: LogItem | null
}>()

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <div v-if="visible" class="modal-overlay" @click="emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>{{ t('logs.viewDetails') }}</h3>
        <button class="btn-icon" @click="emit('close')">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
      <div class="modal-body">
        <pre v-if="log">{{ JSON.stringify(log, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.15s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: var(--sc-bg-elevated);
  border-radius: var(--sc-radius-lg);
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: var(--sc-shadow-lg);
  animation: slideDown 0.2s ease;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--sc-space-4) var(--sc-space-5);
  border-bottom: 1px solid var(--sc-border);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--sc-text-primary);
}

.btn-icon {
  padding: var(--sc-space-2);
  background: transparent;
  border: none;
  border-radius: var(--sc-radius-sm);
  color: var(--sc-text-tertiary);
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

.modal-body {
  padding: var(--sc-space-5);
  overflow: auto;
  max-height: 60vh;
}

.modal-body pre {
  background: var(--sc-log-bg, #1e1e1e);
  color: var(--sc-log-text, #d4d4d4);
  padding: var(--sc-space-4);
  border-radius: var(--sc-radius-sm);
  font-size: 12px;
  overflow: auto;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
