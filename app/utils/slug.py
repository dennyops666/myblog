import re
from unidecode import unidecode

def generate_slug(text):
    """
    生成 URL 友好的 slug
    :param text: 原始文本
    :return: URL 友好的 slug
    """
    # 移除中文字符，转换为拼音或空字符串
    text = unidecode(text)
    
    # 转换为小写
    text = text.lower()
    
    # 将非字母数字字符替换为连字符
    text = re.sub(r'[^a-z0-9]+', '-', text)
    
    # 移除首尾的连字符
    text = text.strip('-')
    
    # 将多个连字符替换为单个连字符
    text = re.sub(r'-+', '-', text)
    
    return text 