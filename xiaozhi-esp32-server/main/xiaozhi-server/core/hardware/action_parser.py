"""
米特(Mint) 动作解析器
从 LLM 回复文本中提取 JSON 动作块
"""

import re
import json
from typing import Optional, Tuple
from config.logger import setup_logging
from .action_protocol import ActionCommand, Motion, Emotion

TAG = __name__
logger = setup_logging()


class ActionParser:
    """从 LLM 回复中解析动作命令"""

    # JSON 块的正则匹配模式
    JSON_PATTERN = re.compile(
        r'\{[^{}]*"text"[^{}]*\}',
        re.DOTALL
    )

    # 更宽松的 JSON 匹配（支持嵌套）
    JSON_BLOCK_PATTERN = re.compile(
        r'\{(?:[^{}]|\{[^{}]*\})*\}',
        re.DOTALL
    )

    @classmethod
    def parse(cls, llm_response: str) -> Tuple[Optional[ActionCommand], str]:
        """
        解析 LLM 回复，提取动作命令

        Args:
            llm_response: LLM 的原始回复文本

        Returns:
            Tuple[ActionCommand, str]: (动作命令, 纯文本内容)
            如果解析失败，返回 (None, 原始文本)
        """
        if not llm_response:
            return None, ""

        # 尝试匹配 JSON 块
        json_match = cls.JSON_BLOCK_PATTERN.search(llm_response)

        if json_match:
            json_str = json_match.group()
            try:
                data = json.loads(json_str)

                # 验证必须包含 text 字段
                if "text" not in data:
                    logger.bind(tag=TAG).warning(f"JSON 缺少 text 字段: {json_str}")
                    return None, llm_response

                # 创建动作命令
                action_cmd = cls._create_action_command(data)
                text = data.get("text", "")

                logger.bind(tag=TAG).info(
                    f"解析动作: motion={action_cmd.motion.value}, "
                    f"emotion={action_cmd.emotion.value}, led={action_cmd.led}"
                )

                return action_cmd, text

            except json.JSONDecodeError as e:
                logger.bind(tag=TAG).warning(f"JSON 解析失败: {e}, 内容: {json_str}")
                return None, llm_response

        # 没有找到 JSON，返回原始文本
        logger.bind(tag=TAG).debug("未找到 JSON 动作块，使用默认动作")
        return cls._create_default_command(llm_response), llm_response

    @classmethod
    def _create_action_command(cls, data: dict) -> ActionCommand:
        """从解析的数据创建动作命令"""
        # 安全获取 motion
        motion_str = data.get("motion", "neutral")
        try:
            motion = Motion(motion_str)
        except ValueError:
            logger.bind(tag=TAG).warning(f"未知动作: {motion_str}，使用默认")
            motion = Motion.NEUTRAL

        # 安全获取 emotion
        emotion_str = data.get("emotion", "neutral")
        try:
            emotion = Emotion(emotion_str)
        except ValueError:
            logger.bind(tag=TAG).warning(f"未知表情: {emotion_str}，使用默认")
            emotion = Emotion.NEUTRAL

        # LED 灯效
        led = data.get("led", "breathing_cyan")

        return ActionCommand(
            text=data.get("text", ""),
            motion=motion,
            emotion=emotion,
            led=led
        )

    @classmethod
    def _create_default_command(cls, text: str) -> ActionCommand:
        """创建默认动作命令"""
        return ActionCommand(
            text=text,
            motion=Motion.NEUTRAL,
            emotion=Emotion.NEUTRAL,
            led="breathing_cyan"
        )

    @classmethod
    def extract_text_only(cls, llm_response: str) -> str:
        """
        只提取文本内容，移除 JSON 块

        Args:
            llm_response: LLM 的原始回复文本

        Returns:
            str: 纯文本内容
        """
        action_cmd, text = cls.parse(llm_response)
        return text if text else llm_response
