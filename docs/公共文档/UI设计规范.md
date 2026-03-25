---
description: DeepJelly UI设计规范v3，米白+深炭黑淡雅风格
version: 3.0
---

# DeepJelly UI 规范 v3

## 概述

DeepJelly 采用**米白+深炭黑**的淡雅配色方案，灵感源自 Claude 官网风格。温暖专业的视觉体验，适合长时间使用的 AI 助手产品。

## 设计原则

1. **温暖专业** - 米白色调营造亲切感，避免冷峻的科技蓝
2. **充足留白** - 呼吸感强的间距系统
3. **圆润友好** - 大圆角设计，降低攻击性
4. **克制用色** - 强调色仅用于微交互，不喧宾夺主
5. **深色点缀** - 代码块、日志区使用深色形成视觉层次

## 色彩系统

### 背景色

| Token | 色值 | 用途 |
|-------|------|------|
| `--dj-bg-primary` | `#FAF9F6` | 主背景，温暖米白 |
| `--dj-bg-secondary` | `#F5F3EE` | 次级背景，卡片hover态 |
| `--dj-bg-tertiary` | `#EFEDE8` | 第三层背景，骨架屏等 |
| `--dj-bg-elevated` | `#FFFFFF` | 浮层、弹窗、输入框背景 |
| `--dj-bg-glass` | `rgba(255,255,255,0.85)` | 毛玻璃效果背景 |

### 文字色

| Token | 色值 | 用途 |
|-------|------|------|
| `--dj-text-primary` | `#1A1A1A` | 主文字，深炭黑 |
| `--dj-text-secondary` | `#4A4A4A` | 次级文字，描述、标签 |
| `--dj-text-tertiary` | `#737373` | 第三级文字，时间、提示 |
| `--dj-text-muted` | `#A3A3A3` | 弱化文字，placeholder |

### 强调色

| Token | 色值 | 用途 |
|-------|------|------|
| `--dj-accent` | `#D97706` | 暖琥珀，focus状态、选中指示 |
| `--dj-accent-light` | `#F59E0B` | 浅琥珀 |
| `--dj-accent-dark` | `#B45309` | 深琥珀 |
| `--dj-accent-glow` | `rgba(217,119,6,0.15)` | 聚焦光晕 |

### 语义色

| Token | 色值 | 用途 |
|-------|------|------|
| `--dj-success` | `#059669` | 成功状态 |
| `--dj-warning` | `#D97706` | 警告状态 |
| `--dj-danger` | `#DC2626` | 危险/删除操作 |
| `--dj-info` | `#2563EB` | 信息提示（极少使用） |

### 边框与阴影

| Token | 值 | 用途 |
|-------|------|------|
| `--dj-border` | `rgba(0,0,0,0.06)` | 细边框、分隔线 |
| `--dj-border-strong` | `rgba(0,0,0,0.12)` | 强边框、hover态 |
| `--dj-shadow-sm` | `0 1px 2px rgba(0,0,0,0.04)` | 微弱阴影 |
| `--dj-shadow-md` | `0 4px 12px rgba(0,0,0,0.06)` | 中等阴影 |
| `--dj-shadow-lg` | `0 8px 24px rgba(0,0,0,0.08)` | 强阴影，弹窗 |

## 间距系统

| Token | 值 | 用途 |
|-------|------|------|
| `--dj-space-1` | 4px | 图标间距 |
| `--dj-space-2` | 8px | 紧凑间隙 |
| `--dj-space-3` | 12px | 小间隙 |
| `--dj-space-4` | 16px | 标准间隙 |
| `--dj-space-5` | 20px | 大间隙 |
| `--dj-space-6` | 24px | 区块间距 |
| `--dj-space-8` | 32px | 大区块间距 |

## 圆角系统

| Token | 值 | 用途 |
|-------|------|------|
| `--dj-radius-sm` | 8px | 小按钮、标签 |
| `--dj-radius-md` | 12px | 标准按钮、输入框 |
| `--dj-radius-lg` | 16px | 卡片、弹窗 |
| `--dj-radius-xl` | 24px | 大卡片 |
| `--dj-radius-full` | 9999px | 药丸形、圆形 |

## 组件规范

### 主按钮

```css
background: var(--dj-text-primary);  /* 深炭黑 */
color: var(--dj-bg-primary);          /* 米白字 */
border-radius: 12px;
padding: 12px 24px;
font-weight: 500;
```

- Hover: 背景变 `--dj-text-secondary`，轻微上浮
- 禁用: 透明度 0.4

### 次级按钮

```css
background: transparent;
color: var(--dj-text-primary);
border: 1px solid var(--dj-border-strong);
border-radius: 12px;
```

### 输入框

```css
background: var(--dj-bg-elevated);    /* 纯白 */
border: 1px solid var(--dj-border-strong);
border-radius: 10px;
padding: 12px 14px;
```

- Focus: 添加琥珀色光晕 `--dj-accent-glow`
- Placeholder: `--dj-text-muted`

### 会话卡片

```css
padding: 14px 16px;
margin: 2px 12px;
border-radius: 14px;
gap: 14px;
```

- 头像: 48x48px，圆角 14px
- 标题: 15px，font-weight: 600

### 消息气泡

**用户消息（右侧）:**
```css
background: var(--dj-text-primary);   /* 深炭黑 */
color: var(--dj-bg-primary);          /* 米白字 */
border-radius: 18px;
border-bottom-right-radius: 4px;
```

**助手消息（左侧）:**
```css
background: var(--dj-bg-elevated);    /* 纯白 */
border: 1px solid var(--dj-border);
border-radius: 18px;
border-bottom-left-radius: 4px;
```

### 代码块

保持**深色主题**形成视觉对比：
```css
background: #1e1e1e;
color: #d4d4d4;
border: 1px solid #3e3e42;
```

## 文件引入

所有组件样式文件应首先引入设计系统：

```typescript
import "@/styles/design-system.css";
import "./Component.css";
```

## 注意事项

1. **不要**硬编码颜色值，全部使用 CSS 变量
2. **不要**使用紫色系（避免 AI 产品常见蓝紫色调）
3. **代码块**保持深色，形成视觉休息区
4. **强调色**仅用于交互反馈，大面积使用主色调
'@ | Out-File -FilePath 'reqs_new/公共文档/UI规范.md' -Encoding utf8"