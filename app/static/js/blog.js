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
    $('#commentForm').submit(function(e) {
        var $form = $(this);
        var $nickname = $form.find('[name="nickname"]');
        var $email = $form.find('[name="email"]');
        var $content = $form.find('[name="content"]');
        var valid = true;
        
        if (!$nickname.val().trim()) {
            valid = false;
            $nickname.addClass('is-invalid');
        } else {
            $nickname.removeClass('is-invalid');
        }
        
        if (!$email.val().trim() || !isValidEmail($email.val())) {
            valid = false;
            $email.addClass('is-invalid');
        } else {
            $email.removeClass('is-invalid');
        }
        
        if (!$content.val().trim()) {
            valid = false;
            $content.addClass('is-invalid');
        } else {
            $content.removeClass('is-invalid');
        }
        
        if (!valid) {
            e.preventDefault();
        }
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