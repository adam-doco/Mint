"""
米特(Mint) 舵机动作控制插件
让 AI 可以控制米特的头部动作
"""

import asyncio
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from core.hardware.action_protocol import Motion

# 动作描述映射，用于生成自然语言回复
MOTION_DESCRIPTIONS = {
    "neutral": "回正姿势",
    "nod": "点头",
    "shake": "摇头",
    "tilt_left": "向左歪头",
    "tilt_right": "向右歪头",
    "look_up": "抬头",
    "look_down": "低头",
    "look_left": "向左看",
    "look_right": "向右看",
    "excited": "兴奋地抖动",
    "shy": "害羞",
    "greeting": "打招呼",
}

mint_motion_function_desc = {
    "type": "function",
    "function": {
        "name": "mint_motion",
        "description": (
            "控制米特的头部动作。可以让米特点头、摇头、歪头、抬头、低头、向左右看等。"
            "当用户要求米特做动作，或者在对话中需要配合肢体语言时使用。"
            "例如：'点点头'、'摇摇头'、'看看我'、'打个招呼'等。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "motion": {
                    "type": "string",
                    "description": "动作类型",
                    "enum": [
                        "neutral",      # 回正
                        "nod",          # 点头
                        "shake",        # 摇头
                        "tilt_left",    # 左歪头
                        "tilt_right",   # 右歪头
                        "look_up",      # 抬头
                        "look_down",    # 低头
                        "look_left",    # 向左看
                        "look_right",   # 向右看
                        "excited",      # 兴奋抖动
                        "shy",          # 害羞
                        "greeting",     # 打招呼
                    ],
                },
                "speed": {
                    "type": "string",
                    "description": "动作速度：slow(慢)、normal(正常)、fast(快)",
                    "enum": ["slow", "normal", "fast"],
                },
            },
            "required": ["motion"],
        },
    },
}


@register_function("mint_motion", mint_motion_function_desc, ToolType.IOT_CTL)
def mint_motion(conn, motion: str = "neutral", speed: str = "normal"):
    """
    控制米特的头部舵机动作

    Args:
        conn: 连接对象
        motion: 动作类型
        speed: 动作速度
    """
    try:
        # 获取 Motion 枚举值
        motion_enum = Motion(motion)

        # 通过 hardware_bridge 执行动作
        if hasattr(conn, 'hardware_bridge') and conn.hardware_bridge:
            # 使用 asyncio 执行异步方法
            asyncio.create_task(
                conn.hardware_bridge.execute_motion(motion_enum, speed)
            )

            motion_desc = MOTION_DESCRIPTIONS.get(motion, motion)
            return ActionResponse(
                Action.RESPONSE,
                None,
                f"好的，我{motion_desc}给你看"
            )
        else:
            return ActionResponse(
                Action.RESPONSE,
                None,
                "抱歉，我的身体控制系统还没准备好"
            )

    except ValueError:
        return ActionResponse(
            Action.RESPONSE,
            None,
            f"抱歉，我不会这个动作：{motion}"
        )
    except Exception as e:
        return ActionResponse(
            Action.ERROR,
            str(e),
            "执行动作时出错了"
        )
