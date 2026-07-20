# config.yaml 完整参考

配置文件位于 `{workspace}/.workbuddy/data/config.yaml`，缺失时自动使用默认配置。

## 完整示例

```yaml
# 数据源声明（供同步层使用，work-report-generator 只读取）
data_sources:
  tasks: lark_task          # lark_task | tapd | github_issues | manual
  calendar: lark_calendar    # lark_calendar | google_calendar
  meetings: lark_vc          # lark_vc | tmeet

# 输出渠道配置
outputs:
  daily:
    - type: feishu_msg       # 飞书消息推送
    - type: local_md         # 本地 Markdown 存档
  weekly:
    - type: feishu_msg       # 飞书消息推送（预览）
    - type: local_md         # 本地 Markdown 存档
    - type: feishu_doc       # 飞书文档发布（确认后）
    # 可替换为: tencent_doc / notion / ...

# 渠道配置（仅当 outputs 中包含对应 type 时需要）
channels:
  feishu:
    msg_target: self           # 消息推送目标：self | chat_id | user_id
    doc_folder: ""             # 飞书文档存放文件夹 token（空则默认根目录）

# 报告偏好
report:
  daily:
    include_stale_tasks: true
    stale_threshold_days: 7
    max_items_per_section: 20
    sync_if_stale_minutes: 60   # 距上次同步超过此时间则提示先同步
  weekly:
    include_threads: true
    include_charts: false
    confirm_before_publish: true
    sync_if_stale_minutes: 60

# 自动化配置（供参考）
automation:
  sync:
    schedule: "每天 17:20"
    scope_days: 3
  daily_report:
    schedule: "工作日 8:45"
  weekly_report:
    schedule: "周五 17:25"
    scope_days: 7
```

## 字段说明

### outputs

| 字段 | 类型 | 说明 |
|------|------|------|
| `daily` | list | 日报输出渠道列表 |
| `weekly` | list | 周报输出渠道列表 |

支持的输出类型：

| type | 说明 |
|------|------|
| `local_md` | 本地 Markdown 文件 |
| `feishu_msg` | 飞书消息推送 |
| `feishu_doc` | 飞书文档发布 |
| `tencent_doc` | 腾讯文档（需先配置 channels.tencent_doc） |

### report.daily

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `include_stale_tasks` | `true` | 是否包含僵尸任务 |
| `stale_threshold_days` | `7` | 僵尸任务判定天数 |
| `max_items_per_section` | `20` | 每节最多展示条数 |
| `sync_if_stale_minutes` | `60` | 距上次同步超时则提示 |

### report.weekly

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `include_threads` | `true` | 是否包含工作脉络 |
| `include_charts` | `false` | 是否包含图表（未来） |
| `confirm_before_publish` | `true` | 周报确认门禁 |
| `sync_if_stale_minutes` | `60` | 距上次同步超时则提示 |

## 默认配置

如果 `config.yaml` 不存在，系统使用以下默认值：

- 数据源：`lark_task`, `lark_calendar`, `lark_vc`
- 日报输出：`feishu_msg`, `local_md`
- 周报输出：`feishu_msg`, `local_md`, `feishu_doc`
- 飞书消息目标：`self`
- 所有 report 配置使用默认值