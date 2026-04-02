import { createApp } from 'vue'
import { createI18n } from 'vue-i18n'
import App from './App.vue'
import './style.css'
import { invoke } from '@tauri-apps/api/core'

// 全局快捷键：F12 打开开发者工具
document.addEventListener('keydown', (e) => {
  if (e.key === 'F12') {
    e.preventDefault()
    invoke('open_devtools').catch(err => {
      console.error('Failed to open devtools:', err)
    })
  }
  // Ctrl+Shift+I 也打开开发者工具
  if (e.ctrlKey && e.shiftKey && e.key === 'I') {
    e.preventDefault()
    invoke('open_devtools').catch(err => {
      console.error('Failed to open devtools:', err)
    })
  }
})

// 国际化配置
const i18n = createI18n({
  legacy: false,
  locale: 'zh_CN',
  fallbackLocale: 'en_US',
  messages: {
    zh_CN: {
      app: {
        title: 'ScreenClaw',
        monitoring: '监控面板',
        settings: '设置/Setting'
      },
      service: {
        status: '服务状态',
        running: '运行中',
        stopped: '已停止',
        start: '启动服务',
        stop: '停止服务',
        localAddress: '本机地址',
        lanAddress: '局域网地址',
        token: '访问令牌',
        connectionInfo: '连接信息'
      },
      logs: {
        title: '指令日志',
        filter: '筛选',
        search: '搜索',
        searchPlaceholder: '搜索指令内容或进程名...',
        keyword: '关键词',
        aiApp: 'AI 应用',
        targetApp: '操作应用',
        allApps: '全部应用',
        sessionId: '会话 ID',
        sessionPlaceholder: '输入会话ID模糊搜索...',
        session: '会话',
        date: '日期',
        allDates: '全部日期',
        time: '时间',
        process: '进程',
        instruction: '指令',
        result: '结果',
        duration: '耗时',
        success: '成功',
        failed: '失败',
        viewDetails: '查看详情',
        loading: '加载中...',
        empty: '暂无日志记录',
        noMatch: '没有匹配的日志',
        showing: '显示',
        clearFilter: '清除筛选'
      },
      settings: {
        title: '系统设置',
        server: {
          title: '服务配置',
          port: '端口',
          token: '访问令牌',
          regenerate: '重新生成'
        },
        screenshot: {
          title: '截图默认值',
          gridTitle: '网格默认值',
          numberTitle: '数字默认值',
          imageTitle: '图片设置',
          gridDensity: '网格密度',
          gridColor: '网格颜色',
          gridOpacity: '网格透明度',
          numberDensity: '数字密度',
          numberDecimal: '小数位数',
          numberSize: '数字大小',
          numberColor: '数字颜色',
          numberOpacity: '数字透明度',
          imageQuality: '图片质量',
          maxImageWidth: '最大图片宽度'
        },
        security: {
          title: '安全设置',
          autoConfirmProcesses: '自动同意键盘鼠标操作',
          blockedProcesses: '禁止访问进程',
          addProcess: '添加进程'
        },
        ui: {
          title: '界面设置',
          language: '语言 / Language',
          languageTip: '切换界面显示语言',
          autoStart: '开机自启动',
          autoStartTip: '系统启动时自动运行 ScreenClaw'
        },
        tooltips: {
          port: 'HTTP 服务监听端口，用于接收 AI 应用的 API 请求',
          token: 'API 访问密钥，防止未授权访问你的设备',
          gridDensity: '屏幕网格的间距（像素），值越小网格越密集',
          gridOpacity: '网格线的不透明度，0%=完全透明，100%=完全不透明',
          gridColor: '网格线的显示颜色',
          numberDensity: '每隔多少个网格显示一个坐标数字。例如值为2，表示每隔2个网格显示一次坐标',
          numberDecimal: '坐标是百分比形式（宽%, 高%），控制百分比后的小数位数。例如 (50.1, 50.1) 表示屏幕中心偏右下位置，小数位数为1',
          numberSize: '坐标数字的字体大小（像素）',
          numberOpacity: '坐标数字的不透明度，0%=完全透明，100%=完全不透明',
          numberColor: '坐标数字的显示颜色',
          imageQuality: 'JPEG 压缩质量（1-100），值越高图片越清晰但文件越大',
          maxImageWidth: '截图缩放的最大宽度，超过会等比缩放以节省传输带宽',
          autoConfirmProcesses: '列表中的进程执行键盘/鼠标操作时，自动批准无需弹窗确认',
          blockedProcesses: '列表中的进程禁止执行任何键盘/鼠标操作'
        },
        save: '保存配置',
        reset: '恢复默认'
      },
      confirm: {
        title: '操作确认',
        message: 'ScreenClaw 需要临时控制你的键盘和鼠标',
        process: '目标进程',
        source: '指令来源',
        allow: '允许',
        cancel: '取消'
      },
      common: {
        save: '保存',
        cancel: '取消',
        confirm: '确认',
        close: '关闭',
        copy: '复制',
        lineByLine: '每行一个',
        refresh: '刷新',
        loading: '获取中...'
      },
      aiIntegrate: {
        button: 'AI自动集成',
        title: '复制提示词发给AI',
        copyButton: '复制提示词',
        tabOpenclaw: 'OpenClaw',
        tabOthers: '其它AI应用',
        // OpenClaw 提示词
        promptTitle: '请帮我集成 ScreenClaw 屏幕可视化操作服务',
        stepOne: '第一步',
        stepOneTitle: '安装技能',
        stepTwo: '第二步',
        stepTwoTitle: '写入技能配置',
        stepTwoDesc: '将下面的地址和令牌保存到技能配置里',
        stepTwoConfigPath: '~/.openclaw/screenclaw/reference/config.md',
        stepThree: '第三步',
        stepThreeTitle: '更新openclaw主配置',
        stepThreeDesc: '将技能目录更新到openclaw.json',
        stepFour: '第四步',
        stepFourTitle: '回复用户',
        stepFourDesc: '在重启网关之前，必须先向用户报告以下信息',
        stepFourSkillLocation: '技能位置',
        stepFourConfigFile: '配置文件',
        stepFourConfigWritten: '已写入',
        stepFourTriggerMode: '触发方式',
        stepFourTriggerExample1: '帮我自动操作{应用名}，{任务描述}',
        stepFourTriggerExample2: '使用screenclaw技能完成{目标}',
        stepFourRestartWarning: '网关将在 20 秒后自动重启...',
        stepFive: '第五步',
        stepFiveTitle: '延迟重启',
        stepFiveDesc: '在回复用户后，执行延迟重启命令',
        linuxMacOS: 'Linux/macOS',
        windows: 'Windows',
        serviceAddress: '服务地址',
        accessToken: '访问令牌',
        extraDirs: '第一步技能安装后的绝对路径',
        // 通用AI提示词
        othersPromptTitle: '请帮我集成 ScreenClaw 屏幕可视化操作服务',
        othersStepOne: '第一步',
        othersStepOneTitle: '安装',
        othersStepTwo: '第二步',
        othersStepTwoTitle: '配置',
        othersStepTwoDesc: '将下面的地址和令牌保存到技能配置里',
        othersConfigFilePath: 'screenclaw/reference/config.md'
      }
    },
    en_US: {
      app: {
        title: 'ScreenClaw',
        monitoring: 'Monitoring',
        settings: '设置/Setting'
      },
      service: {
        status: 'Service Status',
        running: 'Running',
        stopped: 'Stopped',
        start: 'Start Service',
        stop: 'Stop Service',
        localAddress: 'Local Address',
        lanAddress: 'LAN Address',
        token: 'Access Token',
        connectionInfo: 'Connection Info'
      },
      logs: {
        title: 'Instruction Logs',
        filter: 'Filter',
        search: 'Search',
        searchPlaceholder: 'Search instruction or process name...',
        keyword: 'Keyword',
        aiApp: 'AI App',
        targetApp: 'Target App',
        allApps: 'All Apps',
        sessionId: 'Session ID',
        sessionPlaceholder: 'Enter session ID to search...',
        session: 'Session',
        date: 'Date',
        allDates: 'All Dates',
        time: 'Time',
        process: 'Process',
        instruction: 'Instruction',
        result: 'Result',
        duration: 'Duration',
        success: 'Success',
        failed: 'Failed',
        viewDetails: 'View Details',
        loading: 'Loading...',
        empty: 'No logs yet',
        noMatch: 'No matching logs',
        showing: 'Showing',
        clearFilter: 'Clear Filters'
      },
      settings: {
        title: '系统设置',
        server: {
          title: 'Server Configuration',
          port: 'Port',
          token: 'Access Token',
          regenerate: 'Regenerate'
        },
        screenshot: {
          title: 'Screenshot Defaults',
          gridTitle: 'Grid Defaults',
          numberTitle: 'Number Defaults',
          imageTitle: 'Image Settings',
          gridDensity: 'Grid Density',
          gridColor: 'Grid Color',
          gridOpacity: 'Grid Opacity',
          numberDensity: 'Number Density',
          numberDecimal: 'Decimal Places',
          numberSize: 'Number Size',
          numberColor: 'Number Color',
          numberOpacity: 'Number Opacity',
          imageQuality: 'Image Quality',
          maxImageWidth: 'Max Image Width'
        },
        security: {
          title: 'Security Settings',
          autoConfirmProcesses: 'Auto-approve mouse & keyboard control',
          blockedProcesses: 'Blocked Processes',
          addProcess: 'Add Process'
        },
        ui: {
          title: 'Interface Settings',
          language: 'Language / 语言',
          languageTip: 'Switch interface display language',
          autoStart: 'Auto Start on Boot',
          autoStartTip: 'Automatically launch ScreenClaw when system starts'
        },
        tooltips: {
          port: 'HTTP service listening port for receiving AI app API requests',
          token: 'API access key to prevent unauthorized access to your device',
          gridDensity: 'Screen grid spacing in pixels, lower values create denser grids',
          gridOpacity: 'Grid line opacity, 0%=fully transparent, 100%=fully opaque',
          gridColor: 'Display color of grid lines',
          numberDensity: 'Show coordinate number every N grids. E.g., value 2 means show once every 2 grids',
          numberDecimal: 'Coordinates are in percentage form (width%, height%). Controls decimal places. E.g., (50.1, 50.1) means center-right position with 1 decimal place',
          numberSize: 'Font size of coordinate numbers in pixels',
          numberOpacity: 'Coordinate number opacity, 0%=fully transparent, 100%=fully opaque',
          numberColor: 'Display color of coordinate numbers',
          imageQuality: 'JPEG compression quality (1-100), higher values produce clearer images but larger files',
          maxImageWidth: 'Maximum width for screenshot scaling, images are proportionally scaled down to save bandwidth',
          autoConfirmProcesses: 'Processes in this list can perform keyboard/mouse operations without confirmation popup',
          blockedProcesses: 'Processes in this list are prohibited from any keyboard/mouse operations'
        },
        save: 'Save',
        reset: 'Reset to Defaults'
      },
      confirm: {
        title: 'Confirm Operation',
        message: 'ScreenClaw needs to temporarily control your keyboard and mouse',
        process: 'Target Process',
        source: 'Source',
        allow: 'Allow',
        cancel: 'Cancel'
      },
      common: {
        save: 'Save',
        cancel: 'Cancel',
        confirm: 'Confirm',
        close: 'Close',
        copy: 'Copy',
        lineByLine: 'one per line',
        refresh: 'Refresh',
        loading: 'Loading...'
      },
      aiIntegrate: {
        button: 'AI Auto Integrate',
        title: 'Copy Prompt for AI Integration',
        copyButton: 'Copy Prompt',
        tabOpenclaw: 'OpenClaw',
        tabOthers: 'Other AI Apps',
        // OpenClaw prompts
        promptTitle: 'Please help me integrate ScreenClaw Visual Screen Control Service',
        stepOne: 'Step 1',
        stepOneTitle: 'Install Skill',
        stepTwo: 'Step 2',
        stepTwoTitle: 'Write Skill Config',
        stepTwoDesc: 'Save the address and token below to the skill config',
        stepTwoConfigPath: '~/.openclaw/screenclaw/reference/config.md',
        stepThree: 'Step 3',
        stepThreeTitle: 'Update OpenClaw Main Config',
        stepThreeDesc: 'Update skill directory to openclaw.json',
        stepFour: 'Step 4',
        stepFourTitle: 'Reply to User',
        stepFourDesc: 'Before restarting gateway, must report the following to user',
        stepFourSkillLocation: 'Skill Location',
        stepFourConfigFile: 'Config File',
        stepFourConfigWritten: 'Written',
        stepFourTriggerMode: 'Trigger Mode',
        stepFourTriggerExample1: 'Help me auto-operate {app}, {task}',
        stepFourTriggerExample2: 'Use screenclaw skill to complete {goal}',
        stepFourRestartWarning: 'Gateway will restart in 20 seconds...',
        stepFive: 'Step 5',
        stepFiveTitle: 'Delayed Restart',
        stepFiveDesc: 'After replying to user, execute delayed restart command',
        linuxMacOS: 'Linux/macOS',
        windows: 'Windows',
        serviceAddress: 'Service Address',
        accessToken: 'Access Token',
        extraDirs: 'Absolute path after skill installation in step 1',
        // Generic AI prompts
        othersPromptTitle: 'Please help me integrate ScreenClaw Visual Screen Control Service',
        othersStepOne: 'Step 1',
        othersStepOneTitle: 'Install',
        othersStepTwo: 'Step 2',
        othersStepTwoTitle: 'Configuration',
        othersStepTwoDesc: 'Save the address and token below to the skill config',
        othersConfigFilePath: 'screenclaw/reference/config.md'
      }
    }
  }
})

const app = createApp(App)
app.use(i18n)
app.mount('#app')
