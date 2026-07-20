"""渲染器抽象基类"""

from abc import ABC, abstractmethod


class BaseRenderer(ABC):
    """所有渲染器的抽象基类

    新增呈现方式（如 PDF、HTML）只需继承此类并实现 render 方法。
    """

    @abstractmethod
    def render(self, report: dict, config: dict) -> str:
        """渲染报告为字符串

        Args:
            report: Assembler 产出的 Report DSL
            config: 完整配置字典

        Returns:
            渲染后的字符串（Markdown / HTML 等）
        """
        ...