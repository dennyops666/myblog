// 评论提交处理
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM已加载，初始化评论表单处理');
    
    // 获取评论表单
    const commentForm = document.getElementById('comment-form');
    
    if (commentForm) {
        console.log('找到评论表单，设置提交处理程序');
        
        commentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('评论表单提交被触发');
            
            // 获取表单数据
            const postId = commentForm.getAttribute('data-post-id');
            console.log('文章ID:', postId);
            
            const contentField = document.getElementById('content');
            if (!contentField) {
                console.error('未找到内容输入框');
                showAlert('评论提交失败：表单不完整', 'danger');
                return;
            }
            
            const content = contentField.value.trim();
            console.log('评论内容:', content);
            
            if (!content) {
                showAlert('请输入评论内容', 'danger');
                return;
            }
            
            // 构建评论数据
            const commentData = {
                content: content
            };
            
            // 如果是游客，获取昵称和邮箱
            const nicknameField = document.getElementById('nickname');
            const emailField = document.getElementById('email');
            
            if (nicknameField && emailField) {
                const nickname = nicknameField.value.trim();
                const email = emailField.value.trim();
                console.log('昵称:', nickname, '邮箱:', email);
                
                if (!nickname) {
                    showAlert('请输入您的昵称', 'danger');
                    return;
                }
                
                commentData.nickname = nickname;
                commentData.email = email;
            }
            
            // 禁用提交按钮
            const submitButton = commentForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = '提交中...';
            }
            
            const requestUrl = `/blog/post/${postId}/comment`;
            console.log('发送评论请求到:', requestUrl);
            console.log('评论数据:', JSON.stringify(commentData));
            
            // 发送原生AJAX请求
            fetch(requestUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(commentData)
            })
            .then(response => {
                console.log('收到响应:', response.status);
                // 尝试解析JSON
                return response.json().catch(err => {
                    console.error('JSON解析错误:', err);
                    return { success: false, message: '服务器响应格式错误' };
                });
            })
            .then(data => {
                console.log('响应数据:', data);
                if (data.success) {
                    // 成功提交
                    showAlert('评论提交成功，等待审核', 'success');
                    // 清空表单
                    commentForm.reset();
                    // 2秒后刷新页面
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    // 提交失败
                    showAlert(data.message || '评论提交失败', 'danger');
                }
            })
            .catch(error => {
                console.error('评论提交错误:', error);
                showAlert('评论提交时发生错误，请稍后再试', 'danger');
            })
            .finally(() => {
                // 恢复提交按钮
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.textContent = '提交评论';
                }
            });
        });
    } else {
        console.warn('未找到评论表单，ID为comment-form的表单不存在');
    }
});

// 显示提示消息
function showAlert(message, type) {
    console.log('显示提示:', message, type);
    
    // 创建提示元素
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = message + 
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
    
    // 查找提示容器
    let alertContainer = document.querySelector('.alert-container');
    if (!alertContainer) {
        // 如果不存在，创建一个
        alertContainer = document.createElement('div');
        alertContainer.className = 'alert-container';
        alertContainer.style.position = 'fixed';
        alertContainer.style.top = '20px';
        alertContainer.style.right = '20px';
        alertContainer.style.zIndex = '1050';
        document.body.appendChild(alertContainer);
    }
    
    // 添加提示
    alertContainer.appendChild(alertDiv);
    
    // 5秒后自动关闭
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
} 