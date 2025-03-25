/**
 * 主题切换功能
 * 用于在明亮模式和暗黑模式之间切换
 */
document.addEventListener('DOMContentLoaded', function() {
    const themeToggles = document.querySelectorAll('.theme-toggle');
    const themeIcons = document.querySelectorAll('.theme-toggle-icon');
    const htmlElement = document.documentElement;
    
    // 创建自定义事件
    const themeChangedEvent = new Event('themeChanged');

    // 获取当前主题
    function getCurrentTheme() {
        return getCookie('theme') || 'light';
    }

    // 设置Cookie
    function setCookie(name, value, days) {
        let expires = '';
        if (days) {
            const date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = '; expires=' + date.toUTCString();
        }
        document.cookie = name + '=' + (value || '') + expires + '; path=/';
    }

    // 获取Cookie
    function getCookie(name) {
        const nameEQ = name + '=';
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }
    
    // 清除内联样式
    function clearInlineStyles() {
        // 清除表格相关元素的内联样式
        const elementsToClean = document.querySelectorAll(`
            table, .table, .table-striped, .table-responsive, 
            thead, tbody, tr, th, td, 
            .card, .card-body, .card-header
        `);
        
        elementsToClean.forEach(el => {
            // 将内联样式重置为空字符串
            if (el && el.style) {
                el.style.cssText = '';
            }
        });
        
        // 特殊处理最近文章表格
        const recentPostsTable = document.getElementById('recent-posts-table');
        if (recentPostsTable) {
            recentPostsTable.style.cssText = '';
            
            // 确保表格条纹样式正确应用
            if (!recentPostsTable.classList.contains('table-striped')) {
                recentPostsTable.classList.add('table-striped');
            }
            
            // 清除表格所有后代元素的内联样式
            const tableElements = recentPostsTable.querySelectorAll('*');
            tableElements.forEach(el => {
                if (el && el.style) {
                    el.style.cssText = '';
                }
            });
        }
    }

    // 切换主题
    function toggleTheme() {
        const currentTheme = getCurrentTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        // 清除所有内联样式
        clearInlineStyles();
        
        // 更新Cookie
        setCookie('theme', newTheme, 365);
        
        // 更新HTML类
        if (newTheme === 'dark') {
            document.documentElement.classList.add('dark-theme');
            themeIcons.forEach(icon => {
                icon.classList.remove('bi-moon-fill');
                icon.classList.add('bi-sun-fill');
            });
        } else {
            document.documentElement.classList.remove('dark-theme');
            themeIcons.forEach(icon => {
                icon.classList.remove('bi-sun-fill');
                icon.classList.add('bi-moon-fill');
            });
        }
        
        // 延迟触发事件，确保DOM更新完成
        setTimeout(function() {
            document.dispatchEvent(themeChangedEvent);
        }, 100);
    }

    // 应用当前主题
    function applyCurrentTheme() {
        const currentTheme = getCurrentTheme();
        
        // 清除所有内联样式
        clearInlineStyles();
        
        if (currentTheme === 'dark') {
            document.documentElement.classList.add('dark-theme');
            themeIcons.forEach(icon => {
                icon.classList.remove('bi-moon-fill');
                icon.classList.add('bi-sun-fill');
            });
        } else {
            document.documentElement.classList.remove('dark-theme');
            themeIcons.forEach(icon => {
                icon.classList.remove('bi-sun-fill');
                icon.classList.add('bi-moon-fill');
            });
        }
        
        // 触发主题变更事件
        document.dispatchEvent(themeChangedEvent);
    }

    // 应用当前主题
    applyCurrentTheme();

    // 添加点击事件
    themeToggles.forEach(toggle => {
        toggle.addEventListener('click', toggleTheme);
    });
}); 