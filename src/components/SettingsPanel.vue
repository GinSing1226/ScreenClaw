<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useConfig } from '../composables/useConfig'
import { useService } from '../composables/useService'

const { t, locale } = useI18n()
const { status, regenerateToken } = useService()
const { settingsForm, configSaving, configMessage, saveConfig, resetConfig } = useConfig()

type SectionKey =
  | 'ui'
  | 'server'
  | 'grid'
  | 'number'
  | 'image'
  | 'marker'
  | 'crop'
  | 'scroll'
  | 'selfCheck'
  | 'delegated'
  | 'recording'
  | 'security'

const collapsedSections = ref<Record<SectionKey, boolean>>({
  ui: true,
  server: false,
  grid: false,
  number: true,
  image: true,
  marker: true,
  crop: true,
  scroll: true,
  selfCheck: true,
  delegated: true,
  recording: true,
  security: true
})

const toggleSection = (key: SectionKey) => {
  collapsedSections.value[key] = !collapsedSections.value[key]
}

const sectionSummary = computed<Record<SectionKey, string>>(() => ({
  ui: `${settingsForm.value.language}${settingsForm.value.autoStart ? ` / ${t('settings.ui.autoStart')}` : ''}`,
  server: `${settingsForm.value.port}`,
  grid: `${settingsForm.value.colorMode}, ${settingsForm.value.gridDensity}%, ${settingsForm.value.gridOpacity}%`,
  number: `${settingsForm.value.numberSize}px, ${settingsForm.value.numberDensity}x, ${settingsForm.value.numberStrokeWidth}px`,
  image: `${settingsForm.value.imageQuality}%, ${settingsForm.value.maxImageWidth}px`,
  marker: `ring ${settingsForm.value.markerRingRadius}px, dot ${settingsForm.value.markerDotRadius}px`,
  crop: `${settingsForm.value.cropZoomScale}x`,
  scroll: `${settingsForm.value.maxScrolls}, ${settingsForm.value.defaultScrollPercent}`,
  selfCheck: `${settingsForm.value.selfCheckEnabled ? t('common.enabled') : t('common.disabled')}, ${settingsForm.value.selfCheckInterval}, ${settingsForm.value.selfCheckMinChars}`,
  delegated: settingsForm.value.exitHotkey,
  recording: `${settingsForm.value.recordingHotkey}, ${settingsForm.value.recordingScrollMergeInterval}ms`,
  security: `${settingsForm.value.autoConfirmProcesses.split('\n').filter(Boolean).length}/${settingsForm.value.blockedProcesses.split('\n').filter(Boolean).length}`
}))

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
        <button class="section-header" type="button" @click="toggleSection('ui')">
          <span class="section-title">{{ t('settings.ui.title') }}</span>
          <span class="section-summary">{{ sectionSummary.ui }}</span>
          <span class="collapse-icon" :class="{ rotated: !collapsedSections.ui }">›</span>
        </button>
        <div class="section-content" v-show="!collapsedSections.ui">
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
        </div>
      </section>

      <!-- 服务配置 -->
      <section class="settings-section">
        <button class="section-header" type="button" @click="toggleSection('server')">
          <span class="section-title">{{ t('settings.server.title') }}</span>
          <span class="section-summary">{{ sectionSummary.server }}</span>
          <span class="collapse-icon" :class="{ rotated: !collapsedSections.server }">›</span>
        </button>
        <div class="section-content" v-show="!collapsedSections.server">
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
        </div>
      </section>

      <!-- 网格默认值 -->
      <section class="settings-section">
        <button class="section-header" type="button" @click="toggleSection('grid')">
          <span class="section-title">{{ t('settings.screenshot.gridTitle') }}</span>
          <span class="section-summary">{{ sectionSummary.grid }}</span>
          <span class="collapse-icon" :class="{ rotated: !collapsedSections.grid }">›</span>
        </button>
        <div class="section-content" v-show="!collapsedSections.grid">
        <div class="form-group">
          <label class="form-label">
            {{ t('settings.screenshot.colorMode') }}
            <span class="help-icon" :title="t('settings.tooltips.colorMode')">?</span>
          </label>
          <select v-model="settingsForm.colorMode" class="form-select">
            <option value="grayscale">{{ t('settings.screenshot.colorMode') === '颜色模式' ? '灰度' : 'Grayscale' }}</option>
            <option value="color">{{ t('settings.screenshot.colorMode') === '颜色模式' ? '彩色' : 'Color' }}</option>
          </select>
        </div>
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
        </div>
      </section>

      <!-- 数字默认值 -->
      <section class="settings-section">
        <button class="section-header" type="button" @click="toggleSection('number')">
          <span class="section-title">{{ t('settings.screenshot.numberTitle') }}</span>
          <span class="section-summary">{{ sectionSummary.number }}</span>
          <span class="collapse-icon" :class="{ rotated: !collapsedSections.number }">›</span>
        </button>
        <div class="section-content" v-show="!collapsedSections.number">
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
            <input type="number" v-model.number="settingsForm.numberSize" min="6" max="64" step="1" class="form-input" />
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
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.screenshot.numberStrokeWidth') }}
              <span class="help-icon" :title="t('settings.tooltips.numberStrokeWidth')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.numberStrokeWidth" min="0" max="8" step="1" class="form-input" />
          </div>
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.screenshot.numberStrokeColor') }}
              <span class="help-icon" :title="t('settings.tooltips.numberStrokeColor')">?</span>
            </label>
            <input type="color" v-model="settingsForm.numberStrokeColor" />
          </div>
        </div>
        </div>
      </section>

      <!-- 图片设置 -->
      <section class="settings-section">
        <button class="section-header" type="button" @click="toggleSection('image')">
          <span class="section-title">{{ t('settings.screenshot.imageTitle') }}</span>
          <span class="section-summary">{{ sectionSummary.image }}</span>
          <span class="collapse-icon" :class="{ rotated: !collapsedSections.image }">›</span>
        </button>
        <div class="section-content" v-show="!collapsedSections.image">
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
        </div>
      </section>

      <!-- 坐标标记点 -->
      <section class="settings-section">
        <button class="section-header" type="button" @click="toggleSection('marker')">
          <span class="section-title">{{ t('settings.screenshot.markerTitle') }}</span>
          <span class="section-summary">{{ sectionSummary.marker }}</span>
          <span class="collapse-icon" :class="{ rotated: !collapsedSections.marker }">›</span>
        </button>
        <div class="section-content" v-show="!collapsedSections.marker">
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.screenshot.markerRingRadius') }}
              <span class="help-icon" :title="t('settings.tooltips.markerRingRadius')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.markerRingRadius" min="4" max="64" step="1" class="form-input" />
          </div>
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.screenshot.markerRingLineWidth') }}
              <span class="help-icon" :title="t('settings.tooltips.markerRingLineWidth')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.markerRingLineWidth" min="1" max="8" step="1" class="form-input" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.screenshot.markerRingColor') }}
              <span class="help-icon" :title="t('settings.tooltips.markerRingColor')">?</span>
            </label>
            <input type="color" v-model="settingsForm.markerRingColor" />
          </div>
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.screenshot.markerDotRadius') }}
              <span class="help-icon" :title="t('settings.tooltips.markerDotRadius')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.markerDotRadius" min="1" max="16" step="1" class="form-input" />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">
            {{ t('settings.screenshot.markerDotColor') }}
            <span class="help-icon" :title="t('settings.tooltips.markerDotColor')">?</span>
          </label>
          <input type="color" v-model="settingsForm.markerDotColor" />
        </div>
        </div>
      </section>

      <!-- 裁剪放大 -->
      <section class="settings-section">
        <button class="section-header" type="button" @click="toggleSection('crop')">
          <span class="section-title">{{ t('settings.screenshot.cropZoomTitle') }}</span>
          <span class="section-summary">{{ sectionSummary.crop }}</span>
          <span class="collapse-icon" :class="{ rotated: !collapsedSections.crop }">›</span>
        </button>
        <div class="section-content" v-show="!collapsedSections.crop">
        <div class="form-group">
          <label class="form-label">
            {{ t('settings.screenshot.cropZoomScale') }}
            <span class="help-icon" :title="t('settings.tooltips.cropZoomScale')">?</span>
          </label>
          <input type="number" v-model.number="settingsForm.cropZoomScale" min="1.0" max="10.0" step="0.5" class="form-input" />
        </div>
        </div>
      </section>

      <!-- 滚动长截图 -->
      <section class="settings-section">
        <button class="section-header" type="button" @click="toggleSection('scroll')">
          <span class="section-title">{{ t('settings.scrollScreenshot.title') }}</span>
          <span class="section-summary">{{ sectionSummary.scroll }}</span>
          <span class="collapse-icon" :class="{ rotated: !collapsedSections.scroll }">›</span>
        </button>
        <div class="section-content" v-show="!collapsedSections.scroll">
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.scrollScreenshot.maxScrolls') }}
              <span class="help-icon" :title="t('settings.tooltips.maxScrolls')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.maxScrolls" min="1" max="100" class="form-input" />
          </div>
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.scrollScreenshot.defaultScrollPercent') }}
              <span class="help-icon" :title="t('settings.tooltips.defaultScrollPercent')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.defaultScrollPercent" min="0.1" max="0.95" step="0.05" class="form-input" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.scrollScreenshot.defaultScrollWait') }}
              <span class="help-icon" :title="t('settings.tooltips.defaultScrollWait')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.defaultScrollWait" min="0.1" max="10" step="0.1" class="form-input" />
          </div>
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.scrollScreenshot.maxScrollWait') }}
              <span class="help-icon" :title="t('settings.tooltips.maxScrollWait')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.maxScrollWait" min="1" max="120" class="form-input" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.scrollScreenshot.maxTimeout') }}
              <span class="help-icon" :title="t('settings.tooltips.maxTimeout')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.maxTimeout" min="10" max="300" class="form-input" />
          </div>
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.scrollScreenshot.maxAdjustRetries') }}
              <span class="help-icon" :title="t('settings.tooltips.maxAdjustRetries')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.maxAdjustRetries" min="0" max="10" class="form-input" />
          </div>
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.scrollScreenshot.scrollImageQuality') }}
              <span class="help-icon" :title="t('settings.tooltips.scrollImageQuality')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.scrollImageQuality" min="1" max="100" class="form-input" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.scrollScreenshot.targetOverlapMin') }}
              <span class="help-icon" :title="t('settings.tooltips.targetOverlapMin')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.targetOverlapMin" min="0.1" max="0.5" step="0.05" class="form-input" />
          </div>
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.scrollScreenshot.targetOverlapMax') }}
              <span class="help-icon" :title="t('settings.tooltips.targetOverlapMax')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.targetOverlapMax" min="0.2" max="0.6" step="0.05" class="form-input" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.scrollScreenshot.stopThreshold') }}
              <span class="help-icon" :title="t('settings.tooltips.stopThreshold')">?</span>
            </label>
            <input type="number" v-model.number="settingsForm.stopThreshold" min="0" max="0.01" step="0.00001" class="form-input" />
          </div>
        </div>
        </div>
      </section>

      <!-- 轮数自检 -->
      <section class="settings-section">
        <button class="section-header" type="button" @click="toggleSection('selfCheck')">
          <span class="section-title">{{ t('settings.selfCheck.title') }}</span>
          <span class="section-summary">{{ sectionSummary.selfCheck }}</span>
          <span class="collapse-icon" :class="{ rotated: !collapsedSections.selfCheck }">›</span>
        </button>
        <div class="section-content" v-show="!collapsedSections.selfCheck">
          <div class="form-group">
            <label class="form-checkbox">
              <input type="checkbox" v-model="settingsForm.selfCheckEnabled" />
              <span>
                {{ t('settings.selfCheck.enabled') }}
                <span class="help-icon help-icon-inline" :title="t('settings.tooltips.selfCheckEnabled')">?</span>
              </span>
            </label>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">
                {{ t('settings.selfCheck.interval') }}
                <span class="help-icon" :title="t('settings.tooltips.selfCheckInterval')">?</span>
              </label>
              <input type="number" v-model.number="settingsForm.selfCheckInterval" min="1" max="100" step="1" class="form-input" />
            </div>
            <div class="form-group">
              <label class="form-label">
                {{ t('settings.selfCheck.minChars') }}
                <span class="help-icon" :title="t('settings.tooltips.selfCheckMinChars')">?</span>
              </label>
              <input type="number" v-model.number="settingsForm.selfCheckMinChars" min="1" max="2000" step="10" class="form-input" />
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.selfCheck.docPath') }}
              <span class="help-icon" :title="t('settings.tooltips.selfCheckDocPath')">?</span>
            </label>
            <input type="text" v-model="settingsForm.selfCheckDocPath" class="form-input" />
          </div>
          <div class="form-group">
            <label class="form-label">
              {{ t('settings.selfCheck.keywords') }}
              <small class="form-hint">{{ t('settings.selfCheck.keywordsHint') }}</small>
              <span class="help-icon" :title="t('settings.tooltips.selfCheckKeywords')">?</span>
            </label>
            <textarea v-model="settingsForm.selfCheckKeywords" rows="6" class="form-textarea"></textarea>
          </div>
        </div>
      </section>

      <!-- 托管模式 -->
      <section class="settings-section">
        <button class="section-header" type="button" @click="toggleSection('delegated')">
          <span class="section-title">{{ t('settings.delegated.title') }}</span>
          <span class="section-summary">{{ sectionSummary.delegated }}</span>
          <span class="collapse-icon" :class="{ rotated: !collapsedSections.delegated }">›</span>
        </button>
        <div class="section-content" v-show="!collapsedSections.delegated">
        <div class="form-group">
          <label class="form-label">
            {{ t('settings.delegated.exitHotkey') }}
            <span class="help-icon" :title="t('settings.delegated.exitHotkeyTip')">?</span>
          </label>
          <input type="text" v-model="settingsForm.exitHotkey" class="form-input" placeholder="ctrl+alt+z" />
        </div>
        </div>
      </section>

      <!-- 操作录制 -->
      <section class="settings-section">
        <button class="section-header" type="button" @click="toggleSection('recording')">
          <span class="section-title">{{ t('settings.recording.title') }}</span>
          <span class="section-summary">{{ sectionSummary.recording }}</span>
          <span class="collapse-icon" :class="{ rotated: !collapsedSections.recording }">›</span>
        </button>
        <div class="section-content" v-show="!collapsedSections.recording">
        <div class="form-group">
          <label class="form-label">
            {{ t('settings.recording.hotkey') }}
            <span class="help-icon" :title="t('settings.recording.hotkeyTip')">?</span>
          </label>
          <input type="text" v-model="settingsForm.recordingHotkey" class="form-input" placeholder="ctrl+alt+\" />
        </div>
        <div class="form-group">
          <label class="form-label">
            {{ t('settings.recording.scrollMergeInterval') }}
            <span class="help-icon" :title="t('settings.recording.scrollMergeIntervalTip')">?</span>
          </label>
          <input type="number" v-model.number="settingsForm.recordingScrollMergeInterval" class="form-input" min="100" max="5000" step="100" />
        </div>
        </div>
      </section>

      <!-- 安全设置 -->
      <section class="settings-section">
        <button class="section-header" type="button" @click="toggleSection('security')">
          <span class="section-title">{{ t('settings.security.title') }}</span>
          <span class="section-summary">{{ sectionSummary.security }}</span>
          <span class="collapse-icon" :class="{ rotated: !collapsedSections.security }">›</span>
        </button>
        <div class="section-content" v-show="!collapsedSections.security">
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
  margin-bottom: var(--sc-space-3);
  border-bottom: 1px solid var(--sc-border);
}

.settings-section:last-of-type {
  border-bottom: none;
  margin-bottom: var(--sc-space-4);
}

.section-header {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(140px, 1fr) minmax(0, 1.2fr) 20px;
  align-items: center;
  gap: var(--sc-space-3);
  padding: var(--sc-space-4) 0;
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  text-align: left;
}

.section-header:hover .section-title {
  color: var(--sc-accent);
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--sc-text-secondary);
}

.section-summary {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: var(--sc-text-tertiary);
  text-align: right;
}

.collapse-icon {
  display: inline-flex;
  justify-content: center;
  color: var(--sc-text-tertiary);
  font-size: 18px;
  transition: transform 0.2s ease;
}

.collapse-icon.rotated {
  transform: rotate(90deg);
}

.section-content {
  padding-bottom: var(--sc-space-5);
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
