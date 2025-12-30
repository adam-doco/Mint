"""
米特(Mint) 表情控制插件
让 AI 可以控制米特的眼睛表情
"""

import asyncio
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from core.hardware.action_protocol import Emotion

# 表情描述映射
EMOTION_DESCRIPTIONS = {
    "neutral": "正常表情",
    "happy": "开心的表情",
    "sad": "难过的表情",
    "angry": "生气的表情",
    "surprised": "惊讶的表情",
    "sleepy": "困倦的表情",
    "thinking": "思考的表情",
    "love": "爱心眼",
    "doubt": "怀疑的表情",
    "scared": "害怕的表情",
    "proud": "得意的表情",
    "speechless": "无语的表情",
}

mint_emotion_function_desc = {
    "type": "function",
    "function": {
        "name": "mint_emotion",
        "description": (
            "控制米特的眼睛表情。可以让米特显示开心、难过、生气、惊讶等各种表情。"
            "当对话中需要表达情感时使用，例如用户说了有趣的事就显示开心，"
            "用户说了难过的事就显示难过。也可以用户直接要求改变表情。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "emotion": {
                    "type": "string",
                    "description": "表情类型",
                    "enum": [
                        "neutral",      # 正常
                        "happy",        # 开心
                        "sad",          # 难过
                        "angry",        # 生气
                        "surprised",    # 惊讶
                        "sleepy",       # 困倦
                        "thinking",     # 思考
                        "love",         # 爱心
                        "doubt",        # 怀疑
                        "scared",       # 害怕
                        "proud",        # 得意
                        "speechless",   # 无语
                    ],
                },
            },
            "required": ["emotion"],
        },
    },
}


@register_function("mint_emotion", mint_emotion_function_desc, ToolType.IOT_CTL)
def mint_emotion(conn, emotion: str = "neutral"):
    """
    控制米特的眼睛表情

    Args:
        conn: 连接对象
        emotion: 表情类型
    """
    try:
        # 获取 Emotion 枚举值
        emotion_enum = Emotion(emotion)

        # 通过 hardware_bridge 设置表情
        if hasattr(conn, 'hardware_bridge') and conn.hardware_bridge:
            asyncio.create_task(
                conn.hardware_bridge.set_emotion(emotion_enum)
            )

            emotion_desc = EMOTION_DESCRIPTIONS.get(emotion, emotion)
            return ActionResponse(
                Action.RESPONSE,
                None,
                f"好的，我换上{emotion_desc}"
            )
        else:
            return ActionResponse(
                Action.RESPONSE,
                None,
                "抱歉，我的表情系统还没准备好"
            )

    except ValueError:
        return ActionResponse(
            Action.RESPONSE,
            None,
            f"抱歉，我不会这个表情：{emotion}"
        )
    except Exception as e:
        return ActionResponse(
            Action.ERROR,
            str(e),
            "设置表情时出错了"
        )
