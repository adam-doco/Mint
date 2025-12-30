import asyncio
from aiohttp import web
from config.logger import setup_logging
from core.api.ota_handler import OTAHandler
from core.api.vision_handler import VisionHandler
from core.api.hardware_handler import HardwareHandler

TAG = __name__


class SimpleHttpServer:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging()
        self.ota_handler = OTAHandler(config)
        self.vision_handler = VisionHandler(config)
        self.hardware_handler = HardwareHandler(config)

    def _get_websocket_url(self, local_ip: str, port: int) -> str:
        """获取websocket地址

        Args:
            local_ip: 本地IP地址
            port: 端口号

        Returns:
            str: websocket地址
        """
        server_config = self.config["server"]
        websocket_config = server_config.get("websocket")

        if websocket_config and "你" not in websocket_config:
            return websocket_config
        else:
            return f"ws://{local_ip}:{port}/xiaozhi/v1/"

    async def start(self):
        try:
            server_config = self.config["server"]
            read_config_from_api = self.config.get("read_config_from_api", False)
            host = server_config.get("ip", "0.0.0.0")
            port = int(server_config.get("http_port", 8003))

            if port:
                app = web.Application()

                if not read_config_from_api:
                    # 如果没有开启智控台，只是单模块运行，就需要再添加简单OTA接口，用于下发websocket接口
                    app.add_routes(
                        [
                            web.get("/xiaozhi/ota/", self.ota_handler.handle_get),
                            web.post("/xiaozhi/ota/", self.ota_handler.handle_post),
                            web.options(
                                "/xiaozhi/ota/", self.ota_handler.handle_options
                            ),
                            # 下载接口，仅提供 data/bin/*.bin 下载
                            web.get(
                                "/xiaozhi/ota/download/{filename}",
                                self.ota_handler.handle_download,
                            ),
                            web.options(
                                "/xiaozhi/ota/download/{filename}",
                                self.ota_handler.handle_options,
                            ),
                        ]
                    )
                # 添加路由
                app.add_routes(
                    [
                        web.get("/mcp/vision/explain", self.vision_handler.handle_get),
                        web.post(
                            "/mcp/vision/explain", self.vision_handler.handle_post
                        ),
                        web.options(
                            "/mcp/vision/explain", self.vision_handler.handle_options
                        ),
                    ]
                )

                # 硬件控制 API 路由 (供 Dify 调用)
                app.add_routes(
                    [
                        # 设备列表
                        web.get("/api/v1/devices", self.hardware_handler.handle_devices),
                        web.options("/api/v1/devices", self.hardware_handler.handle_options),
                        # 音量控制
                        web.post("/api/v1/volume", self.hardware_handler.handle_volume),
                        web.options("/api/v1/volume", self.hardware_handler.handle_options),
                        # 屏幕亮度
                        web.post("/api/v1/brightness", self.hardware_handler.handle_brightness),
                        web.options("/api/v1/brightness", self.hardware_handler.handle_options),
                        # 屏幕开关
                        web.post("/api/v1/screen/power", self.hardware_handler.handle_screen_power),
                        web.options("/api/v1/screen/power", self.hardware_handler.handle_options),
                        # 动作控制
                        web.post("/api/v1/motion", self.hardware_handler.handle_motion),
                        web.options("/api/v1/motion", self.hardware_handler.handle_options),
                        # 表情控制
                        web.post("/api/v1/emotion", self.hardware_handler.handle_emotion),
                        web.options("/api/v1/emotion", self.hardware_handler.handle_options),
                        # LED 灯效
                        web.post("/api/v1/led", self.hardware_handler.handle_led),
                        web.options("/api/v1/led", self.hardware_handler.handle_options),
                        # LED 自定义颜色
                        web.post("/api/v1/led/color", self.hardware_handler.handle_led_color),
                        web.options("/api/v1/led/color", self.hardware_handler.handle_options),
                    ]
                )

                # 运行服务
                runner = web.AppRunner(app)
                await runner.setup()
                site = web.TCPSite(runner, host, port)
                await site.start()

                # 保持服务运行
                while True:
                    await asyncio.sleep(3600)  # 每隔 1 小时检查一次
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"HTTP服务器启动失败: {e}")
            import traceback

            self.logger.bind(tag=TAG).error(f"错误堆栈: {traceback.format_exc()}")
            raise
