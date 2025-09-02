import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytz
from app.core.config import settings
from app.core.event import eventmanager
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType, NotificationType
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


class EmptyFileCleaner(_PluginBase):
    # 插件名称
    plugin_name = "空文件清理器"
    # 插件描述
    plugin_desc = "自动删除指定目录下的空文件（包括子目录），支持排除指定目录"
    # 插件图标
    plugin_icon = "delete.jpg"
    # 插件版本
    plugin_version = "1.0.0"
    # 插件作者
    plugin_author = "assistant"
    # 作者主页
    author_url = "https://github.com/assistant"
    # 插件配置项ID前缀
    plugin_config_prefix = "emptyfilecleaner_"
    # 加载顺序
    plugin_order = 10
    # 可使用的用户级别
    auth_level = 1

    def __init__(self):
        super().__init__()
        self._enabled = False
        self._onlyonce = False
        self._cron = ""
        self._target_dirs = ""
        self._exclude_dirs = ""
        self._min_size = 0
        self._include_empty_dirs = False
        self._notify = True
        self._dry_run = False
        self._scheduler: Optional[BackgroundScheduler] = None

    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled", False)
            self._onlyonce = config.get("onlyonce", False)
            self._cron = config.get("cron", "0 2 * * *")
            self._target_dirs = config.get("target_dirs", "")
            self._exclude_dirs = config.get("exclude_dirs", "")
            self._min_size = int(config.get("min_size", 0))
            self._include_empty_dirs = config.get("include_empty_dirs", False)
            self._notify = config.get("notify", True)
            self._dry_run = config.get("dry_run", False)

        # 停止现有的定时任务
        self.stop_service()

        # 启动定时任务
        if self._enabled:
            if self._onlyonce:
                self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                logger.info("空文件清理器启动，立即运行一次")
                self._scheduler.add_job(
                    func=self.clean_empty_files,
                    trigger="date",
                    run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                )
                # 关闭一次性开关
                self._onlyonce = False
                self.update_config({
                    "onlyonce": False,
                    "enabled": self._enabled,
                    "cron": self._cron,
                    "target_dirs": self._target_dirs,
                    "exclude_dirs": self._exclude_dirs,
                    "min_size": self._min_size,
                    "include_empty_dirs": self._include_empty_dirs,
                    "notify": self._notify,
                    "dry_run": self._dry_run
                })
                # 启动服务
                if self._scheduler.get_jobs():
                    self._scheduler.print_jobs()
                    self._scheduler.start()
            elif self._cron:
                try:
                    self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                    trigger = CronTrigger.from_crontab(self._cron, timezone=settings.TZ)
                    self._scheduler.add_job(
                        func=self.clean_empty_files,
                        trigger=trigger,
                        id="EmptyFileCleaner",
                        name="空文件清理器"
                    )
                    logger.info(f"空文件清理器定时任务启动，执行周期：{self._cron}")
                    if self._scheduler.get_jobs():
                        self._scheduler.print_jobs()
                        self._scheduler.start()
                except Exception as e:
                    logger.error(f"启动空文件清理器定时任务失败：{e}")

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """
        定义远程控制命令
        :return: 命令关键字、事件、描述、附加数据
        """
        return [{
            "cmd": "/clean_empty_files",
            "event": EventType.PluginAction,
            "desc": "空文件清理",
            "category": "清理",
            "data": {
                "action": "clean_empty_files"
            }
        }]

    def get_api(self) -> List[Dict[str, Any]]:
        return [{
            "path": "/clean_empty_files",
            "endpoint": self.clean_empty_files,
            "methods": ["GET"],
            "summary": "清理空文件",
            "description": "立即执行空文件清理任务",
        }]

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'onlyonce',
                                            'label': '立即运行一次',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'notify',
                                            'label': '发送通知',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'cron',
                                            'label': '执行周期',
                                            'placeholder': '0 2 * * *'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'min_size',
                                            'label': '最小文件大小(字节)',
                                            'placeholder': '0',
                                            'type': 'number'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'target_dirs',
                                            'label': '目标目录',
                                            'rows': 3,
                                            'placeholder': '每行一个目录路径，如：\n/downloads\n/media/movies'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'exclude_dirs',
                                            'label': '排除目录',
                                            'rows': 3,
                                            'placeholder': '每行一个目录路径，这些目录本身不会被删除，但会检查其子文件'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'include_empty_dirs',
                                            'label': '删除空目录',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'dry_run',
                                            'label': '测试模式（不实际删除）',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'tonal',
                                            'text': '注意：空文件清理存在风险，建议先开启测试模式确认要删除的文件，然后再执行实际删除。排除目录本身不会被删除，但会检查其中的空文件。'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "onlyonce": False,
            "cron": "0 2 * * *",
            "target_dirs": "",
            "exclude_dirs": "",
            "min_size": 0,
            "include_empty_dirs": False,
            "notify": True,
            "dry_run": False
        }

    def get_page(self) -> List[dict]:
        """
        拼装插件详情页面，需要返回页面配置，同时获取数据
        """
        return [
            {
                'component': 'VRow',
                'content': [
                    {
                        'component': 'VCol',
                        'props': {
                            'cols': 12
                        },
                        'content': [
                            {
                                'component': 'VCard',
                                'content': [
                                    {
                                        'component': 'VCardText',
                                        'props': {
                                            'class': 'pa-4'
                                        },
                                        'content': [
                                            {
                                                'component': 'VBtn',
                                                'props': {
                                                    'color': 'primary',
                                                    'size': 'large',
                                                    'variant': 'elevated'
                                                },
                                                'content': [
                                                    '立即清理'
                                                ],
                                                'events': {
                                                    'click': {
                                                        'api': 'plugin/EmptyFileCleaner/clean_empty_files',
                                                        'method': 'get'
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]

    @eventmanager.register(EventType.PluginAction)
    def remote_action(self, event):
        """
        远程控制响应
        """
        if event:
            event_data = event.event_data
            if not event_data or event_data.get("action") != "clean_empty_files":
                return
            self.post_message(channel=event_data.get("channel"),
                            title="开始执行空文件清理任务",
                            userid=event_data.get("user"))
            self.clean_empty_files()

    def clean_empty_files(self):
        """
        清理空文件的主要方法
        """
        if not self._target_dirs.strip():
            logger.warning("未配置目标目录")
            return

        logger.info("开始执行空文件清理任务")
        cleaned_files = []
        cleaned_dirs = []
        total_size_saved = 0

        # 解析目标目录
        target_directories = [Path(line.strip()) for line in self._target_dirs.strip().split('\n') if line.strip()]
        
        # 解析排除目录
        exclude_directories = []
        if self._exclude_dirs.strip():
            exclude_directories = [Path(line.strip()) for line in self._exclude_dirs.strip().split('\n') if line.strip()]

        try:
            for target_dir in target_directories:
                if not target_dir.exists():
                    logger.warning(f"目标目录不存在：{target_dir}")
                    continue

                logger.info(f"开始扫描目录：{target_dir}")
                
                # 先清理文件，再清理目录
                file_count, file_size = self._clean_files_in_directory(target_dir, exclude_directories)
                cleaned_files.extend(file_count)
                total_size_saved += file_size

                # 如果需要清理空目录
                if self._include_empty_dirs:
                    dir_count = self._clean_empty_directories(target_dir, exclude_directories)
                    cleaned_dirs.extend(dir_count)

            # 输出统计信息
            summary = f"清理完成！"
            if cleaned_files:
                summary += f"\n删除空文件 {len(cleaned_files)} 个，释放空间 {self._format_size(total_size_saved)}"
            if cleaned_dirs:
                summary += f"\n删除空目录 {len(cleaned_dirs)} 个"
            
            if not cleaned_files and not cleaned_dirs:
                summary += "\n未发现需要清理的空文件或空目录"

            logger.info(summary)

            # 发送通知
            if self._notify:
                self.post_message(
                    mtype=NotificationType.SiteMessage,
                    title="【空文件清理任务完成】",
                    text=summary
                )

        except Exception as e:
            error_msg = f"空文件清理任务执行失败：{str(e)}"
            logger.error(error_msg)
            if self._notify:
                self.post_message(
                    mtype=NotificationType.SiteMessage,
                    title="【空文件清理任务失败】",
                    text=error_msg
                )

    def _clean_files_in_directory(self, directory: Path, exclude_dirs: List[Path]) -> Tuple[List[str], int]:
        """
        清理目录中的空文件
        """
        cleaned_files = []
        total_size = 0

        try:
            for root, dirs, files in os.walk(directory):
                current_path = Path(root)
                
                for file in files:
                    file_path = current_path / file
                    try:
                        # 检查文件大小
                        file_size = file_path.stat().st_size
                        if file_size <= self._min_size:
                            if self._dry_run:
                                logger.info(f"[测试模式] 将删除空文件：{file_path}")
                                cleaned_files.append(str(file_path))
                                total_size += file_size
                            else:
                                logger.info(f"删除空文件：{file_path}")
                                file_path.unlink()
                                cleaned_files.append(str(file_path))
                                total_size += file_size
                    except Exception as e:
                        logger.warning(f"处理文件 {file_path} 时出错：{e}")

        except Exception as e:
            logger.error(f"扫描目录 {directory} 时出错：{e}")

        return cleaned_files, total_size

    def _clean_empty_directories(self, directory: Path, exclude_dirs: List[Path]) -> List[str]:
        """
        清理空目录（从最深层开始）
        """
        cleaned_dirs = []

        try:
            # 获取所有子目录，按深度排序（深的在前）
            all_dirs = []
            for root, dirs, files in os.walk(directory):
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    all_dirs.append(dir_path)
            
            # 按路径深度排序，深的在前
            all_dirs.sort(key=lambda x: len(x.parts), reverse=True)

            for dir_path in all_dirs:
                try:
                    # 检查是否是排除目录
                    if any(self._is_subdirectory_or_same(dir_path, exclude_dir) for exclude_dir in exclude_dirs):
                        logger.debug(f"跳过排除目录：{dir_path}")
                        continue

                    # 检查目录是否为空
                    if self._is_directory_empty(dir_path):
                        if self._dry_run:
                            logger.info(f"[测试模式] 将删除空目录：{dir_path}")
                            cleaned_dirs.append(str(dir_path))
                        else:
                            logger.info(f"删除空目录：{dir_path}")
                            dir_path.rmdir()
                            cleaned_dirs.append(str(dir_path))
                except Exception as e:
                    logger.warning(f"处理目录 {dir_path} 时出错：{e}")

        except Exception as e:
            logger.error(f"清理空目录时出错：{e}")

        return cleaned_dirs

    def _is_directory_empty(self, directory: Path) -> bool:
        """
        检查目录是否为空
        """
        try:
            return not any(directory.iterdir())
        except Exception:
            return False

    def _is_subdirectory_or_same(self, path: Path, parent: Path) -> bool:
        """
        检查path是否是parent的子目录或相同目录
        """
        try:
            path.resolve().relative_to(parent.resolve())
            return True
        except ValueError:
            return False

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """
        格式化文件大小
        """
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.2f} {units[unit_index]}"

    def stop_service(self):
        """
        退出插件
        """
        try:
            if self._scheduler:
                self._scheduler.remove_all_jobs()
                if self._scheduler.running:
                    self._scheduler.shutdown()
                self._scheduler = None
        except Exception as e:
            logger.error(f"停止空文件清理器服务失败：{e}")
