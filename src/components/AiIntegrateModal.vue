<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { AppConfig } from '../composables/useConfig'

const { t } = useI18n()

const props = defineProps<{
  visible: boolean
  config: AppConfig | null
  appRoot: string
}>()

const emit = defineEmits<{
  close: []
}>()

type TabType = 'openclaw' | 'others'
const activeTab = ref<TabType>('openclaw')

const serviceUrl = computed(() => {
  const port = props.config?.server?.port ?? 12261
  return `http://127.0.0.1:${port}`
})
const token = computed(() => props.config?.server?.token || '')
const skillInstallCmd = 'npx skills add https://github.com/GinSing1226/ScreenClaw -y -g'

const openclawPrompt = computed(() => {
  return `${t('aiIntegrate.promptTitle')}

# ${t('aiIntegrate.stepOne')}: ${t('aiIntegrate.stepOneTitle')}
${t('aiIntegrate.stepOneDesc')}
\`\`\`bash
${skillInstallCmd}
\`\`\`

# ${t('aiIntegrate.stepTwo')}: ${t('aiIntegrate.stepTwoTitle')}
${t('aiIntegrate.stepTwoDesc')} \`${t('aiIntegrate.stepTwoConfigPath')}\`
- ${t('aiIntegrate.serviceAddress')}: \`${serviceUrl.value}\`
- ${t('aiIntegrate.accessToken')}: \`${token.value}\`
- 📂 ${t('aiIntegrate.stepFourAppRoot')}：${props.appRoot}

# ${t('aiIntegrate.stepThree')}：${t('aiIntegrate.stepThreeTitle')}
${t('aiIntegrate.stepThreeDesc')}
\`\`\`json
 "skills": [
    "load": [
      "extraDirs": ["${t('aiIntegrate.extraDirs')}"]
    ]
  ]
\`\`\`

# ${t('aiIntegrate.stepFour')}：**${t('aiIntegrate.stepFourTitle')}**
**${t('aiIntegrate.stepFourDesc')}**
📍 ${t('aiIntegrate.stepFourSkillLocation')}：~/.openclaw/skills/<skill-name>
📋 ${t('aiIntegrate.stepFourConfigFile')}：config.json ${t('aiIntegrate.stepFourConfigWritten')}
📂 ${t('aiIntegrate.stepFourAppRoot')}：${props.appRoot}

🚀 ${t('aiIntegrate.stepFourTriggerMode')}：
  - "${t('aiIntegrate.stepFourTriggerExample1')}"
  - "${t('aiIntegrate.stepFourTriggerExample2')}"

⚠️ ${t('aiIntegrate.stepFourRestartWarning')}

# ${t('aiIntegrate.stepFive')}：**${t('aiIntegrate.stepFiveTitle')}**
${t('aiIntegrate.stepFiveDesc')}

**${t('aiIntegrate.linuxMacOS')}**:
\`\`\`bash
sleep 20 && openclaw gateway restart
\`\`\`

**${t('aiIntegrate.windows')}**:
\`\`\`powershell
Start-Sleep -Seconds 20; openclaw gateway restart
\`\`\``
})

const othersPrompt = computed(() => {
  return `${t('aiIntegrate.othersPromptTitle')}

# ${t('aiIntegrate.othersStepOne')}: **${t('aiIntegrate.othersStepOneTitle')}**
${t('aiIntegrate.othersStepOneDesc')}
\`\`\`bash
${skillInstallCmd}
\`\`\`

# ${t('aiIntegrate.othersStepTwo')}：**${t('aiIntegrate.othersStepTwoTitle')}**
${t('aiIntegrate.othersStepTwoDesc')} \`${t('aiIntegrate.othersConfigFilePath')}\`
- ${t('aiIntegrate.serviceAddress')}: \`${serviceUrl.value}\`
- ${t('aiIntegrate.accessToken')}: \`${token.value}\`
📂 ${t('aiIntegrate.othersAppRoot')}：${props.appRoot}`
})

const currentPrompt = computed(() => {
  return activeTab.value === 'openclaw' ? openclawPrompt.value : othersPrompt.value
})

const switchTab = (tab: TabType) => {
  activeTab.value = tab
}

const copyPrompt = () => {
  navigator.clipboard.writeText(currentPrompt.value)
}
</script>

<template>
  <div v-if="visible" class="modal-overlay" @click="emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>{{ t('aiIntegrate.title') }}</h3>
        <button class="btn-close" @click="emit('close')">×</button>
      </div>

      <div class="tab-header">
        <button class="tab-button" :class="{ active: activeTab === 'openclaw' }" @click="switchTab('openclaw')">
          {{ t('aiIntegrate.tabOpenclaw') }}
        </button>
        <button class="tab-button" :class="{ active: activeTab === 'others' }" @click="switchTab('others')">
          {{ t('aiIntegrate.tabOthers') }}
        </button>
      </div>

      <div class="modal-body">
        <pre class="prompt-content">{{ currentPrompt }}</pre>
      </div>

      <div class="modal-footer">
        <button class="btn-copy" @click="copyPrompt">
          {{ t('aiIntegrate.copyButton') }}
        </button>
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
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--sc-bg-elevated);
  border-radius: var(--sc-radius-lg);
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
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
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--sc-text-tertiary);
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.btn-close:hover {
  color: var(--sc-text-primary);
}

.tab-header {
  display: flex;
  gap: var(--sc-space-1);
  padding: var(--sc-space-3) var(--sc-space-5);
  background: var(--sc-bg-secondary);
  border-bottom: 1px solid var(--sc-border);
}

.tab-button {
  padding: var(--sc-space-2) var(--sc-space-4);
  background: transparent;
  border: none;
  border-radius: var(--sc-radius-md);
  color: var(--sc-text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-button:hover {
  color: var(--sc-text-primary);
  background: var(--sc-bg-tertiary);
}

.tab-button.active {
  color: var(--sc-text-primary);
  background: var(--sc-bg-elevated);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.modal-body {
  flex: 1;
  overflow: auto;
  padding: var(--sc-space-4);
}

.prompt-content {
  margin: 0;
  padding: var(--sc-space-4);
  background: #1a1a1a;
  border-radius: var(--sc-radius-md);
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #e5e5e5;
  white-space: pre-wrap;
  word-break: break-word;
}

.modal-footer {
  padding: var(--sc-space-4) var(--sc-space-5);
  border-top: 1px solid var(--sc-border);
  display: flex;
  justify-content: flex-end;
}

.btn-copy {
  padding: var(--sc-space-2) var(--sc-space-5);
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: var(--sc-radius-sm);
  color: #e5e5e5;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-copy:hover {
  background: #2a2a2a;
  border-color: #444;
}
</style>
