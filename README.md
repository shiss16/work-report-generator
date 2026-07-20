# work-report-generator

WorkBuddy Skill: 从 SQLite 读取结构化工作数据，按日期组织、提取关键工作项，
生成日报/周报 Markdown 报告。数据源无关，配置驱动。

## 触发词

日报、daily、整理工作、周报、weekly、本周总结、工作报告、weekly report

## 快速开始

```bash
# 日报
python scripts/run.py daily

# 周报
python scripts/run.py weekly
```

## 文件结构

```
work-report-generator/
├── SKILL.md                    # 技能定义
├── README.md                   # 本文件
├── scripts/
│   ├── db.py                   # SQLite 工具
│   ├── config.py               # 配置管理
│   ├── query.py                # 查询引擎
│   ├── assemble.py             # 组装引擎
│   ├── cli.py                  # 命令行入口
│   ├── run.py                  # Agent 调用入口
│   └── render/
│       ├── daily.py            # 日报渲染器
│       ├── weekly.py           # 周报渲染器
│       └── markdown_output.py  # 文件输出
├── references/
│   ├── work_item_schema.md     # 数据模型
│   ├── data_source_guide.md    # 接入指南
│   ├── report_dsl.md           # DSL 定义
│   └── config_reference.md     # 配置参考
└── tests/
    ├── test_db.py              # 11 tests
    ├── test_config.py          # 6 tests
    ├── test_query.py           # 9 tests
    └── test_assemble.py        # 5 tests
```

## 测试

```bash
python -m pytest tests/ -v
# 31 passed
```