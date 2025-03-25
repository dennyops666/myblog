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

// Toast组件
const Toast = {
    container: null,
    
    init: function() {
        // 确保容器存在
        if (!$('#toast-container').length) {
            $('body').append('<div id="toast-container" class="toast-top-right"></div>');
        }
        this.container = $('#toast-container');
        this.container.empty();
    },
    
    show: function(type, message, duration = 3000) {
        if (!this.container) {
            this.init();
        }
        
        console.log('Showing toast:', type, message);
        
        // 清除同类型的旧提示
        this.container.find('.toast.' + type).remove();
        
        const toast = $('<div>')
            .addClass('toast ' + type)
            .html(`<span style="flex: 1">${message}</span>`)
            .appendTo(this.container);
        
        // 强制重绘
        toast[0].offsetHeight;
        
        // 显示toast
        toast.addClass('show');
        
        // 成功提示延长显示时间
        const showDuration = type === 'success' ? 4000 : duration;
        
        // 设置自动消失
        setTimeout(() => {
            toast.removeClass('show');
            setTimeout(() => toast.remove(), 400);
        }, showDuration);
    },
    
    success: function(message) {
        this.show('success', `
            <span style="
                font-size: 22px; 
                font-weight: 600; 
                text-shadow: 0 1px 2px rgba(0,0,0,0.15);
                letter-spacing: 0.5px;
            ">${message}</span>
        `, 5000);
    },
    
    error: function(message) {
        this.show('error', message);
    },
    
    info: function(message) {
        this.show('info', message);
    }
};

// 初始化全局 showToast 函数
window.showToast = function(type, message) {
    if (type === 'success') {
        Toast.success(message);
    } else if (type === 'error') {
        Toast.error(message);
    } else {
        Toast.info(message);
    }
};

// 等待 jQuery 加载完成后初始化 Toast
waitForJQuery(function() {
    $(document).ready(function() {
        Toast.init();
    });
}); 