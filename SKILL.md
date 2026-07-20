---
name: work-report-generator
description: >-
  接收结构化工作数据（会议纪要、任务记录等），按日期组织、提取关键工作项，
  生成日报/周报 Markdown 报告。数据源无关，可复用。触发词：生成工作周报、
  整理工作内容、汇总会议、工作报告、weekly report。
agent_created: true
---

# 工作内容报告生成器

接收结构化的工作数据 JSON，生成按日期组织的日报/周报 Markdown 报告。
**数据源无关**——只要输入符合 schema，任何数据源都能用。

## 输入

默认读取当前工作目录下的 `meetings_data.json`（由 `lark-meeting-fetcher` 产出）。
也支持用户指定其他 JSON 文件路径。

输入格式定义见 `references/input_schema.md`。

## 工作流

### Step 1: 读取并校验输入

```bash
# 读取 JSON 文件
cat meetings_data.json | python -m json.tool > /dev/null
```

校验 `period`、`meetings` 数组存在且非空。若数据为空，告知用户并终止。

### Step 2: 按日期分组

将所有 meeting 按 `date` 字段分组，按日期升序排列。

### Step 3: 提取关键工作项

对每个 meeting，从 `ai_summary` 和 `todos` 中提取：

- 与当前用户相关的任务（如用户信息可获取，则匹配名称；否则提取全部）
- 会议核心议题
- 待办事项及责任人

### Step 4: 生成概览统计

```
- 会议总数：11 场
- 有纪要：7 场，有妙记：3 场，无记录：3 场
- 最忙日期：6月17日（5 场会议）
```

### Step 5: 生成每日详情

对每一天：
1. 列出当天所有会议（时间、主题、纪要状态）
2. 对有纪要的会议，用 2-3 句话摘要核心内容
3. 列出关键待办

### Step 6: 生成工作脉络总结

按主题维度归纳整个周期的工作主线：
- 从会议主题中提取高频关键词
- 跨日期串联同一主题的进展
- 输出 3-5 条工作主线，每条 1-2 句话

### Step 7: 输出报告

将报告写入 `work_report_<start>_<end>.md`，格式见 `references/report_template.md`。

## 报告格式规范

- 标题：`## 时间范围 工作内容报告`
- 每个日期用 `### 📅 MM月DD日（周X）` 作为二级标题
- 会议用表格展示概要，纪要内容用要点列表
- 使用 emoji 标注纪要状态：✅ 有纪要 / ⚠️ 获取失败 / 🔒 需授权 / — 无记录
- 最终输出控制在 50-70 行以内

## 数据源扩展

本 skill 不绑定飞书。任何数据源只要输出符合 `references/input_schema.md` 的 JSON，
即可用本 skill 生成报告。未来可接入：

- TAPD 任务数据
- GitHub commits
- 飞书文档变更记录
- 自定义工作日志

只需在对接时新增一个 fetcher skill（如 `tapd-task-fetcher`），
输出统一格式的 JSON，本 skill 即可复用。

## 参考

- 输入格式定义：`references/input_schema.md`
- 报告模板：`references/report_template.md`