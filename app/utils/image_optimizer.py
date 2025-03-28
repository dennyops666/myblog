"""
文件名：image_optimizer.py
描述：图片优化工具类
作者：denny
"""

import os
from PIL import Image
from io import BytesIO
import logging
from typing import Tuple, Optional
from flask import current_app
from app.extensions import cache

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageOptimizer:
    """图片优化工具类"""
    
    # 默认配置
    DEFAULT_QUALITY = 85
    DEFAULT_FORMAT = 'JPEG'
    MAX_SIZE = (1920, 1080)  # 最大尺寸
    THUMBNAIL_SIZE = (300, 300)  # 缩略图尺寸
    
    # 缓存配置
    CACHE_TIMEOUT = 3600  # 1小时缓存过期时间
    
    @staticmethod
    def optimize_image(image_path: str, quality: int = DEFAULT_QUALITY,
                      max_size: Tuple[int, int] = MAX_SIZE,
                      output_format: str = DEFAULT_FORMAT) -> Optional[str]:
        """优化图片
        
        Args:
            image_path: 图片路径
            quality: 压缩质量（1-100）
            max_size: 最大尺寸
            output_format: 输出格式
            
        Returns:
            str: 优化后的图片路径
        """
        # 检查缓存
        cache_key = f'optimized_image:{image_path}:{quality}:{max_size}:{output_format}'
        cached_path = cache.get(cache_key)
        if cached_path and os.path.exists(cached_path):
            return cached_path
            
        try:
            # 检查文件是否存在
            if not os.path.exists(image_path):
                logger.error(f"图片不存在: {image_path}")
                return None
                
            # 打开图片
            with Image.open(image_path) as img:
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 调整尺寸
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # 生成优化后的文件名
                filename, ext = os.path.splitext(image_path)
                optimized_path = f"{filename}_optimized{ext}"
                
                # 保存优化后的图片
                img.save(optimized_path, 
                        format=output_format,
                        quality=quality,
                        optimize=True)
                
                # 缓存结果
                cache.set(cache_key, optimized_path, timeout=ImageOptimizer.CACHE_TIMEOUT)
                
                logger.info(f"图片优化成功: {optimized_path}")
                return optimized_path
                
        except Exception as e:
            logger.error(f"图片优化失败: {str(e)}")
            return None
    
    @staticmethod
    def create_thumbnail(image_path: str, size: Tuple[int, int] = THUMBNAIL_SIZE) -> Optional[str]:
        """创建缩略图
        
        Args:
            image_path: 图片路径
            size: 缩略图尺寸
            
        Returns:
            str: 缩略图路径
        """
        # 检查缓存
        cache_key = f'thumbnail:{image_path}:{size}'
        cached_path = cache.get(cache_key)
        if cached_path and os.path.exists(cached_path):
            return cached_path
            
        try:
            # 检查文件是否存在
            if not os.path.exists(image_path):
                logger.error(f"图片不存在: {image_path}")
                return None
                
            # 打开图片
            with Image.open(image_path) as img:
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 创建缩略图
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # 生成缩略图文件名
                filename, ext = os.path.splitext(image_path)
                thumbnail_path = f"{filename}_thumb{ext}"
                
                # 保存缩略图
                img.save(thumbnail_path, 
                        format=ImageOptimizer.DEFAULT_FORMAT,
                        quality=ImageOptimizer.DEFAULT_QUALITY,
                        optimize=True)
                
                # 缓存结果
                cache.set(cache_key, thumbnail_path, timeout=ImageOptimizer.CACHE_TIMEOUT)
                
                logger.info(f"缩略图创建成功: {thumbnail_path}")
                return thumbnail_path
                
        except Exception as e:
            logger.error(f"缩略图创建失败: {str(e)}")
            return None
    
    @staticmethod
    def get_image_info(image_path: str) -> Optional[dict]:
        """获取图片信息
        
        Args:
            image_path: 图片路径
            
        Returns:
            dict: 图片信息
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(image_path):
                logger.error(f"图片不存在: {image_path}")
                return None
                
            # 打开图片
            with Image.open(image_path) as img:
                return {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height
                }
                
        except Exception as e:
            logger.error(f"获取图片信息失败: {str(e)}")
            return None
    
    @staticmethod
    def is_valid_image(file) -> bool:
        """检查是否为有效的图片文件
        
        Args:
            file: 文件对象
            
        Returns:
            bool: 是否为有效的图片
        """
        try:
            Image.open(file).verify()
            return True
        except Exception:
            return False
    
    @staticmethod
    def optimize_for_web(image_path: str) -> Optional[BytesIO]:
        """优化图片用于Web显示
        
        Args:
            image_path: 图片路径
            
        Returns:
            BytesIO: 优化后的图片数据
        """
        # 检查缓存
        cache_key = f'web_optimized:{image_path}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return BytesIO(cached_data)
            
        try:
            # 检查文件是否存在
            if not os.path.exists(image_path):
                logger.error(f"图片不存在: {image_path}")
                return None
                
            # 打开图片
            with Image.open(image_path) as img:
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 调整尺寸
                if img.size[0] > ImageOptimizer.MAX_SIZE[0] or \
                   img.size[1] > ImageOptimizer.MAX_SIZE[1]:
                    img.thumbnail(ImageOptimizer.MAX_SIZE, 
                                Image.Resampling.LANCZOS)
                
                # 创建内存缓冲区
                buffer = BytesIO()
                
                # 保存优化后的图片到缓冲区
                img.save(buffer,
                        format=ImageOptimizer.DEFAULT_FORMAT,
                        quality=ImageOptimizer.DEFAULT_QUALITY,
                        optimize=True)
                
                # 缓存结果
                buffer.seek(0)
                cache.set(cache_key, buffer.getvalue(), timeout=ImageOptimizer.CACHE_TIMEOUT)
                
                # 将指针移到开始位置
                buffer.seek(0)
                return buffer
                
        except Exception as e:
            logger.error(f"Web图片优化失败: {str(e)}")
            return None 