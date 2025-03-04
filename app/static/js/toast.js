// 显示提示信息
function showToast(type, message) {
    // 创建 toast 容器（如果不存在）
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }

    // 创建 toast 元素
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    // 设置 toast 的内容
    const toastBody = document.createElement('div');
    toastBody.className = 'd-flex';
    toastBody.innerHTML = `
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    `;

    toast.appendChild(toastBody);
    container.appendChild(toast);

    // 初始化 Bootstrap toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 3000
    });

    // 显示 toast
    bsToast.show();

    // toast 隐藏后删除元素
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
        if (container.children.length === 0) {
            container.remove();
        }
    });
} 