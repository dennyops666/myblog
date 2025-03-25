// 页面加载完成后执行
$(document).ready(function() {
    // 自动隐藏消息提示
    $('.alert').delay(3000).fadeOut();
    
    // 返回顶部按钮
    var $backToTop = $('<a>', {
        href: '#',
        class: 'back-to-top',
        html: '<i class="fas fa-arrow-up"></i>'
    }).appendTo('body');
    
    $(window).scroll(function() {
        if ($(this).scrollTop() > 100) {
            $backToTop.fadeIn();
        } else {
            $backToTop.fadeOut();
        }
    });
    
    $backToTop.click(function(e) {
        e.preventDefault();
        $('html, body').animate({scrollTop: 0}, 800);
    });
    
    // 文章目录导航
    if ($('.article-toc').length) {
        var headings = $('.article-content').find('h2, h3, h4');
        var toc = '';
        
        headings.each(function(i) {
            var $heading = $(this);
            var id = 'heading-' + i;
            $heading.attr('id', id);
            
            var level = parseInt($heading.prop('tagName').substr(1)) - 1;
            var indent = '  '.repeat(level - 1);
            
            toc += indent + '- [' + $heading.text() + '](#' + id + ')\n';
        });
        
        $('.article-toc').html(marked(toc));
        
        // 滚动时高亮当前标题
        $(window).scroll(function() {
            var scrollTop = $(this).scrollTop();
            
            headings.each(function() {
                var $heading = $(this);
                var headingTop = $heading.offset().top - 100;
                
                if (scrollTop >= headingTop) {
                    var id = $heading.attr('id');
                    $('.article-toc a').removeClass('active');
                    $('.article-toc a[href="#' + id + '"]').addClass('active');
                }
            });
        });
    }
    
    // 代码高亮
    if ($('pre code').length) {
        // 检查hljs是否存在
        if (typeof hljs !== 'undefined') {
            $('pre code').each(function(i, block) {
                hljs.highlightBlock(block);
            });
        } else {
            console.warn('高亮库(hljs)未加载，代码块将不会被高亮显示');
        }
    }
    
    // 图片点击放大
    $('.article-content img').click(function() {
        var $img = $(this);
        var src = $img.attr('src');
        
        var $modal = $('<div>', {
            class: 'modal fade',
            html: `
                <div class="modal-dialog modal-lg modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-body p-0">
                            <img src="${src}" class="img-fluid">
                        </div>
                    </div>
                </div>
            `
        }).appendTo('body');
        
        $modal.modal('show');
        $modal.on('hidden.bs.modal', function() {
            $modal.remove();
        });
    });
    
    // 初始化 POST_DATA
    if (typeof window.POST_DATA === 'undefined') {
        console.log('POST_DATA未定义，初始化默认值');
        window.POST_DATA = {
            postId: window.location.pathname.split('/').pop(),
            currentUser: {
                isAuthenticated: false
            }
        };
    } else {
        console.log('检测到用户状态:', window.POST_DATA.currentUser.isAuthenticated ? '已登录' : '未登录');
    }

    // 获取DOM元素
    const $commentForm = $('#comment-form');
    if (!$commentForm.length) {
        console.log('评论表单不存在，跳过初始化');
        return;
    }

    const $commentContent = $('#content');
    const $replyHint = $('#reply-hint');
    const $cancelReply = $('#cancel-reply');
    const $submitBtn = $commentForm.find('button[type="submit"]');
    const $nickname = $('#nickname');
    const $email = $('#email');
    
    // 回复按钮点击事件
    $('.reply-btn').on('click', function() {
        const commentId = $(this).data('comment-id');
        const authorName = $(this).data('author-name');
        
        // 先移除所有已存在的parent_id输入框
        $commentForm.find('input[name="parent_id"]').remove();
        // 添加新的parent_id输入框
        $commentForm.append(`<input type="hidden" name="parent_id" value="${commentId}">`);
        $replyHint.find('span').text(`回复 ${authorName}：`);
        $replyHint.show();
        $commentContent.focus();
        
        // 滚动到评论框
        $('html, body').animate({
            scrollTop: $commentForm.offset().top - 100
        }, 500);
    });
    
    // 取消回复
    $cancelReply.on('click', function() {
        $commentForm.find('input[name="parent_id"]').remove();
        $replyHint.hide();
        $commentContent.focus();
    });
    
    // 检查用户认证状态并加载保存的信息
    const isAuthenticated = window.POST_DATA && 
                          window.POST_DATA.currentUser && 
                          window.POST_DATA.currentUser.isAuthenticated;
                          
    if (!isAuthenticated) {
        const savedNickname = localStorage.getItem('nickname');
        const savedEmail = localStorage.getItem('email');
        
        if (savedNickname) $nickname.val(savedNickname);
        if (savedEmail) $email.val(savedEmail);
    }
    
    // 评论表单提交
    let isSubmitting = false;
    $commentForm.on('submit', function(e) {
        e.preventDefault();
        
        // 如果正在提交，直接返回
        if (isSubmitting) {
            return;
        }
        
        // 获取评论内容并安全处理
        const contentVal = $commentContent.val() || '';
        const content = contentVal.trim();
        
        if (!content) {
            showToast('error', '请输入评论内容');
            return;
        }
        
        // 构建评论数据
        const commentData = {
            content: content,
            parent_id: $commentForm.find('input[name="parent_id"]').val() || null
        };
        
        // 检查用户认证状态
        const isAuthenticated = window.POST_DATA && 
                              window.POST_DATA.currentUser && 
                              window.POST_DATA.currentUser.isAuthenticated === true;
        
        console.log('提交评论时用户状态:', isAuthenticated ? '已登录' : '未登录');
        
        // 如果是匿名评论，需要验证昵称和邮箱
        if (!isAuthenticated) {
            // 只有未登录用户才需要检查昵称和邮箱
            const nicknameExists = $nickname.length > 0;
            const emailExists = $email.length > 0;
            
            console.log('表单字段检测:', {
                nicknameExists: nicknameExists,
                emailExists: emailExists
            });
            
            if (nicknameExists && emailExists) {
                const nicknameVal = $nickname.val() || '';
                const emailVal = $email.val() || '';
                const nickname = nicknameVal.trim();
                const email = emailVal.trim();
                
                if (!nickname) {
                    showToast('error', '请输入昵称');
                    return;
                }
                
                if (!email || !isValidEmail(email)) {
                    showToast('error', '请输入有效的邮箱地址');
                    return;
                }
                
                commentData.nickname = nickname;
                commentData.email = email;
                
                // 保存到localStorage
                localStorage.setItem('nickname', nickname);
                localStorage.setItem('email', email);
            } else {
                console.error('昵称或邮箱字段不存在，但用户未登录。可能是模板问题。');
                showToast('error', '无法提交评论，请刷新页面后重试');
                return;
            }
        } else {
            // 已登录用户不需要额外的验证，服务端会使用当前用户信息
            console.log('用户已登录，使用当前用户信息');
            
            // 确保已登录用户也发送必要的字段
            if (window.POST_DATA && window.POST_DATA.currentUser) {
                console.log('POST_DATA.currentUser详情:', window.POST_DATA.currentUser);
                if (window.POST_DATA.currentUser.username) {
                    commentData.nickname = window.POST_DATA.currentUser.username;
                    console.log('设置已登录用户昵称:', commentData.nickname);
                }
                if (window.POST_DATA.currentUser.email) {
                    commentData.email = window.POST_DATA.currentUser.email;
                    console.log('设置已登录用户邮箱:', commentData.email);
                }
                if (window.POST_DATA.currentUser.id) {
                    commentData.author_id = window.POST_DATA.currentUser.id;
                    console.log('设置已登录用户ID:', commentData.author_id);
                }
            } else {
                console.warn('已登录但POST_DATA.currentUser缺失');
            }
        }
        
        // 设置提交状态
        isSubmitting = true;
        
        console.log('最终提交的评论数据:', JSON.stringify(commentData));
        
        // 禁用提交按钮
        $submitBtn.prop('disabled', true).text('提交中...');
        
        // 发送评论请求
        const postId = $commentForm.data('post-id');
        
        // 如果form中没有post-id属性，尝试从URL获取
        let commentUrl;
        if (postId) {
            commentUrl = `/blog/post/${postId}/comment`;
        } else {
            // 从URL路径中提取文章ID
            const pathSegments = window.location.pathname.split('/');
            // 假设URL格式为 /blog/post/:id 或类似格式
            const urlPostId = pathSegments[pathSegments.length - 1];
            if (!urlPostId || urlPostId === '' || isNaN(parseInt(urlPostId))) {
                console.error('无法确定文章ID，评论提交失败');
                showToast('error', '无法确定文章ID，评论提交失败');
                $submitBtn.prop('disabled', false).text('发表评论');
                isSubmitting = false;
                return;
            }
            commentUrl = `/blog/post/${urlPostId}/comment`;
        }
        
        console.log('正在提交评论:', {
            url: commentUrl,
            data: commentData,
            isAuthenticated: isAuthenticated,
            userId: window.POST_DATA.currentUser.id,
            content: commentData.content,
            author_id: commentData.author_id,
            nickname: commentData.nickname,
            email: commentData.email,
            parent_id: commentData.parent_id
        });
        
        // 验证必填字段
        if (!commentData.content || commentData.content.trim() === '') {
            showToast('error', '请输入评论内容');
            $submitBtn.prop('disabled', false).text('发表评论');
            isSubmitting = false;
            return;
        }
        
        $.ajax({
            url: commentUrl,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(commentData),
            success: function(response) {
                console.log('评论提交响应:', response);
                console.log('response.success的值:', response.success, '类型:', typeof response.success);
                console.log('response.status的值:', response.status);
                
                // 强制使用绿色背景显示成功消息
                if (response && (response.success === true || response.status === 'success')) {
                    // 重置表单
                    resetForm();
                    // 显示成功提示
                    showToast('success', response.message || '评论发布成功');
                    // 延迟刷新页面，并防止重复提交
                    $submitBtn.text('提交成功，页面即将刷新...');
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    showToast('error', response.message || '评论失败，请稍后重试');
                    // 恢复提交按钮和提交状态
                    $submitBtn.prop('disabled', false).text('发表评论');
                    isSubmitting = false;
                }
            },
            error: function(xhr, status, error) {
                console.error('评论提交失败:', {
                    status: status,
                    error: error,
                    response: xhr.responseText
                });
                
                let errorMessage = '评论失败，请稍后重试';
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response && response.message) {
                        errorMessage = response.message;
                    }
                } catch (e) {
                    console.error('解析错误响应失败:', e);
                }
                
                showToast('error', errorMessage);
                // 恢复提交按钮和提交状态
                $submitBtn.prop('disabled', false).text('发表评论');
                isSubmitting = false;
            }
        });
    });
    
    // 重置表单
    function resetForm() {
        $commentForm[0].reset();
        $commentForm.find('input[name="parent_id"]').remove();
        $replyHint.hide();
    }
});

// 辅助函数：验证邮箱格式
function isValidEmail(email) {
    var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// 返回顶部按钮样式
var style = document.createElement('style');
style.textContent = `
    .back-to-top {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 40px;
        height: 40px;
        background-color: #007bff;
        color: #fff;
        text-align: center;
        line-height: 40px;
        border-radius: 50%;
        display: none;
        z-index: 1000;
        box-shadow: 0 2px 5px rgba(0,0,0,.2);
        transition: background-color 0.3s;
    }
    
    .back-to-top:hover {
        background-color: #0056b3;
        color: #fff;
        text-decoration: none;
    }
    
    .article-toc {
        position: sticky;
        top: 20px;
    }
    
    .article-toc a {
        display: block;
        padding: 5px 0;
        color: #666;
        text-decoration: none;
        transition: color 0.3s;
    }
    
    .article-toc a:hover,
    .article-toc a.active {
        color: #007bff;
    }
`;
document.head.appendChild(style);

// 显示提示消息
function showToast(type, message) {
    console.log('调用showToast，类型:', type, '消息:', message);
    
    // 清除所有现有的toast
    $('.toast-container .toast').remove();
    
    // 明确设置背景颜色类
    let bgClass;
    if (type === 'success') {
        console.log('设置绿色背景');
        bgClass = 'bg-success';
    } else if (type === 'error') {
        console.log('设置红色背景'); 
        bgClass = 'bg-danger';
    } else {
        console.log('设置信息背景');
        bgClass = 'bg-info';
    }
    
    const toast = `
        <div class="toast align-items-center text-white ${bgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    // 检查toast-container是否存在
    if ($('.toast-container').length === 0) {
        console.log('toast-container不存在，创建新的');
        $('body').append('<div class="toast-container position-fixed top-0 end-0 p-3"></div>');
    }
    
    $('.toast-container').append(toast);
    const $toast = $('.toast').last();
    const bsToast = new bootstrap.Toast($toast, {
        delay: 3000,
        animation: true
    });
    bsToast.show();
    
    // 自动移除
    $toast.on('hidden.bs.toast', function() {
        $(this).remove();
    });
} 