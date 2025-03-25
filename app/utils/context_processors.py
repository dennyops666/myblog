"""上下文处理器模块

这个模块提供了一些上下文处理器函数，用于在模板中使用。
"""

from datetime import datetime

def utility_processor():
    """实用工具处理器
    
    返回一个包含实用工具函数的字典，这些函数可以在模板中使用。
    """
    def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
        """格式化日期时间
        
        Args:
            value: 要格式化的日期时间值
            format: 格式化字符串，默认为'%Y-%m-%d %H:%M:%S'
            
        Returns:
            格式化后的日期时间字符串
        """
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return value
        return value.strftime(format)

    return dict(format_datetime=format_datetime) 