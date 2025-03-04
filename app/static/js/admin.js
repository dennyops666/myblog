$(document).ready(function() {
    // 删除确认
    $('.btn-delete').on('click', function(e) {
        if (!confirm('确定要删除吗？')) {
            e.preventDefault();
        }
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

// 初始化侧边栏
document.addEventListener('DOMContentLoaded', function() {
    // 获取当前页面的URL路径
    const currentPath = window.location.pathname;
    
    // 查找所有侧边栏链接
    const sidebarLinks = document.querySelectorAll('.nav-link');
    
    // 遍历链接，找到匹配当前路径的链接
    sidebarLinks.forEach(link => {
        if (currentPath.startsWith(link.getAttribute('href'))) {
            link.classList.add('active');
            
            // 如果链接在折叠面板中，展开面板
            const collapse = link.closest('.collapse');
            if (collapse) {
                collapse.classList.add('show');
                const trigger = document.querySelector(`[data-bs-target="#${collapse.id}"]`);
                if (trigger) {
                    trigger.setAttribute('aria-expanded', 'true');
                }
            }
        }
    });
}); 