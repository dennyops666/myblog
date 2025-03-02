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
        $('pre code').each(function(i, block) {
            hljs.highlightBlock(block);
        });
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
    
    // 评论表单验证
    $('#comment-form').on('submit', function(e) {
        e.preventDefault();
        var form = $(this);
        var url = form.attr('action');
        
        $.ajax({
            type: 'POST',
            url: url,
            data: JSON.stringify({
                content: $('#content').val(),
                nickname: $('#nickname').val(),
                email: $('#email').val(),
                parent_id: $('#parent_id').val()
            }),
            contentType: 'application/json',
            success: function(response) {
                if (response.status === 'success') {
                    // 显示成功消息
                    showAlert('success', response.message);
                    // 清空表单
                    form[0].reset();
                    // 刷新评论列表
                    location.reload();
                } else {
                    showAlert('danger', response.message);
                }
            },
            error: function(xhr) {
                var message = '提交评论失败';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    message = xhr.responseJSON.message;
                }
                showAlert('danger', message);
            }
        });
    });
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
function showAlert(type, message) {
    var alert = $('<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' +
        message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' +
        '</div>');
    
    $('#messages').append(alert);
    alert.delay(3000).fadeOut(500, function() {
        $(this).remove();
    });
} 