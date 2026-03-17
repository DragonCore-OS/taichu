# Taichu Frontend

> 华夏文明谱前端应用 - 可视化 Round 17.4 和 Gate 3 执行进度

---

## 项目概述

本前端用于可视化展示：
- **Round 17.4**: 安全修复进度、误伤分析、实时指标
- **Gate 3**: 任务库浏览、Benchmark 结果、对比分析
- **Persona System v2**: 19 席位展示、发言模拟

---

## 技术栈

```
React 18 + TypeScript
Tailwind CSS
React Router v6
Recharts (数据可视化)
Axios (API 通信)
```

---

## 目录结构

```
frontend/
├── src/
│   ├── components/     # 可复用组件
│   │   ├── Layout.tsx
│   │   ├── Sidebar.tsx
│   │   ├── MetricCard.tsx
│   │   └── TaskCard.tsx
│   ├── pages/          # 页面组件
│   │   ├── Dashboard.tsx      # 总览
│   │   ├── Round17.tsx        # Round 17.4 详情
│   │   ├── Gate3.tsx          # Gate 3 详情
│   │   ├── Tasks.tsx          # 任务库浏览
│   │   └── Personas.tsx       # 19 席位展示
│   ├── api/            # API 接口
│   │   └── index.ts
│   ├── utils/          # 工具函数
│   │   └── format.ts
│   └── App.tsx
├── public/
│   └── index.html
├── docs/               # 开发文档
│   └── API_SPEC.md
└── README.md
```

---

## 核心功能模块

### 1. Dashboard 总览
- Round 17.4 当前状态 (FB 率、Alignment)
- Gate 3 Phase 进度
- 关键指标卡片

### 2. Round 17.4 监控
- 实时 FB 率趋势图
- live_auto 样本分析
- 误伤分型可视化
- Step 2-5 进度追踪

### 3. Gate 3 Benchmark
- 50 任务库浏览
- 任务详情展示
- Pilot 结果对比
- 三组对照分析

### 4. Persona System
- 19 核心席位展示
- 人格卡片 (文化、专长)
- 发言模拟界面
- Audit trail 展示

---

## API 接口规范

详见 `docs/API_SPEC.md`

关键接口：
```
GET  /api/status          # 当前状态
GET  /api/r17/progress    # Round 17.4 进度
GET  /api/gate3/tasks     # 任务库
POST /api/simulate        # 发言模拟
```

---

## 开发指引

### 本地启动
```bash
cd frontend
npm install
npm run dev
```

### 构建
```bash
npm run build
```

### 代码规范
- ESLint + Prettier
- 组件名 PascalCase
- 函数名 camelCase
- 类型定义严格

---

## 设计参考

### 色彩系统
```
Primary:    #3B82F6 (蓝色)
Success:    #10B981 (绿色)
Warning:    #F59E0B (橙色)
Danger:     #EF4444 (红色)
Neutral:    #6B7280 (灰色)
```

### 状态标识
```
✅ PASS  → 绿色
❌ FAIL  → 红色  
🔄 进行中 → 蓝色
⏸️ HOLD  → 橙色
🔒 LOCKED → 灰色
```

---

## 与后端集成

后端数据位置：
- Round 17.4: `CodeBuddy/20260310101858/data/shadow/`
- Gate 3 任务: `persona_system_v2/gate3_tasks/`
- Persona Registry: `persona_system_v2/data/`

---

*由 Codex 协助开发*
