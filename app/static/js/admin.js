$(document).ready(function() {
    // 删除确认
    $('.btn-delete').on('click', function(e) {
        if (!confirm('确定要删除吗？')) {
            e.preventDefault();
        }
    });

    // 表单验证和提交
    $('form').on('submit', function(e) {
        e.preventDefault(); // 阻止表单默认提交
        
        var $form = $(this);
        var $submitBtn = $form.find('button[type="submit"]');
        var originalBtnText = $submitBtn.text();
        
        // 验证必填字段
        var required = $form.find('[required]');
        var valid = true;
        required.each(function() {
            if (!$(this).val()) {
                valid = false;
                $(this).addClass('is-invalid');
            } else {
                $(this).removeClass('is-invalid');
            }
        });
        
        if (!valid) {
            showMessage('请填写所有必填字段', false);
            return;
        }
        
        // 禁用提交按钮并显示加载状态
        $submitBtn.prop('disabled', true).text('保存中...');
        
        // 准备表单数据
        var formData = new FormData($form[0]);
        
        // 发送AJAX请求
        fetch($form.attr('action'), {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应错误');
            }
            return response.text().then(text => {
                try {
                    return text ? JSON.parse(text) : {};
                } catch (e) {
                    console.error('解析响应数据失败:', e);
                    throw new Error('服务器响应格式错误');
                }
            });
        })
        .then(data => {
            if (data.success) {
                showMessage(data.message || '保存成功', true);
                if (data.redirect_url) {
                    setTimeout(function() {
                        window.location.href = data.redirect_url;
                    }, 1000);
                }
            } else {
                showMessage(data.message || '保存失败', false);
            }
        })
        .catch(error => {
            console.error('提交表单失败:', error);
            showMessage('保存失败：' + error.message, false);
        })
        .finally(() => {
            // 恢复提交按钮状态
            $submitBtn.prop('disabled', false).text(originalBtnText);
        });
    });

    // 图片预览
    $('input[type="file"]').on('change', function() {
        var file = this.files[0];
        if (file) {
            var reader = new FileReader();
            reader.onload = function(e) {
                $('#preview').attr('src', e.target.result);
            };
            reader.readAsDataURL(file);
        }
    });

    // 初始化标签输入
    $(window).on('load', function() {
        try {
            var $tagInput = $('#tags');
            if ($tagInput.length > 0) {
                // 初始化 Select2
                $tagInput.select2({
                    theme: 'bootstrap-5',
                    language: 'zh-CN',
                    placeholder: '选择或输入标签',
                    allowClear: true,
                    multiple: true,
                    tags: true,
                    tokenSeparators: [',', ' '],
                    width: '100%',
                    maximumSelectionLength: 5,
                    minimumInputLength: 1,
                    selectOnClose: true
                });

                // 从后端获取标签数据
                var existingTags = $tagInput.data('tags');
                if (existingTags && Array.isArray(existingTags)) {
                    existingTags.forEach(function(tag) {
                        if (tag && tag.id && tag.text) {
                            var option = new Option(tag.text, tag.id, true, true);
                            $tagInput.append(option);
                        }
                    });
                    $tagInput.trigger('change');
                }
            }
        } catch (e) {
            console.error('初始化标签输入失败:', e);
        }
    });
});

// 显示消息提示
function showMessage(message, success) {
    var alertClass = success ? 'alert-success' : 'alert-danger';
    var $alert = $('<div class="alert ' + alertClass + ' alert-dismissible fade show" role="alert">' +
        message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>' +
        '</div>');
    
    // 移除现有的提示
    $('.alert').remove();
    
    // 添加新提示到页面顶部
    $('.container').first().prepend($alert);
    
    // 自动关闭提示
    if (success) {
        setTimeout(function() {
            $alert.alert('close');
        }, 3000);
    }
} 