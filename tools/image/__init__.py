"""
图片工具模块
- 压缩
- 格式转换
- 水印
"""
from .compress import ImageCompressPage
from .convert import ImageConvertPage
from .watermark import ImageWatermarkPage

__all__ = [
    'ImageCompressPage',
    'ImageConvertPage',
    'ImageWatermarkPage'
]
