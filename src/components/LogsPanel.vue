<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useLogs } from '../composables/useLogs'
import type { LogItem } from '../composables/useLogs'

const { t } = useI18n()
const {
  logs,
  logsLoading,
  filter,
  searchKeyword,
  uniqueAiApps,
  uniqueTargetApps,
  filteredLogs,
  clearFilters,
  translateInstruction,
  formatTime
} = useLogs()

const collapsed = ref(false)

const emit = defineEmits<{
  viewDetail: [log: LogItem]
}>()
</script>

<template>
  <div class="card-section logs-section" :class="{ collapsed }">
    <div class="section-header" @click="collapsed = !collapsed">
      <div class="section-title">
        <svg class="collapse-icon" :class="{ rotated: collapsed }" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M6 9l6 6 6-6"/>
        </svg>
        <span>{{ t('logs.title') }}</span>
      </div>
      <div class="logs-count" v-if="filteredLogs.length !== logs.length">
        {{ t('logs.showing') }} {{ filteredLogs.length }} / {{ logs.length }}
      </div>
    </div>

    <div class="section-content logs-content" v-show="!collapsed">
      <!-- 筛选器 -->
      <div class="logs-filters">
        <div class="filter-group">
          <label class="filter-label">{{ t('logs.aiApp') }}</label>
          <select v-model="filter.aiApp" class="filter-select">
            <option value="">{{ t('logs.allApps') }}</option>
            <option v-for="name in uniqueAiApps" :key="name" :value="name">
              {{ name }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label class="filter-label">{{ t('logs.targetApp') }}</label>
          <select v-model="filter.targetApp" class="filter-select">
            <option value="">{{ t('logs.allApps') }}</option>
            <option v-for="name in uniqueTargetApps" :key="name" :value="name">
              {{ name }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label class="filter-label">{{ t('logs.sessionId') }}</label>
          <input
            type="text"
            v-model="filter.session"
            class="filter-input"
            :placeholder="t('logs.sessionPlaceholder')"
          />
        </div>

        <div class="filter-group">
          <label class="filter-label">{{ t('logs.date') }}</label>
          <div class="date-picker-wrapper">
            <input type="date" v-model="filter.date" class="filter-date" :class="{ 'has-value': filter.date }" />
            <span class="date-placeholder" v-show="!filter.date">{{ t('logs.allDates') }}</span>
            <svg class="date-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
            </svg>
          </div>
        </div>

        <button class="btn-clear-filter" @click="clearFilters" v-if="filter.aiApp || filter.targetApp || filter.session || filter.date">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
          {{ t('logs.clearFilter') }}
        </button>
      </div>

      <!-- 搜索框 -->
      <div class="logs-search">
        <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <input
          type="text"
          v-model="searchKeyword"
          :placeholder="t('logs.searchPlaceholder')"
          class="search-input"
        />
      </div>

      <!-- 日志列表 -->
      <div class="logs-list" v-if="!logsLoading && filteredLogs.length">
        <div
          v-for="log in filteredLogs"
          :key="log.timestamp"
          class="log-item"
          @click="emit('viewDetail', log)"
        >
          <div class="log-time">{{ formatTime(log.timestamp) }}</div>
          <div class="log-process">{{ log.process_name }}</div>
          <div class="log-instruction">{{ translateInstruction(log.instruction) }}</div>
          <div class="log-result" :class="{ success: log.result.success, error: !log.result.success }">
            {{ log.result.success ? '✓' : '✗' }}
          </div>
        </div>
      </div>

      <div v-if="logsLoading" class="logs-empty">
        <div class="loading-spinner"></div>
        <span>{{ t('logs.loading') }}</span>
      </div>

      <div v-if="!logsLoading && !filteredLogs.length" class="logs-empty">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="16" y1="13" x2="8" y2="13"></line>
          <line x1="16" y1="17" x2="8" y2="17"></line>
          <polyline points="10 9 9 9 8 9"></polyline>
        </svg>
        <span>{{ filteredLogs.length ? t('logs.noMatch') : t('logs.empty') }}</span>
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

.logs-count {
  font-size: 12px;
  color: var(--sc-text-tertiary);
  background: var(--sc-bg-tertiary);
  padding: 2px 8px;
  border-radius: var(--sc-radius-full);
}

.logs-content {
  display: flex;
  flex-direction: column;
  max-height: 500px;
}

.logs-filters {
  display: flex;
  gap: var(--sc-space-3);
  padding: var(--sc-space-3) var(--sc-space-5);
  background: var(--sc-bg-secondary);
  border-bottom: 1px solid var(--sc-border);
  flex-shrink: 0;
  flex-wrap: wrap;
  align-items: flex-end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--sc-space-1);
  min-width: 140px;
}

.filter-label {
  font-size: 11px;
  color: var(--sc-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.filter-select,
.filter-input,
.filter-date {
  background: var(--sc-bg-elevated);
  border: 1px solid var(--sc-border-strong);
  border-radius: 6px;
  padding: var(--sc-space-2) var(--sc-space-3);
  font-size: 13px;
  color: var(--sc-text-primary);
  min-width: 120px;
}

.filter-select:focus,
.filter-input:focus,
.filter-date:focus {
  outline: none;
  border-color: var(--sc-accent);
  box-shadow: 0 0 0 2px var(--sc-accent-glow);
}

.filter-select {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23737373' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  padding-right: 28px;
}

.filter-input::placeholder {
  color: var(--sc-text-muted);
}

.date-picker-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.date-picker-wrapper .filter-date {
  padding-right: 32px;
  width: 100%;
  cursor: pointer;
}

.filter-date::-webkit-datetime-edit {
  visibility: hidden;
}

.filter-date.has-value::-webkit-datetime-edit {
  visibility: visible;
}

.date-picker-wrapper .date-icon {
  position: absolute;
  right: 8px;
  pointer-events: none;
  color: var(--sc-text-tertiary);
}

.filter-date::-webkit-calendar-picker-indicator {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  cursor: pointer;
  opacity: 0;
}

.date-placeholder {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--sc-text-muted);
  font-size: 13px;
  pointer-events: none;
  background: var(--sc-bg-elevated);
  padding: 2px 4px;
}

.btn-clear-filter {
  display: flex;
  align-items: center;
  gap: var(--sc-space-1);
  padding: var(--sc-space-2) var(--sc-space-3);
  background: transparent;
  border: 1px solid var(--sc-border-strong);
  border-radius: 6px;
  color: var(--sc-text-secondary);
  font-size: 12px;
  cursor: pointer;
  margin-top: auto;
  transition: all 0.2s;
}

.btn-clear-filter:hover {
  background: var(--sc-bg-tertiary);
  border-color: var(--sc-danger);
  color: var(--sc-danger);
}

.logs-search {
  display: flex;
  align-items: center;
  padding: var(--sc-space-2) var(--sc-space-5);
  background: var(--sc-bg-secondary);
  border-bottom: 1px solid var(--sc-border);
  flex-shrink: 0;
}

.search-icon {
  color: var(--sc-text-tertiary);
  margin-right: var(--sc-space-2);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: var(--sc-bg-elevated);
  border: 1px solid var(--sc-border-strong);
  border-radius: 6px;
  padding: var(--sc-space-2) var(--sc-space-3);
  font-size: 13px;
  color: var(--sc-text-primary);
}

.search-input:focus {
  outline: none;
  border-color: var(--sc-accent);
  box-shadow: 0 0 0 2px var(--sc-accent-glow);
}

.search-input::placeholder {
  color: var(--sc-text-muted);
}

.logs-list {
  flex: 1;
  overflow-y: auto;
  padding: 0;
  min-height: 0;
}

.log-item {
  display: grid;
  grid-template-columns: 90px 140px 1fr 40px;
  gap: var(--sc-space-3);
  padding: var(--sc-space-3) var(--sc-space-5);
  border-bottom: 1px solid var(--sc-border);
  cursor: pointer;
  transition: background 0.15s;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 13px;
}

.log-item:hover {
  background: var(--sc-bg-secondary);
}

.log-time {
  color: var(--sc-text-tertiary);
  font-size: 12px;
}

.log-process {
  color: var(--sc-accent-dark);
  font-weight: 500;
}

.log-instruction {
  color: var(--sc-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-result {
  text-align: center;
  font-weight: bold;
}

.log-result.success {
  color: var(--sc-success);
}

.log-result.error {
  color: var(--sc-danger);
}

.logs-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sc-space-4);
  padding: var(--sc-space-8);
  color: var(--sc-text-tertiary);
  font-size: 14px;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--sc-border);
  border-top-color: var(--sc-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .logs-filters {
    flex-direction: column;
  }

  .filter-group {
    min-width: 100%;
  }

  .log-item {
    grid-template-columns: 1fr;
    gap: var(--sc-space-1);
  }
}
</style>
