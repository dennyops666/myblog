from typing import Any, Dict, List, Optional, Union
from flask import jsonify, current_app
from sqlalchemy import inspect
from sqlalchemy.orm import Query

class ApiResponse:
    """API 响应工具类，用于统一格式化 API 响应"""
    
    @staticmethod
    def _serialize_model(model: Any, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
        """SQLAlchemy 模型序列化"""
        if hasattr(model, 'to_dict'):
            return model.to_dict() if not exclude else {
                k: v for k, v in model.to_dict().items()
                if k not in (exclude or [])
            }
        
        data = {c.key: getattr(model, c.key)
                for c in inspect(model).mapper.column_attrs
                if not exclude or c.key not in exclude}
        
        # 处理日期时间类型
        for key, value in data.items():
            if hasattr(value, 'isoformat'):
                data[key] = value.isoformat()
        
        return data
    
    @classmethod
    def _serialize_data(cls, data: Any, exclude: Optional[List[str]] = None) -> Any:
        """API 响应数据序列化"""
        if hasattr(data, '__iter__') and not isinstance(data, (str, bytes, dict)):
            return [cls._serialize_model(item, exclude) if hasattr(item, '__table__') else item
                    for item in data]
        elif hasattr(data, '__table__'):
            return cls._serialize_model(data, exclude)
        elif isinstance(data, dict):
            return {k: cls._serialize_data(v, exclude) for k, v in data.items()}
        return data
    
    @classmethod
    def paginate(
        cls,
        query: Query,
        page: int = 1,
        per_page: int = 10,
        error_out: bool = True,
        exclude: Optional[List[str]] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """SQLAlchemy 查询分页响应"""
        if error_out and page < 1:
            return cls.bad_request('页码必须大于0')
        
        if error_out and per_page < 1:
            return cls.bad_request('每页数量必须大于0')
        
        items = query.limit(per_page).offset((page - 1) * per_page).all()
        total = query.order_by(None).count()
        pages = (total + per_page - 1) // per_page
        
        response = {
            'items': cls._serialize_data(items, exclude),
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages,
                'has_prev': page > 1,
                'has_next': page < pages,
                'current': page,
                'first': 1,
                'last': pages,
                'prev': page - 1 if page > 1 else None,
                'next': page + 1 if page < pages else None
            }
        }
        
        if extra_data:
            response.update(extra_data)
        
        return cls.success(response)
    
    @classmethod
    def list_response(
        cls,
        items: List[Any],
        total: Optional[int] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        exclude: Optional[List[str]] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """API 列表响应"""
        response = {
            'items': cls._serialize_data(items, exclude)
        }
        
        if all(x is not None for x in (total, page, per_page)):
            pages = (total + per_page - 1) // per_page
            response['pagination'] = {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages,
                'has_prev': page > 1,
                'has_next': page < pages,
                'current': page,
                'first': 1,
                'last': pages,
                'prev': page - 1 if page > 1 else None,
                'next': page + 1 if page < pages else None
            }
        
        if extra_data:
            response.update(extra_data)
        
        if meta:
            response['meta'] = meta
        
        return cls.success(response)
    
    @classmethod
    def tree_response(
        cls,
        items: List[Dict[str, Any]],
        id_field: str = 'id',
        parent_field: str = 'parent_id',
        children_field: str = 'children',
        root_value: Any = None
    ) -> Dict[str, Any]:
        """API 树形结构响应"""
        def build_tree(items, parent_value=root_value):
            nodes = []
            for item in items:
                if item[parent_field] == parent_value:
                    children = build_tree(items, item[id_field])
                    if children:
                        item[children_field] = children
                    nodes.append(item)
            return nodes
        
        return cls.success({
            'items': build_tree(items)
        })
    
    @classmethod
    def download_response(
        cls,
        filename: str,
        content_type: str = 'application/octet-stream',
        download_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """API 文件下载响应"""
        return cls.success({
            'download': {
                'filename': filename,
                'content_type': content_type,
                'download_name': download_name or filename
            }
        })
    
    @staticmethod
    def _build_response(
        success: bool,
        message: str,
        data: Optional[Any] = None,
        error_code: Optional[int] = None,
        error_details: Optional[Union[str, Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """构建基础响应"""
        response = {
            'success': success,
            'message': message
        }
        
        if data is not None:
            response['data'] = data
            
        if error_code is not None:
            response['error_code'] = error_code
            
        if error_details is not None and current_app.debug:
            response['error_details'] = error_details
            
        response.update(kwargs)
        return response
    
    @classmethod
    def success(
        cls,
        data: Optional[Any] = None,
        message: str = "操作成功",
        **kwargs
    ) -> Dict[str, Any]:
        """返回成功响应"""
        return cls._build_response(
            success=True,
            message=message,
            data=data,
            **kwargs
        )
    
    @classmethod
    def error(
        cls,
        message: str = "操作失败",
        error_code: int = 500,
        error_details: Optional[Union[str, Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """返回错误响应"""
        return cls._build_response(
            success=False,
            message=message,
            error_code=error_code,
            error_details=error_details,
            **kwargs
        )
    
    @classmethod
    def bad_request(
        cls,
        message: str = "请求参数错误",
        error_details: Optional[Union[str, Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """返回请求参数错误响应"""
        return cls.error(
            message=message,
            error_code=400,
            error_details=error_details,
            **kwargs
        )
    
    @classmethod
    def unauthorized(
        cls,
        message: str = "未登录或登录已过期",
        error_details: Optional[Union[str, Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """返回未授权响应"""
        return cls.error(
            message=message,
            error_code=401,
            error_details=error_details,
            **kwargs
        )
    
    @classmethod
    def forbidden(
        cls,
        message: str = "权限不足",
        error_details: Optional[Union[str, Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """返回权限不足响应"""
        return cls.error(
            message=message,
            error_code=403,
            error_details=error_details,
            **kwargs
        )
    
    @classmethod
    def not_found(
        cls,
        message: str = "资源不存在",
        error_details: Optional[Union[str, Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """返回资源不存在响应"""
        return cls.error(
            message=message,
            error_code=404,
            error_details=error_details,
            **kwargs
        )
    
    @classmethod
    def validation_error(
        cls,
        message: str = "数据验证失败",
        error_details: Optional[Union[str, Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """返回数据验证失败响应"""
        return cls.error(
            message=message,
            error_code=422,
            error_details=error_details,
            **kwargs
        )
    
    @classmethod
    def server_error(
        cls,
        message: str = "服务器内部错误",
        error_details: Optional[Union[str, Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """返回服务器内部错误响应"""
        return cls.error(
            message=message,
            error_code=500,
            error_details=error_details,
            **kwargs
        )
    
    @classmethod
    def service_unavailable(
        cls,
        message: str = "服务暂时不可用",
        error_details: Optional[Union[str, Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """返回服务暂时不可用响应"""
        return cls.error(
            message=message,
            error_code=503,
            error_details=error_details,
            **kwargs
        )
    
    @classmethod
    def conflict(
        cls,
        message: str = "资源冲突",
        error_details: Optional[Union[str, Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """返回资源冲突响应"""
        return cls.error(
            message=message,
            error_code=409,
            error_details=error_details,
            **kwargs
        )
    
    @classmethod
    def too_many_requests(
        cls,
        message: str = "请求过于频繁",
        retry_after: Optional[int] = None,
        error_details: Optional[Union[str, Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """返回请求过于频繁响应"""
        if retry_after is not None:
            kwargs['retry_after'] = retry_after
        
        return cls.error(
            message=message,
            error_code=429,
            error_details=error_details,
            **kwargs
        )
