# work-report-generator

WorkBuddy Skill: 接收结构化工作数据（会议纪要、任务记录等），按日期组织、提取关键工作项，生成日报/周报 Markdown 报告。数据源无关，可复用。

## 触发词

生成工作周报、整理工作内容、汇总会议、工作报告、weekly report

## 文件结构

- `SKILL.md` - 技能定义文件
- `references/input_schema.md` - 输入数据格式定义
- `references/report_template.md` - 报告模板

## 使用方式

作为 WorkBuddy Skill 安装后，当用户提到触发词时自动加载。输入数据需符合 `references/input_schema.md` 定义的 JSON 格式。