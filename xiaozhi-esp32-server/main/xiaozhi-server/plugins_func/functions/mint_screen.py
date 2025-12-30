"""
米特(Mint) 屏幕控制插件
让 AI 可以控制米特的屏幕亮度等
"""

import json
import asyncio
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


mint_brightness_function_desc = {
    "type": "function",
    "function": {
        "name": "mint_brightness",
        "description": (
            "控制米特屏幕（眼睛）的亮度。可以设置具体亮度值，或者调亮、调暗。"
            "当用户要求调整屏幕亮度时使用，例如：'屏幕太亮了'、'把亮度调低一点'等。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "亮度操作类型",
                    "enum": ["set", "up", "down"],
                },
                "value": {
                    "type": "integer",
                    "description": "亮度值(0-100)，仅当action为set时需要",
                    "minimum": 0,
                    "maximum": 100,
                },
            },
            "required": ["action"],
        },
    },
}


@register_function("mint_brightness", mint_brightness_function_desc, ToolType.IOT_CTL)
def mint_brightness(conn, action: str = "set", value: int = 80):
    """
    控制米特的屏幕亮度

    Args:
        conn: 连接对象
        action: 操作类型 (set/up/down)
        value: 亮度值 (0-100)
    """
    try:
        # 构建 IoT 控制命令
        command = {
            "name": "Screen",
            "method": "",
            "parameters": {}
        }

        response_text = ""

        if action == "set":
            # 限制亮度范围
            value = max(0, min(100, value))
            command["method"] = "SetBrightness"
            command["parameters"]["brightness"] = value
            response_text = f"好的，屏幕亮度已调整到 {value}"

        elif action == "up":
            command["method"] = "BrightnessUp"
            response_text = "好的，屏幕已调亮"

        elif action == "down":
            command["method"] = "BrightnessDown"
            response_text = "好的，屏幕已调暗"

        else:
            return ActionResponse(
                Action.RESPONSE,
                None,
                f"不支持的亮度操作：{action}"
            )

        # 发送 IoT 命令到 ESP32
        if hasattr(conn, 'websocket') and conn.websocket:
            send_message = json.dumps({
                "type": "iot",
                "commands": [command]
            })

            asyncio.create_task(_send_command(conn.websocket, send_message))
            logger.bind(tag=TAG).info(f"屏幕亮度控制命令已发送: {command}")

            return ActionResponse(
                Action.RESPONSE,
                None,
                response_text
            )
        else:
            return ActionResponse(
                Action.RESPONSE,
                None,
                "抱歉，设备连接不可用"
            )

    except Exception as e:
        logger.bind(tag=TAG).error(f"屏幕亮度控制出错: {e}")
        return ActionResponse(
            Action.ERROR,
            str(e),
            "调整亮度时出错了"
        )


async def _send_command(websocket, message):
    """异步发送命令"""
    try:
        await websocket.send(message)
    except Exception as e:
        logger.bind(tag=TAG).error(f"发送命令失败: {e}")


# 屏幕开关控制
mint_screen_power_function_desc = {
    "type": "function",
    "function": {
        "name": "mint_screen_power",
        "description": (
            "控制米特屏幕（眼睛）的开关。"
            "当用户要求关闭或打开屏幕时使用，例如：'关闭屏幕'、'打开屏幕'、'闭上眼睛'等。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "power": {
                    "type": "string",
                    "description": "开关状态",
                    "enum": ["on", "off"],
                },
            },
            "required": ["power"],
        },
    },
}


@register_function("mint_screen_power", mint_screen_power_function_desc, ToolType.IOT_CTL)
def mint_screen_power(conn, power: str = "on"):
    """
    控制米特的屏幕开关

    Args:
        conn: 连接对象
        power: 开关状态 (on/off)
    """
    try:
        command = {
            "name": "Screen",
            "method": "TurnOn" if power == "on" else "TurnOff",
            "parameters": {}
        }

        response_text = "好的，屏幕已打开" if power == "on" else "好的，屏幕已关闭"

        # 发送 IoT 命令到 ESP32
        if hasattr(conn, 'websocket') and conn.websocket:
            send_message = json.dumps({
                "type": "iot",
                "commands": [command]
            })

            asyncio.create_task(_send_command(conn.websocket, send_message))
            logger.bind(tag=TAG).info(f"屏幕开关命令已发送: {command}")

            return ActionResponse(
                Action.RESPONSE,
                None,
                response_text
            )
        else:
            return ActionResponse(
                Action.RESPONSE,
                None,
                "抱歉，设备连接不可用"
            )

    except Exception as e:
        logger.bind(tag=TAG).error(f"屏幕开关控制出错: {e}")
        return ActionResponse(
            Action.ERROR,
            str(e),
            "控制屏幕时出错了"
        )
