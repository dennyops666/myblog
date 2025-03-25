// 切换主题
function toggleTheme() {
    if (document.documentElement.classList.contains('dark-theme')) {
        // 切换到浅色主题
        document.documentElement.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
        if (themeToggleIcon) {
            themeToggleIcon.textContent = '🌙';
        }
    } else {
        // 切换到深色主题
        document.documentElement.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
        if (themeToggleIcon) {
            themeToggleIcon.textContent = '☀️';
        }
        
        // 强制设置表格背景色
        setTimeout(function() {
            const tableElements = document.querySelectorAll('.card-body, .table-responsive, .table, tbody, tr, td');
            tableElements.forEach(el => {
                el.style.backgroundColor = '#1e1e1e';
            });
            
            // 特别处理最近文章表格
            const recentPostsCard = document.querySelector('.card-body.p-0');
            if (recentPostsCard) {
                recentPostsCard.style.backgroundColor = '#1e1e1e';
            }
            
            const tableResponsive = document.querySelector('.table-responsive');
            if (tableResponsive) {
                tableResponsive.style.backgroundColor = '#1e1e1e';
            }
            
            const recentPostsTable = document.getElementById('recent-posts-table');
            if (recentPostsTable) {
                recentPostsTable.style.backgroundColor = '#1e1e1e';
            }
            
            // 处理奇数行
            const oddRows = document.querySelectorAll('.table tbody tr:nth-child(odd)');
            oddRows.forEach(row => {
                row.style.backgroundColor = 'rgba(255, 255, 255, 0.03)';
            });
        }, 100);
    }
} 