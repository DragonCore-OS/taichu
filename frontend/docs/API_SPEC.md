# Frontend API Specification

## 基础信息

- **Base URL**: `/api/v1`
- **Format**: JSON
- **Auth**: 暂不启用 (内部系统)

---

## 接口列表

### 1. 获取系统状态

```http
GET /api/status
```

**Response**:
```json
{
  "round17": {
    "step": 2,
    "alignment": 76,
    "overall_fb": 16,
    "live_auto_fb": 23.1,
    "status": "in_progress"
  },
  "gate3": {
    "phase": "phase_1_complete",
    "tasks_ready": 50,
    "phase_2_status": "hold"
  }
}
```

---

### 2. Round 17.4 进度

```http
GET /api/r17/progress
```

**Response**:
```json
{
  "current_step": 2,
  "steps": [
    {"id": 1, "name": "样本抽取", "status": "completed"},
    {"id": 2, "name": "误伤分型", "status": "in_progress"},
    {"id": 3, "name": "根因归类", "status": "pending"},
    {"id": 4, "name": "单点修复", "status": "pending"},
    {"id": 5, "name": "50样本验证", "status": "pending"}
  ],
  "samples": [
    {
      "id": "OBS-83edbf9afd08",
      "issue_type": "technical_decision",
      "risk_level": "medium",
      "deliberation_score": 74,
      "review_score": 63
    }
  ]
}
```

---

### 3. 获取任务库

```http
GET /api/gate3/tasks
```

**Query Params**:
- `category`: strategic|system_design|diplomatic|conflict_resolution|crisis_response
- `complexity_min`: 1-10
- `complexity_max`: 1-10

**Response**:
```json
{
  "total": 50,
  "categories": {
    "strategic": 10,
    "system_design": 10,
    "diplomatic": 10,
    "conflict_resolution": 10,
    "crisis_response": 10
  },
  "tasks": [
    {
      "task_id": "strategic_001",
      "name": "新兴市场进入策略",
      "complexity": 7,
      "category": "strategic",
      "estimated_tokens": 8000
    }
  ]
}
```

---

### 4. 获取单个任务详情

```http
GET /api/gate3/tasks/:task_id
```

**Response**:
```json
{
  "task_id": "strategic_001",
  "name": "新兴市场进入策略",
  "complexity": 7,
  "category": "strategic",
  "description": "公司 A 是成熟的 SaaS 企业...",
  "requirements": [...],
  "success_criteria": {
    "mandatory": [...],
    "optional": [...]
  },
  "evaluation_rubric": {...},
  "estimated_tokens": 8000,
  "max_turns": 15
}
```

---

### 5. 获取 19 核心席位

```http
GET /api/personas
```

**Response**:
```json
{
  "total": 19,
  "personas": [
    {
      "seat_id": "00001",
      "name": "鬼谷子",
      "archetype": "strategist",
      "expertise_domains": ["strategy", "persuasion"],
      "cultural_lineage": "纵横家",
      "thinking_style": "analytical"
    }
  ]
}
```

---

### 6. 发言模拟

```http
POST /api/simulate
```

**Body**:
```json
{
  "persona_id": "00001",
  "round_num": 1,
  "issue_title": "如何应对外部威胁",
  "issue_type": "strategic"
}
```

**Response**:
```json
{
  "name": "鬼谷子",
  "stance": "propose",
  "content": "鬼谷子观，此事之战略目标...",
  "verified": true,
  "audit": {
    "template_divergence_score": 0.7,
    "culture_match_score": 0.5,
    "registry_keys_used": ["00001"]
  }
}
```

---

## Mock 数据

开发阶段使用静态 JSON 文件：
- `public/mock/status.json`
- `public/mock/tasks.json`
- `public/mock/personas.json`

---

## 错误处理

```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task not found",
    "status": 404
  }
}
```

---

## 状态码

| Code | Meaning |
|------|---------|
| 200 | OK |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Server Error |
