import os
import tempfile
import pytest


@pytest.fixture
def db_path():
    """创建临时数据库文件路径，测试结束后自动清理"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass