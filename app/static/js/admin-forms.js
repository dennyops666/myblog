/**
 * 管理后台表单处理脚本
 * 用于拦截表单提交，使用AJAX方式提交，并处理JSON响应
 */

document.addEventListener('DOMContentLoaded', function() {
    // 查找所有管理后台表单
    const adminForms = document.querySelectorAll('form');
    
    adminForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // 检查表单是否有指定的不使用AJAX的属性
            if (form.dataset.noAjax === 'true') {
                return; // 不拦截此表单
            }
            
            // 阻止表单默认提交
            e.preventDefault();
            
            // 获取提交按钮，用于显示加载状态
            const submitButton = form.querySelector('button[type="submit"]');
            const originalButtonText = submitButton ? submitButton.innerHTML : '';
            
            // 显示加载状态
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 提交中...';
            }
            
            // 获取表单数据
            const formData = new FormData(form);
            
            // 使用fetch API发送请求
            fetch(form.action, {
                method: form.method || 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                // 检查是否是JSON响应
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    return response.json().then(data => {
                        // 恢复按钮状态
                        if (submitButton) {
                            submitButton.disabled = false;
                            submitButton.innerHTML = originalButtonText;
                        }
                        
                        // 处理JSON响应
                        handleJsonResponse(data);
                    });
                } else {
                    // 不是JSON响应，可能是HTML页面或重定向
                    window.location.href = response.url;
                }
            })
            .catch(error => {
                console.error('表单提交错误:', error);
                
                // 恢复按钮状态
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalButtonText;
                }
                
                // 显示错误提示
                showToast('error', '提交失败，请稍后重试');
            });
        });
    });
});

/**
 * 处理JSON响应
 * @param {Object} data - 服务器返回的JSON数据
 */
function handleJsonResponse(data) {
    // 检查是否成功
    if (data.success) {
        // 显示成功消息
        showToast('success', data.message || '操作成功！');
        
        // 如果有重定向URL，延迟后跳转
        if (data.redirect_url) {
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 1000);
        }
    } else {
        // 显示错误消息
        showToast('error', data.message || '操作失败！');
    }
}

/**
 * 显示提示消息
 * @param {string} type - 提示类型：success 或 error
 * @param {string} message - 提示消息
 */
function showToast(type, message) {
    // 检查是否已经有toast容器
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // 创建toast元素
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    // 设置toast内容
    toastEl.innerHTML = `
        <div class="toast-body">
            ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    `;
    
    // 添加到容器
    toastContainer.appendChild(toastEl);
    
    // 初始化Bootstrap toast
    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: 3000
    });
    
    // 显示toast
    toast.show();
    
    // 监听toast隐藏事件，移除元素
    toastEl.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
} 