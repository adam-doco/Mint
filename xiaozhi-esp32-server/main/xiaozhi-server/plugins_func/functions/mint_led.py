"""
米特(Mint) LED 灯效控制插件
让 AI 可以控制米特的 LED 灯光效果
"""

import asyncio
from plugins_func.register import register_function, ToolType, ActionResponse, Action

# 灯效描述映射
LED_EFFECT_DESCRIPTIONS = {
    "off": "关闭灯光",
    "breathing_white": "白色呼吸灯",
    "breathing_cyan": "青色呼吸灯",
    "breathing_blue": "蓝色呼吸灯",
    "breathing_pink": "粉色呼吸灯",
    "breathing_green": "绿色呼吸灯",
    "breathing_orange": "橙色呼吸灯",
    "pulse_blue": "蓝色脉冲",
    "pulse_green": "绿色脉冲",
    "pulse_red": "红色脉冲",
    "rainbow": "彩虹灯效",
    "spin_purple": "紫色旋转",
    "spin_cyan": "青色旋转",
    "blink_yellow": "黄色闪烁",
    "blink_red": "红色闪烁",
    "solid_white": "白色常亮",
    "solid_cyan": "青色常亮",
}

mint_led_function_desc = {
    "type": "function",
    "function": {
        "name": "mint_led",
        "description": (
            "控制米特的 LED 灯光效果。可以设置不同颜色的呼吸灯、脉冲、彩虹、旋转、闪烁等效果。"
            "当用户要求改变灯光、营造氛围、或者需要视觉反馈时使用。"
            "例如：'把灯变成蓝色'、'开彩虹灯'、'关灯'等。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "effect": {
                    "type": "string",
                    "description": "灯效名称",
                    "enum": [
                        "off",              # 关闭
                        "breathing_white",  # 白色呼吸
                        "breathing_cyan",   # 青色呼吸
                        "breathing_blue",   # 蓝色呼吸
                        "breathing_pink",   # 粉色呼吸
                        "breathing_green",  # 绿色呼吸
                        "breathing_orange", # 橙色呼吸
                        "pulse_blue",       # 蓝色脉冲
                        "pulse_green",      # 绿色脉冲
                        "pulse_red",        # 红色脉冲
                        "rainbow",          # 彩虹
                        "spin_purple",      # 紫色旋转
                        "spin_cyan",        # 青色旋转
                        "blink_yellow",     # 黄色闪烁
                        "blink_red",        # 红色闪烁
                        "solid_white",      # 白色常亮
                        "solid_cyan",       # 青色常亮
                    ],
                },
            },
            "required": ["effect"],
        },
    },
}


@register_function("mint_led", mint_led_function_desc, ToolType.IOT_CTL)
def mint_led(conn, effect: str = "breathing_cyan"):
    """
    控制米特的 LED 灯效

    Args:
        conn: 连接对象
        effect: 灯效名称
    """
    try:
        # 通过 hardware_bridge 设置灯效
        if hasattr(conn, 'hardware_bridge') and conn.hardware_bridge:
            asyncio.create_task(
                conn.hardware_bridge.set_led_effect(effect)
            )

            effect_desc = LED_EFFECT_DESCRIPTIONS.get(effect, effect)
            if effect == "off":
                return ActionResponse(
                    Action.RESPONSE,
                    None,
                    "好的，我把灯关掉了"
                )
            else:
                return ActionResponse(
                    Action.RESPONSE,
                    None,
                    f"好的，我切换到{effect_desc}"
                )
        else:
            return ActionResponse(
                Action.RESPONSE,
                None,
                "抱歉，我的灯光系统还没准备好"
            )

    except Exception as e:
        return ActionResponse(
            Action.ERROR,
            str(e),
            "设置灯效时出错了"
        )


# 额外提供一个自定义颜色的函数
mint_led_color_function_desc = {
    "type": "function",
    "function": {
        "name": "mint_led_color",
        "description": (
            "设置米特 LED 的自定义颜色。可以指定 RGB 值来设置任意颜色。"
            "当用户要求特定颜色但预设灯效中没有时使用。"
            "例如：'把灯变成紫色'、'我想要暖黄色的灯'等。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "r": {
                    "type": "integer",
                    "description": "红色分量 (0-255)",
                    "minimum": 0,
                    "maximum": 255,
                },
                "g": {
                    "type": "integer",
                    "description": "绿色分量 (0-255)",
                    "minimum": 0,
                    "maximum": 255,
                },
                "b": {
                    "type": "integer",
                    "description": "蓝色分量 (0-255)",
                    "minimum": 0,
                    "maximum": 255,
                },
                "mode": {
                    "type": "string",
                    "description": "灯光模式：solid(常亮)、breathing(呼吸)、pulse(脉冲)",
                    "enum": ["solid", "breathing", "pulse"],
                },
            },
            "required": ["r", "g", "b"],
        },
    },
}


@register_function("mint_led_color", mint_led_color_function_desc, ToolType.IOT_CTL)
def mint_led_color(conn, r: int = 0, g: int = 255, b: int = 255, mode: str = "breathing"):
    """
    设置米特 LED 的自定义颜色

    Args:
        conn: 连接对象
        r: 红色分量 (0-255)
        g: 绿色分量 (0-255)
        b: 蓝色分量 (0-255)
        mode: 灯光模式
    """
    try:
        # 限制 RGB 值范围
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))

        # 通过 hardware_bridge 设置颜色
        if hasattr(conn, 'hardware_bridge') and conn.hardware_bridge:
            asyncio.create_task(
                conn.hardware_bridge.set_led_color(r, g, b, mode)
            )

            mode_desc = {"solid": "常亮", "breathing": "呼吸", "pulse": "脉冲"}.get(mode, mode)
            return ActionResponse(
                Action.RESPONSE,
                None,
                f"好的，我把灯光设置成了 RGB({r},{g},{b}) {mode_desc}模式"
            )
        else:
            return ActionResponse(
                Action.RESPONSE,
                None,
                "抱歉，我的灯光系统还没准备好"
            )

    except Exception as e:
        return ActionResponse(
            Action.ERROR,
            str(e),
            "设置灯光颜色时出错了"
        )
