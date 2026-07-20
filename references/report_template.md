# ⚠️ 已废弃 — 报告模板

> 2026-07-20：已拆分为 `daily_template.md` 和 `weekly_template.md`。
> 渲染逻辑已移至 `scripts/render/daily.py` 和 `scripts/render/weekly.py`。

## 多日周报模板

```markdown
## {{period.start}} - {{period.end}} 工作内容报告

> 数据来源：飞书会议纪要 | 共 {{total}} 场会议，{{with_note}} 场有纪要

### 📊 概览

| 指标 | 数值 |
|------|------|
| 会议总数 | {{total}} 场 |
| 有纪要 | {{with_note}} 场 |
| 有妙记 | {{with_minutes}} 场 |
| 无记录 | {{without_any}} 场 |
| 最忙日 | {{busiest_day}}（{{busiest_count}} 场） |

---

### 📅 {{date}}（周X）

| 时间 | 会议 | 纪要 |
|------|------|:----:|
| {{start}}-{{end}} | **{{topic}}** | {{status_emoji}} |

**{{topic}}** 核心内容：
- 要点 1
- 要点 2

**待办：**
- [ ] 待办项 1（负责人：XXX）
- [ ] 待办项 2（负责人：XXX）

---

### 📊 工作脉络总结

1. **工作主线 1** — 简述
2. **工作主线 2** — 简述
3. **工作主线 3** — 简述

> ⚠️ 注：{{fetch_errors}} 场会议纪要获取失败，{{missing_scope}} 场需额外授权。
```

## 单日模板

适用于只查一天的场景，结构同上但省略"概览"和"工作脉络总结"章节。

## 状态图标

| 状态 | 图标 |
|------|:----:|
| 有纪要，获取成功 | ✅ |
| 有纪要，获取失败 | ⚠️ |
| 需授权 | 🔒 |
| 无纪要/录制 | — |