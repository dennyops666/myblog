// 评论表单处理
$(document).ready(function() {
    // 评论表单验证
    $('#commentForm').on('submit', function(e) {
        e.preventDefault();
        var form = $(this);
        var url = form.attr('action');
        
        // 验证评论内容
        var content = form.find('[name="content"]').val().trim();
        if (!content) {
            window.showToast('error', '评论内容不能为空');
            return;
        }
        
        // 获取父评论ID
        var parentId = form.find('[name="parent_id"]').val();
        
        // 构建评论数据
        var commentData = {
            content: content,
            parent_id: parentId
        };
        
        // 如果存在昵称和邮箱字段（未登录用户），则添加这些信息
        if (form.find('[name="nickname"]').length && form.find('[name="email"]').length) {
            var nickname = form.find('[name="nickname"]').val().trim();
            var email = form.find('[name="email"]').val().trim();
            
            if (!nickname || !email) {
                window.showToast('error', '请输入昵称和邮箱');
                return;
            }
            if (!isValidEmail(email)) {
                window.showToast('error', '请输入有效的邮箱地址');
                return;
            }
            
            commentData.nickname = nickname;
            commentData.email = email;
        }
        
        // 禁用提交按钮，防止重复提交
        var submitBtn = form.find('button[type="submit"]');
        submitBtn.prop('disabled', true);
        
        $.ajax({
            type: 'POST',
            url: url,
            data: JSON.stringify(commentData),
            contentType: 'application/json',
            success: function(response) {
                if (response.status === 'success') {
                    window.showToast('success', response.message);
                    form[0].reset();
                    // 延迟1秒后刷新页面，确保用户能看到提示消息
                    setTimeout(function() {
                        location.reload();
                    }, 1000);
                } else {
                    window.showToast('error', response.message || '评论提交失败，请稍后重试');
                }
            },
            error: function(xhr) {
                var message = '评论提交失败，请稍后重试';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    message = xhr.responseJSON.message;
                }
                window.showToast('error', message);
            },
            complete: function() {
                // 重新启用提交按钮
                submitBtn.prop('disabled', false);
            }
        });
    });
});

// 辅助函数：验证邮箱格式
function isValidEmail(email) {
    var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
} 