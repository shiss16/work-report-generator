"""llm_enhance.py 测试"""

import json
import pytest
from scripts.llm_enhance import build_daily_prompt, parse_llm_response


class TestBuildDailyPrompt:
    """行为 #1: build_daily_prompt 生成正确结构的 prompt"""

    def test_prompt_contains_meeting_data(self):
        meetings = [
            {
                "title": "项目早会",
                "date": "2026-07-20",
                "start_time": "2026-07-20 09:00",
                "ai_summary": "讨论了进度，决定下周上线",
                "participants": '["张三", "李四"]',
                "todos": '["张三：完成接口开发", "李四：准备测试环境"]',
            },
            {
                "title": "需求评审",
                "date": "2026-07-19",
                "start_time": "2026-07-19 14:00",
                "ai_summary": "评审了新需求，确认了优先级",
                "participants": '["王五"]',
                "todos": '["王五：整理需求文档"]',
            },
        ]

        prompt = build_daily_prompt(meetings, "石上松")

        # 包含会议信息
        assert "项目早会" in prompt
        assert "需求评审" in prompt
        # 包含摘要
        assert "讨论了进度" in prompt
        assert "评审了新需求" in prompt
        # 包含待办
        assert "完成接口开发" in prompt
        assert "准备测试环境" in prompt
        assert "整理需求文档" in prompt
        # 包含用户信息
        assert "石上松" in prompt
        # 包含输出格式要求
        assert "brief" in prompt.lower()
        assert "actions" in prompt.lower()
        assert "priority" in prompt.lower()
        assert "urgent" in prompt.lower()

    def test_prompt_handles_empty_meetings(self):
        prompt = build_daily_prompt([], "石上松")
        # 不应崩溃，应返回有意义的 prompt
        assert len(prompt) > 0
        assert "石上松" in prompt

    def test_prompt_handles_none_fields(self):
        meetings = [
            {
                "title": "通话",
                "date": "2026-07-20",
                "start_time": None,
                "ai_summary": None,
                "participants": '["张三"]',
                "todos": "[]",
            },
        ]
        prompt = build_daily_prompt(meetings, "石上松")
        assert "通话" in prompt
        assert len(prompt) > 0


class TestParseLLMResponse:
    """行为 #2-3: parse_llm_response 解析 LLM 响应"""

    def test_parses_valid_json(self):
        response = json.dumps({
            "brief": "昨天主要讨论了AI场景落地，今天需要关注技术方案评估。",
            "actions": [
                {
                    "priority": "urgent",
                    "content": "完成技术方案评估",
                    "assignee": "石上松",
                    "reason": "阻塞后续AI场景开发",
                    "source": "储能早会",
                },
                {
                    "priority": "high",
                    "content": "与市场部沟通数据问题",
                    "assignee": "龙阳",
                    "reason": "影响总裁驾驶舱上线",
                    "source": "储能早会",
                },
            ],
        })
        result = parse_llm_response(response)
        assert result["brief"] == "昨天主要讨论了AI场景落地，今天需要关注技术方案评估。"
        assert len(result["actions"]) == 2
        assert result["actions"][0]["priority"] == "urgent"
        assert result["actions"][0]["assignee"] == "石上松"

    def test_parses_json_with_markdown_fence(self):
        response = '```json\n{"brief": "测试", "actions": []}\n```'
        result = parse_llm_response(response)
        assert result["brief"] == "测试"
        assert result["actions"] == []

    def test_parses_json_with_plain_fence(self):
        response = '```\n{"brief": "测试", "actions": []}\n```'
        result = parse_llm_response(response)
        assert result["brief"] == "测试"

    def test_handles_empty_response(self):
        result = parse_llm_response("")
        assert result["brief"] == ""
        assert result["actions"] == []

    def test_handles_none_response(self):
        result = parse_llm_response(None)
        assert result["brief"] == ""
        assert result["actions"] == []

    def test_handles_malformed_json(self):
        result = parse_llm_response("这不是 JSON")
        assert result["brief"] == ""
        assert result["actions"] == []

    def test_handles_partial_json_missing_actions(self):
        response = '{"brief": "只有简报，没有行动"}'
        result = parse_llm_response(response)
        assert result["brief"] == "只有简报，没有行动"
        assert result["actions"] == []

    def test_handles_extra_text_around_json(self):
        response = '好的，以下是结果：\n{"brief": "测试", "actions": []}\n希望有帮助。'
        result = parse_llm_response(response)
        assert result["brief"] == "测试"