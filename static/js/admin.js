/**
 * 博客管理系统JavaScript功能
 */
document.addEventListener('DOMContentLoaded', function() {
    // 初始化删除确认
    initializeDeleteConfirmations();
    
    // 初始化提示消息自动关闭
    initializeAlertDismiss();
    
    // 高亮当前菜单项
    highlightActiveMenuItem();
    
    // 如果页面上有编辑器，初始化它
    if (document.getElementById('content-editor')) {
        initializeEditor();
    }
});

/**
 * 初始化删除确认对话框
 */
function initializeDeleteConfirmations() {
    // 查找所有带有删除确认的链接
    document.querySelectorAll('[data-confirm]').forEach(function(element) {
        element.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || '确定要删除吗？';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

/**
 * 初始化提示消息自动关闭
 */
function initializeAlertDismiss() {
    // 查找所有提示消息
    document.querySelectorAll('.alert').forEach(function(alert) {
        // 5秒后自动淡出
        setTimeout(function() {
            // 添加淡出类
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s';
            
            // 完全淡出后移除元素
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    });
}

/**
 * 高亮当前菜单项
 */
function highlightActiveMenuItem() {
    // 当我们已经从后端渲染了active类时，我们不需要再用JS添加
    // 检查是否已经有高亮菜单项
    const hasActiveMenu = document.querySelector('.sidebar-menu a.active');
    
    // 如果已有活动菜单项，不做额外处理
    if (hasActiveMenu) {
        return;
    }
    
    // 否则，根据URL路径确定活动菜单项
    const currentPath = window.location.pathname;
    
    // 特殊处理：如果当前在/admin/，那么只有首页按钮高亮
    if (currentPath === '/admin/' || currentPath === '/admin') {
        const homeLink = document.querySelector('.sidebar-menu a[href="/admin"]');
        if (homeLink) {
            homeLink.classList.add('active');
        }
        return;
    }
    
    // 对于其他页面，找到最匹配的菜单项
    let bestMatch = null;
    let bestMatchLength = 0;
    
    // 查找所有菜单项，使用正确的侧边栏选择器
    document.querySelectorAll('.sidebar-menu a').forEach(function(link) {
        const href = link.getAttribute('href');
        
        // 跳过首页链接，防止它匹配到所有/admin/开头的路径
        if (href === '/admin' || href === '/admin/') {
            return;
        }
        
        // 如果链接路径是当前路径的前缀，并且比之前找到的匹配更长
        if (currentPath.startsWith(href) && href.length > bestMatchLength) {
            bestMatch = link;
            bestMatchLength = href.length;
        }
    });
    
    // 如果找到了匹配，添加活动类
    if (bestMatch) {
        bestMatch.classList.add('active');
    }
}

/**
 * 初始化简单文本编辑器
 */
function initializeEditor() {
    const editor = document.getElementById('content-editor');
    if (!editor) return;
    
    // 创建工具栏
    const toolbar = document.createElement('div');
    toolbar.className = 'editor-toolbar';
    editor.parentNode.insertBefore(toolbar, editor);
    
    // 添加工具栏按钮
    const buttons = [
        { name: '加粗', icon: '𝐁', action: 'bold' },
        { name: '斜体', icon: '𝐼', action: 'italic' },
        { name: '标题1', icon: 'H1', action: 'h1' },
        { name: '标题2', icon: 'H2', action: 'h2' },
        { name: '标题3', icon: 'H3', action: 'h3' },
        { name: '链接', icon: '🔗', action: 'link' },
        { name: '图片', icon: '🖼️', action: 'image' },
        { name: '预览', icon: '👁️', action: 'preview' }
    ];
    
    buttons.forEach(function(btn) {
        const button = document.createElement('button');
        button.type = 'button';
        button.title = btn.name;
        button.textContent = btn.icon;
        button.dataset.action = btn.action;
        button.addEventListener('click', function() {
            handleEditorAction(this.dataset.action, editor);
        });
        toolbar.appendChild(button);
    });
    
    // 防止tab键跳出编辑器
    editor.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            e.preventDefault();
            
            // 在光标位置插入制表符
            const start = this.selectionStart;
            const end = this.selectionEnd;
            
            this.value = this.value.substring(0, start) + 
                         '\t' + 
                         this.value.substring(end);
            
            // 将光标放在插入的制表符之后
            this.selectionStart = this.selectionEnd = start + 1;
        }
    });
}

/**
 * 处理编辑器操作
 */
function handleEditorAction(action, editor) {
    // 获取选中的文本
    const start = editor.selectionStart;
    const end = editor.selectionEnd;
    const selectedText = editor.value.substring(start, end);
    let replacement = '';
    
    // 根据操作类型处理
    switch (action) {
        case 'bold':
            replacement = `<strong>${selectedText}</strong>`;
            break;
        case 'italic':
            replacement = `<em>${selectedText}</em>`;
            break;
        case 'h1':
            replacement = `<h1>${selectedText}</h1>`;
            break;
        case 'h2':
            replacement = `<h2>${selectedText}</h2>`;
            break;
        case 'h3':
            replacement = `<h3>${selectedText}</h3>`;
            break;
        case 'link':
            const url = prompt('请输入链接地址:', 'http://');
            if (url) {
                replacement = `<a href="${url}">${selectedText || url}</a>`;
            } else {
                return; // 用户取消
            }
            break;
        case 'image':
            const imgUrl = prompt('请输入图片地址:', 'http://');
            if (imgUrl) {
                const alt = prompt('请输入图片描述:', '');
                replacement = `<img src="${imgUrl}" alt="${alt}" />`;
            } else {
                return; // 用户取消
            }
            break;
        case 'preview':
            // 创建或更新预览区域
            let preview = document.getElementById('editor-preview');
            if (!preview) {
                preview = document.createElement('div');
                preview.id = 'editor-preview';
                preview.className = 'card';
                preview.style.marginTop = '20px';
                
                const previewHeader = document.createElement('div');
                previewHeader.className = 'card-header';
                previewHeader.innerHTML = '<h3>预览</h3>';
                preview.appendChild(previewHeader);
                
                const previewBody = document.createElement('div');
                previewBody.className = 'card-body';
                previewBody.id = 'preview-content';
                preview.appendChild(previewBody);
                
                editor.parentNode.appendChild(preview);
            }
            
            // 更新预览内容
            document.getElementById('preview-content').innerHTML = editor.value;
            return;
    }
    
    // 更新编辑器内容
    if (replacement) {
        editor.value = editor.value.substring(0, start) + 
                       replacement + 
                       editor.value.substring(end);
        
        // 将光标放在插入的内容之后
        editor.selectionStart = editor.selectionEnd = start + replacement.length;
        editor.focus();
    }
} 