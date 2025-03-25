/**
 * 主题切换器
 * 实现在浅色和深色主题之间切换的功能
 */
document.addEventListener('DOMContentLoaded', function() {
    initThemeSwitcher();
});

/**
 * 初始化主题切换功能
 */
function initThemeSwitcher() {
    // 从localStorage获取当前主题
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // 应用当前主题
    if (currentTheme === 'dark') {
        document.documentElement.classList.add('dark-theme');
    } else {
        document.documentElement.classList.remove('dark-theme');
    }
    
    // 更新主题图标
    updateThemeIcons(currentTheme);
    
    // 为所有主题切换按钮添加点击事件
    document.querySelectorAll('.theme-toggle').forEach(function(toggler) {
        toggler.addEventListener('click', function() {
            // 获取当前主题
            const isDarkTheme = document.documentElement.classList.contains('dark-theme');
            
            // 切换主题
            if (isDarkTheme) {
                document.documentElement.classList.remove('dark-theme');
                localStorage.setItem('theme', 'light');
                updateThemeIcons('light');
            } else {
                document.documentElement.classList.add('dark-theme');
                localStorage.setItem('theme', 'dark');
                updateThemeIcons('dark');
            }
        });
    });
}

/**
 * 更新所有主题图标
 */
function updateThemeIcons(theme) {
    document.querySelectorAll('.theme-toggle-icon').forEach(function(icon) {
        if (theme === 'dark') {
            icon.textContent = '切换到日间模式';
        } else {
            icon.textContent = '切换到夜间模式';
        }
    });
    
    // 更新图标样式
    document.querySelectorAll('.theme-toggle i').forEach(function(icon) {
        if (theme === 'dark') {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    });
} 