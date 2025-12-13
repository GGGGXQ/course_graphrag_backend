import os
import config
import sys
from enum import StrEnum
import logging
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from dataclasses import dataclass

LOG_LEVEL = config.LOG_LEVEL


this_module = sys.modules[__name__]

# 日志级别
CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

ROOT_PATH = os.path.dirname(os.path.abspath(__name__))
DEFAULT_LOG_DIR = os.path.join(ROOT_PATH, "runtime", "kownledge_graph_log")


class ELogFileType(StrEnum):
    TimedRotating = "TimedRotating"
    SizeRotating = "SizeRotating"
    NormalFile = "NormalFile"


@dataclass
class LogConfig:
    name: str
    is_save_to_file: bool = True
    is_output_to_stream: bool = True
    level: str | int = "info"
    file_type: ELogFileType = ELogFileType.NormalFile
    log_dirname: str | None = DEFAULT_LOG_DIR

    # 当file_type为TimedRotating时有效
    # 间隔单位
    when: str = "D"
    # 间隔时间
    interval: int = 1

    # 当file_type为SizeRotating时有效
    # 文件大小
    max_bytes: int = 1024 * 1024 * 1024  # 1G

    # 当file_type为TimedRotating和SizeRotating时有效, 备份文件数量
    backup_count: int = 10

    def __post_init__(self):
        if isinstance(self.level, int) and self.level in [0, 10, 20, 30, 40, 50]:
            pass
        elif isinstance(self.level, str):
            if self.level.isdigit():
                self.level = int(self.level)
            elif self.level.isalpha():
                self.level = getattr(this_module, self.level.upper())
        else:
            raise AttributeError()


class LogHandler(logging.Logger):
    """
    LogHandler
    """

    def __init__(
        self,
        log_config: LogConfig,
    ):
        if isinstance(log_config.file_type, str):
            log_config.file_type = ELogFileType(log_config.file_type)

        self.log_config = log_config
        self.name = log_config.name
        self.level = log_config.level

        # 日志文件夹初始化
        self.log_dirname = (
            self.log_config.log_dirname
            if self.log_config.log_dirname
            else DEFAULT_LOG_DIR
        )
        if self.log_dirname:
            if not os.path.exists(self.log_dirname):
                os.makedirs(self.log_dirname)

        logging.Logger.__init__(self, self.name, level=self.level)
        if self.log_config.is_output_to_stream:
            self.__setStreamHandler__()
        if self.log_config.is_save_to_file:
            self.__setFileHandler__()

    def __setFileHandler__(self):
        """
        set file handler
        :param level:
        :return:
        """
        encoding = "utf-8"
        file_name = os.path.join(self.log_dirname, "{name}.log".format(name=self.name))
        if self.log_config.file_type == ELogFileType.TimedRotating:
            file_handler = TimedRotatingFileHandler(
                filename=file_name,
                when=self.log_config.when,
                interval=self.log_config.interval,
                backupCount=self.log_config.backup_count,
                encoding=encoding,
            )
            file_handler.suffix = "%Y%m%d"

        elif self.log_config.file_type == ELogFileType.SizeRotating:
            # 最大1G
            file_handler = RotatingFileHandler(
                filename=file_name,
                maxBytes=self.log_config.max_bytes,
                backupCount=self.log_config.backup_count,
                encoding=encoding,
            )
            # file_handler.suffix = '%Y%m%d'
        elif self.log_config.file_type == ELogFileType.NormalFile:
            file_handler = logging.FileHandler(filename=file_name, encoding=encoding)
        else:
            raise AttributeError("file_type error")

        file_handler.setLevel(self.level)

        formatter = logging.Formatter(
            "%(asctime)s %(filename)s-%(process)d-[line:%(lineno)d] %(levelname)s  %(message)s"  # noqa
        )

        file_handler.setFormatter(formatter)
        self.file_handler = file_handler
        self.addHandler(file_handler)

    def __setStreamHandler__(self):
        """
        set stream handler
        :param level:
        :return:
        """
        stream_handler = logging.StreamHandler()
        # formatter = logging.Formatter(
        #     "%(asctime)s %(filename)s-%(process)d-[line:%(lineno)d] %(levelname)s  %(message)s"  # noqa
        # )
        formatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s")
        stream_handler.setFormatter(formatter)

        stream_handler.setLevel(self.log_config.level)

        self.addHandler(stream_handler)

    def resetName(self, name):
        """
        reset name
        :param name:
        :return:
        """
        self.log_config.name = self.name = name
        self.removeHandler(self.file_handler)
        self.__setFileHandler__()


log_config = LogConfig(
    name="course_graphrag",
    level=LOG_LEVEL,
    file_type=ELogFileType.TimedRotating,
    when="W0",
    interval=1,
    backup_count=30,
)

logger = LogHandler(log_config=log_config)


# stream_chunk_log_config = LogConfig(
#     name="stream_chunk",
#     level=LOG_LEVEL,
#     file_type=ELogFileType.SizeRotating,
#     backup_count=2,
#     max_bytes=100 * 1024 * 1024,
# )


# stream_chunk_logger = LogHandler(log_config=stream_chunk_log_config)
