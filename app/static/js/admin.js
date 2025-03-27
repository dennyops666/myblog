// 确保 jQuery 已加载
function waitForJQuery(callback) {
    if (window.jQuery) {
        callback();
    } else {
        setTimeout(function() {
            waitForJQuery(callback);
        }, 50);
    }
}

// 等待 jQuery 加载完成后初始化管理功能
waitForJQuery(function() {
    $(document).ready(function() {
        // 初始化编辑器
        initializeEditor();
        
        // 创建遮罩层
        if (!$('.sidebar-overlay').length) {
            $('body').append('<div class="sidebar-overlay"></div>');
        }
        
        // 获取当前视口宽度
        function getViewportWidth() {
            return window.innerWidth || document.documentElement.clientWidth;
        }
        
        // 检查是否为移动设备视图
        function isMobileView() {
            return getViewportWidth() <= 992;
        }
        
        // 初始化布局状态
        function initLayout() {
            const $body = $('body');
            const $sidebar = $('.sidebar');
            const $mainWrapper = $('.main-wrapper');
            const $navbarBrand = $('.navbar-brand');
            const $sidebarOverlay = $('.sidebar-overlay');
            
            // 获取保存的侧边栏状态
            const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
            
            // 移动设备视图处理
            if (isMobileView()) {
                $sidebar.removeClass('collapsed show');
                $mainWrapper.removeClass('expanded');
                $navbarBrand.css('width', 'auto');
                $body.removeClass('sidebar-open');
                $sidebarOverlay.hide();
            } else {
                // 桌面视图处理
                if (isCollapsed) {
                    $sidebar.addClass('collapsed');
                    $mainWrapper.addClass('expanded');
                    $navbarBrand.css('width', '80px');
                } else {
                    $sidebar.removeClass('collapsed');
                    $mainWrapper.removeClass('expanded');
                    $navbarBrand.css('width', '300px');
                }
            }
            
            // 调整内容布局
            adjustContentLayout();
        }
        
        // 切换侧边栏状态
        function toggleSidebar() {
            const $body = $('body');
            const $sidebar = $('.sidebar');
            const $mainWrapper = $('.main-wrapper');
            const $navbarBrand = $('.navbar-brand');
            const $sidebarOverlay = $('.sidebar-overlay');
            
            // 移动设备视图处理
            if (isMobileView()) {
                $sidebar.toggleClass('show');
                $body.toggleClass('sidebar-open');
                
                if ($sidebar.hasClass('show')) {
                    $sidebarOverlay.fadeIn(200);
                    $body.css('overflow', 'hidden');
                } else {
                    $sidebarOverlay.fadeOut(200);
                    $body.css('overflow', '');
                }
            } else {
                // 桌面视图处理
                const willCollapse = !$sidebar.hasClass('collapsed');
                
                $sidebar.toggleClass('collapsed');
                $mainWrapper.toggleClass('expanded');
                
                if (willCollapse) {
                    $navbarBrand.css('width', '80px');
                } else {
                    $navbarBrand.css('width', '300px');
                }
                
                // 保存状态
                localStorage.setItem('sidebarCollapsed', willCollapse);
            }
            
            // 调整内容布局
            adjustContentLayout();
        }
        
        // 调整内容布局
        function adjustContentLayout() {
            const viewportWidth = getViewportWidth();
            const $dashboardStats = $('.dashboard-stats');
            const $latestContent = $('.latest-content');
            
            // 设置网格列数
            if (viewportWidth > 1920) {
                $dashboardStats.css('grid-template-columns', 'repeat(4, 1fr)');
                $latestContent.css('grid-template-columns', 'repeat(2, 1fr)');
            } else if (viewportWidth > 1600) {
                $dashboardStats.css('grid-template-columns', 'repeat(4, 1fr)');
                $latestContent.css('grid-template-columns', 'repeat(2, 1fr)');
            } else if (viewportWidth > 1366) {
                $dashboardStats.css('grid-template-columns', 'repeat(3, 1fr)');
                $latestContent.css('grid-template-columns', 'repeat(2, 1fr)');
            } else if (viewportWidth > 992) {
                $dashboardStats.css('grid-template-columns', 'repeat(2, 1fr)');
                $latestContent.css('grid-template-columns', '1fr');
            } else {
                $dashboardStats.css('grid-template-columns', '1fr');
                $latestContent.css('grid-template-columns', '1fr');
            }
        }
        
        // 绑定事件处理
        function bindEvents() {
            // 侧边栏切换按钮
            $('#sidebarToggle').off('click').on('click', function(e) {
                e.preventDefault();
                toggleSidebar();
            });
            
            // 遮罩层点击事件
            $('.sidebar-overlay').off('click').on('click', function() {
                toggleSidebar();
            });
            
            // 窗口大小变化事件
            let resizeTimer;
            $(window).off('resize').on('resize', function() {
                clearTimeout(resizeTimer);
                resizeTimer = setTimeout(function() {
                    initLayout();
                }, 250);
            });
        }
        
        // 初始化
        initLayout();
        bindEvents();

        // 删除确认
        $('.btn-delete').on('click', function(e) {
            if (!confirm('确定要删除吗？此操作不可恢复！')) {
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
        
        // 初始化侧边栏
        const currentPath = window.location.pathname;
        const sidebarLinks = document.querySelectorAll('.nav-link');
        
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

        // 初始化工具提示
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // 初始化弹出框
        var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });

        // 自动隐藏警告框
        var alertList = document.querySelectorAll('.alert');
        alertList.forEach(function(alert) {
            setTimeout(function() {
                var bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });

        // 实时获取最新统计数据
        fetchLatestStats();
        
        // 每60秒自动刷新一次统计数据
        setInterval(fetchLatestStats, 60000);

        // 添加自动刷新统计数据的功能
        if (window.location.pathname === '/admin/' || window.location.pathname === '/admin/dashboard') {
            console.log('管理后台首页已加载，将启用自动刷新');
            
            // 立即刷新一次
            refreshStats();
            
            // 每60秒自动刷新一次
            setInterval(refreshStats, 60000);
        }
    });
});

// 获取最新统计数据
function fetchLatestStats() {
    fetch('/admin/api/stats')
        .then(response => response.json())
        .then(data => {
            // 更新统计数据
            updateStats(data);
            // 更新最近文章列表
            if (data.recent_posts && data.recent_posts.length > 0) {
                updateRecentPosts(data.recent_posts);
            }
        })
        .catch(error => console.error('获取统计数据失败:', error));
}

// 更新统计数据
function updateStats(data) {
    // 更新各项统计数字
    if (document.getElementById('post-count')) {
        document.getElementById('post-count').textContent = data.post_count || 0;
    }
    if (document.getElementById('category-count')) {
        document.getElementById('category-count').textContent = data.category_count || 0;
    }
    if (document.getElementById('published-count')) {
        document.getElementById('published-count').textContent = data.published_count || 0;
    }
    if (document.getElementById('draft-count')) {
        document.getElementById('draft-count').textContent = data.draft_count || 0;
    }
    if (document.getElementById('tag-count')) {
        document.getElementById('tag-count').textContent = data.tag_count || 0;
    }
}

/**
 * 更新最近文章列表
 */
function updateRecentPosts(posts) {
    const tbody = $('#recent-posts-table tbody');
    
    if (!posts || posts.length === 0) {
        tbody.html('<tr><td colspan="5" class="text-center py-3">暂无文章</td></tr>');
        return;
    }
    
    let html = '';
    posts.forEach(post => {
        // 根据状态设置不同的标签样式
        let statusClass = 'badge-secondary';
        let statusText = post.status;
        
        if (post.status === 'PUBLISHED') {
            statusClass = 'badge-success';
            statusText = '已发布';
        } else if (post.status === 'DRAFT') {
            statusClass = 'badge-warning';
            statusText = '草稿';
        } else if (post.status === 'ARCHIVED') {
            statusClass = 'badge-secondary';
            statusText = '已归档';
        }
        
        // 检查是否是暗黑模式
        const isDarkMode = document.documentElement.classList.contains('dark-theme');
        
        // 在暗黑模式下需要确保按钮和标签有正确的样式
        const btnClass = isDarkMode ? 'btn-primary' : 'btn-primary';
        
        html += `
        <tr>
            <td>${post.title}</td>
            <td>${post.created_at || '未知'}</td>
            <td><span class="badge ${statusClass}">${statusText}</span></td>
            <td>${post.view_count || 0}</td>
            <td>
                <a href="/admin/post/${post.id}/edit" class="btn btn-sm ${btnClass}">
                    <i class="fa fa-edit"></i> 编辑
                </a>
            </td>
        </tr>
        `;
    });
    
    tbody.html(html);
}

/**
 * 刷新统计数据和文章列表
 */
function refreshStats() {
    console.log('开始刷新后台统计数据...');
    
    // 获取当前时间戳，防止缓存
    const timestamp = new Date().getTime();
    
    // 设置加载状态
    $('#post-count, #category-count, #comment-count, #tag-count, #view-count').html('<i class="fa fa-spinner fa-spin"></i>');
    
    // 使用fetch API
    fetch(`/admin/api/stats?_=${timestamp}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('网络错误');
        }
        return response.json();
    })
    .then(data => {
        console.log('获取统计数据成功:', data);
        
        // 更新统计数据
        $('#post-count').text(data.post_count || 0);
        $('#category-count').text(data.category_count || 0);
        if ($('#published-count').length) {
            $('#published-count').text(data.published_count || 0);
        }
        if ($('#draft-count').length) {
            $('#draft-count').text(data.draft_count || 0);
        }
        $('#tag-count').text(data.tag_count || 0);
        
        // 更新文章列表
        updateRecentPosts(data.recent_posts || []);
    })
    .catch(error => {
        console.error('获取统计数据失败:', error);
        // 显示错误提示
        $('#post-count, #category-count, #tag-count').text('--');
    });
}

/**
 * 初始化简单文本编辑器
 */
function initializeEditor() {
    const editor = document.getElementById('content-editor');
    if (!editor) return;
    
    // 创建工具栏
    const toolbar = document.createElement('div');
    toolbar.className = 'editor-toolbar btn-toolbar';
    toolbar.setAttribute('role', 'toolbar');
    toolbar.setAttribute('aria-label', '编辑器工具栏');
    editor.parentNode.insertBefore(toolbar, editor);
    
    // 添加工具栏按钮组
    const buttonGroups = [
        [
            { name: '加粗', icon: '<i class="fas fa-bold"></i>', action: 'bold' },
            { name: '斜体', icon: '<i class="fas fa-italic"></i>', action: 'italic' }
        ],
        [
            { name: '标题1', icon: 'H1', action: 'h1' },
            { name: '标题2', icon: 'H2', action: 'h2' },
            { name: '标题3', icon: 'H3', action: 'h3' }
        ],
        [
            { name: '链接', icon: '<i class="fas fa-link"></i>', action: 'link' },
            { name: '图片', icon: '<i class="fas fa-image"></i>', action: 'image' }
        ]
    ];
    
    buttonGroups.forEach(function(group) {
        const buttonGroup = document.createElement('div');
        buttonGroup.className = 'btn-group me-2';
        buttonGroup.setAttribute('role', 'group');
        
        group.forEach(function(btn) {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'btn btn-sm btn-outline-secondary';
            button.title = btn.name;
            button.innerHTML = btn.icon;
            button.dataset.action = btn.action;
            button.onclick = function() {
                const start = editor.selectionStart;
                const end = editor.selectionEnd;
                handleEditorAction(editor, btn.action, start, end);
            };
            buttonGroup.appendChild(button);
        });
        
        toolbar.appendChild(buttonGroup);
    });
    
    // 防止tab键跳出编辑器
    editor.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = this.selectionStart;
            const end = this.selectionEnd;
            this.value = this.value.substring(0, start) + '\t' + this.value.substring(end);
            this.selectionStart = this.selectionEnd = start + 1;
        }
    });
}

// 处理编辑器操作
function handleEditorAction(editor, action, start, end) {
    const selectedText = editor.value.substring(start, end);
    let replacement = '';

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
            }
            break;
        case 'image':
            const imgUrl = prompt('请输入图片链接:', 'http://');
            if (imgUrl) {
                replacement = `<img src="${imgUrl}" alt="" style="max-width:100%;" />`;
            }
            break;
    }
    
    if (replacement) {
        editor.value = editor.value.substring(0, start) + replacement + editor.value.substring(end);
        editor.selectionStart = editor.selectionEnd = start + replacement.length;
        
        // 触发 change 事件
        const event = new Event('change', { bubbles: true });
        editor.dispatchEvent(event);
    }
} 