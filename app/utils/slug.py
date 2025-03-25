import re
import unicodedata
from datetime import datetime

def generate_slug(text, max_length=50):
    """
    生成URL友好的slug
    
    参数:
        text (str): 要转换为slug的文本
        max_length (int): slug的最大长度
        
    返回:
        str: 生成的slug
    """
    # 转换为小写
    text = text.lower()
    
    # 将Unicode字符转换为ASCII
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    
    # 替换非字母数字字符为连字符
    text = re.sub(r'[^a-z0-9\-]', '-', text)
    
    # 替换多个连续连字符为单个连字符
    text = re.sub(r'-+', '-', text)
    
    # 移除开头和结尾的连字符
    text = text.strip('-')
    
    # 如果slug为空，使用当前时间戳
    if not text:
        text = f"tag-{int(datetime.now().timestamp())}"
    
    # 截断到最大长度
    return text[:max_length] 