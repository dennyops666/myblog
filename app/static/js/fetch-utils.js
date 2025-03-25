/**
 * 通用Fetch工具函数，自动处理401未授权等常见错误
 * @param {string} url - 请求URL
 * @param {Object} options - fetch选项
 * @returns {Promise} - 返回处理后的Promise
 */
function fetchWithAuth(url, options = {}) {
    return fetch(url, options)
        .then(response => {
            // 处理401未授权错误
            if (response.status === 401) {
                console.log("用户未登录，正在重定向到登录页面");
                // 如果响应是JSON格式，先解析它以获取redirect URL
                if (response.headers.get('content-type')?.includes('application/json')) {
                    return response.json().then(data => {
                        if (data.redirect) {
                            window.location.href = data.redirect;
                        } else {
                            // 默认重定向到登录页面
                            window.location.href = '/auth/login';
                        }
                        throw new Error("用户未登录");
                    });
                } else {
                    // 默认重定向到登录页面
                    window.location.href = '/auth/login';
                    throw new Error("用户未登录");
                }
            }
            
            // 处理其他服务器错误
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // 检查内容类型
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return response.json().then(data => {
                    // 检查JSON响应中的错误标志
                    if (data.success === false && data.redirect) {
                        window.location.href = data.redirect;
                        throw new Error(data.message || "操作失败");
                    }
                    return data;
                });
            }
            
            return response;
        });
} 