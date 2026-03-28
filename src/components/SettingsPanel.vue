<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useConfig } from '../composables/useConfig'
import { useService } from '../composables/useService'

const { t, locale } = useI18n()
const { status, regenerateToken } = useService()
const { settingsForm, configSaving, configMessage, saveConfig, resetConfig } = useConfig()

const languageOptions = [
  { value: 'zh_CN', label: '简体中文' },
  { value: 'en_US', label: 'English' }
]

const changeLanguage = (lang: string) => {
  locale.value = lang
  settingsForm.value.language = lang
}
</script>

<template>
  <div class="settings-panel">
    <div class="settings-scroll">
      <h2 class="settings-title">{{ t('settings.title') }}</h2>

      <!-- 界面设置 -->
      <section class="settings-section">
        <h3 class="section-subtitle">{{ t('settings.ui.title') }}</h3>
        <div class="form-group">
          <label class="form-label">
            {{ t('settings.ui.language') }}
            <span class="help-icon" :title="t('settings.ui.languageTip')">?</span>
          </label>
          <select v-model="settingsForm.language" @change="changeLanguage(settingsForm.language)" class="form-select">
            <option v-for="lang in languageOptions" :key="lang.value" :value="lang.value">
              {{ lang.label }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-checkbox">
            <input type="checkbox" v-model="settingsForm.autoStart" />
            <span>
              {{ t('settings.ui.autoStart') }}
              <span class="help-icon help-icon-inline" :title="t('settings.ui.autoStartTip')">?</span>
            </span>
          </label>
        </div>
      </section>

      <!-- 服务配置 -->
      <section class="settings-section">
        <h3 class="section-subtitle">{{ t('settings.server.title') }}</h3>
        <div class="form-group">
          <label class="form-label">
            {{ t('settings.server.port') }}
            <span class="help-icon" :title="t('settings.tooltips.port')">?</span>
          </label>
          <input type="number" v-model.number="settingsForm.port" min="1024" max="65535" class="form-input" />
        </div>
        <div class="form-group">
          <label class="form-label">
            {{ t('settings.server.token') }}
            <span class="help-icon" :title="t('settings.tooltips.token')">?</span>
          </label>
          <div class="token-field">
            <code class="token-preview">{{ status.token }}</code>
            <button class="btn-secondary btn-sm" @click="regenerateToken">
              {{ t('settings.server.regenerate') }}
            </button>
          </div>
        </div>
      </section>

      <!-- 网格默认值 -->
      <section class="settings-section">
        <h3 class="section-subtitle">{{ t('settings.screenshot.gridTitle') }}</h3>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.screenshot.gridDensity') }}
              <span class="help-icon" :title="t('settings.tooltips.gridDensity')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.gridDensity" min="1" max="20" step="0.5" class="form-input" />
          </div>
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.screenshot.gridOpacity') }}
              <span class="help-icon" :title="t('settings.tooltips.gridOpacity')">?</span>
            </label>
            <div class="range-group">
              <input type="range" v-model.number="settingsForm.gridOpacity" min="0" max="100" />
              <span class="range-value">{{ settingsForm.gridOpacity }}%</span>
            </div>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">
            {{ t('settings.screenshot.gridColor') }}
            <span class="help-icon" :title="t('settings.tooltips.gridColor')">?</span>
          </label>
          <input type="color" v-model="settingsForm.gridColor" />
        </div>
      </section>

      <!-- 数字默认值 -->
      <section class="settings-section">
        <h3 class="section-subtitle">{{ t('settings.screenshot.numberTitle') }}</h3>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.screenshot.numberDensity') }}
              <span class="help-icon" :title="t('settings.tooltips.numberDensity')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.numberDensity" min="1" max="10" step="1" class="form-input" />
          </div>
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.screenshot.numberDecimal') }}
              <span class="help-icon" :title="t('settings.tooltips.numberDecimal')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.numberDecimal" min="0" max="4" step="1" class="form-input" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.screenshot.numberSize') }}
              <span class="help-icon" :title="t('settings.tooltips.numberSize')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.numberSize" min="6" max="24" step="1" class="form-input" />
          </div>
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.screenshot.numberOpacity') }}
              <span class="help-icon" :title="t('settings.tooltips.numberOpacity')">?</span>
            </label>
            <div class="range-group">
              <input type="range" v-model.number="settingsForm.numberOpacity" min="0" max="100" />
              <span class="range-value">{{ settingsForm.numberOpacity }}%</span>
            </div>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">
            {{ t('settings.screenshot.numberColor') }}
            <span class="help-icon" :title="t('settings.tooltips.numberColor')">?</span>
          </label>
          <input type="color" v-model="settingsForm.numberColor" />
        </div>
      </section>

      <!-- 图片设置 -->
      <section class="settings-section">
        <h3 class="section-subtitle">{{ t('settings.screenshot.imageTitle') }}</h3>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.screenshot.imageQuality') }}
              <span class="help-icon" :title="t('settings.tooltips.imageQuality')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.imageQuality" min="1" max="100" class="form-input" />
          </div>
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.screenshot.maxImageWidth') }}
              <span class="help-icon" :title="t('settings.tooltips.maxImageWidth')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.maxImageWidth" min="640" max="3840" class="form-input" />
          </div>
        </div>
      </section>

      <!-- 安全设置 -->
      <section class="settings-section">
        <h3 class="section-subtitle">{{ t('settings.security.title') }}</h3>
        <div class="form-group">
          <label class="form-label">
            {{ t('settings.security.autoConfirmProcesses') }} <small class="form-hint">({{ t('common.lineByLine') }})</small>
            <span class="help-icon" :title="t('settings.tooltips.autoConfirmProcesses')">?</span>
          </label>
          <textarea
            v-model="settingsForm.autoConfirmProcesses"
            rows="3"
            class="form-textarea"
            placeholder="notepad.exe&#10;calc.exe"
          ></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">
            {{ t('settings.security.blockedProcesses') }} <small class="form-hint">({{ t('common.lineByLine') }})</small>
            <span class="help-icon" :title="t('settings.tooltips.blockedProcesses')">?</span>
          </label>
          <textarea
            v-model="settingsForm.blockedProcesses"
            rows="3"
            class="form-textarea"
            placeholder="notepad.exe&#10;calc.exe"
          ></textarea>
        </div>
      </section>
    </div>

    <!-- 操作按钮 -->
    <div class="settings-actions">
      <button class="btn-primary" @click="saveConfig" :disabled="configSaving">
        {{ configSaving ? '...' : t('settings.save') }}
      </button>
      <button class="btn-secondary" @click="resetConfig">
        {{ t('settings.reset') }}
      </button>
      <span v-if="configMessage" class="config-message" :class="{ error: configMessage.includes('Error') }">
        {{ configMessage }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.settings-panel {
  display: flex;
  flex-direction: column;
  background: var(--sc-bg-elevated);
  border-radius: var(--sc-radius-xl);
  box-shadow: var(--sc-shadow-md);
  max-width: 800px;
  margin: 0 auto;
  height: calc(100vh - 120px);
  overflow: hidden;
}

.settings-scroll {
  flex: 1;
  overflow-y: auto;
  padding: var(--sc-space-6);
}

.settings-title {
  margin: 0 0 var(--sc-space-6);
  font-size: 20px;
  font-weight: 600;
  color: var(--sc-text-primary);
}

.settings-section {
  margin-bottom: var(--sc-space-6);
  padding-bottom: var(--sc-space-6);
  border-bottom: 1px solid var(--sc-border);
}

.settings-section:last-of-type {
  border-bottom: none;
  margin-bottom: var(--sc-space-4);
}

.section-subtitle {
  margin: 0 0 var(--sc-space-4);
  font-size: 15px;
  font-weight: 600;
  color: var(--sc-text-secondary);
}

.form-group {
  margin-bottom: var(--sc-space-4);
}

.form-label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: var(--sc-space-2);
  font-size: 13px;
  font-weight: 500;
  color: var(--sc-text-secondary);
}

.form-hint {
  font-weight: 400;
  color: var(--sc-text-tertiary);
}

.help-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  font-size: 11px;
  font-weight: 600;
  color: var(--sc-text-tertiary);
  background: var(--sc-bg-secondary);
  border: 1px solid var(--sc-border);
  border-radius: 50%;
  cursor: help;
  flex-shrink: 0;
  position: relative;
}

.help-icon:hover {
  color: var(--sc-text-primary);
  border-color: var(--sc-accent);
  background: var(--sc-bg-tertiary);
}

.help-icon-inline {
  display: inline-flex;
  margin-left: 4px;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: var(--sc-space-3);
  background: var(--sc-bg-primary);
  border: 1px solid var(--sc-border-strong);
  border-radius: var(--sc-radius-sm);
  font-size: 14px;
  color: var(--sc-text-primary);
  transition: all 0.2s ease;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--sc-accent);
  box-shadow: 0 0 0 3px var(--sc-accent-glow);
}

.form-textarea {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  resize: vertical;
  min-height: 100px;
}

.form-checkbox {
  display: flex;
  align-items: center;
  gap: var(--sc-space-2);
  cursor: pointer;
  font-size: 14px;
  color: var(--sc-text-primary);
}

.form-checkbox input {
  margin: 0;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sc-space-5);
}

.range-group {
  display: flex;
  align-items: center;
  gap: var(--sc-space-3);
}

.range-group input[type="range"] {
  flex: 1;
}

.range-value {
  min-width: 45px;
  font-size: 13px;
  color: var(--sc-text-secondary);
}

.token-field {
  display: flex;
  align-items: center;
  gap: var(--sc-space-3);
}

.token-preview {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 12px;
  background: var(--sc-bg-secondary);
  padding: var(--sc-space-3);
  border-radius: var(--sc-radius-sm);
  flex: 1;
  word-break: break-all;
  border: 1px solid var(--sc-border);
}

.btn-sm {
  padding: var(--sc-space-2) var(--sc-space-4);
  font-size: 13px;
}

.btn-secondary {
  padding: var(--sc-space-2) var(--sc-space-4);
  background: var(--sc-bg-secondary);
  border: 1px solid var(--sc-border-strong);
  border-radius: var(--sc-radius-sm);
  color: var(--sc-text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: var(--sc-bg-tertiary);
  border-color: var(--sc-accent);
}

.btn-primary {
  padding: var(--sc-space-3) var(--sc-space-5);
  background: var(--sc-accent);
  border: none;
  border-radius: var(--sc-radius-sm);
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: var(--sc-accent-dark);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.settings-actions {
  display: flex;
  gap: var(--sc-space-3);
  align-items: center;
  padding: var(--sc-space-4) var(--sc-space-6);
  background: var(--sc-bg-elevated);
  border-top: 1px solid var(--sc-border);
  flex-shrink: 0;
}

.config-message {
  font-size: 14px;
  color: var(--sc-success);
}

.config-message.error {
  color: var(--sc-danger);
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
