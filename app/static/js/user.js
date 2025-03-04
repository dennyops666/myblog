// 用户删除功能
function deleteUser(userId) {
    const form = document.getElementById(`delete-form-${userId}`);
    if (!form) {
        showToast('error', '删除操作失败：找不到删除表单');
        return;
    }

    // 使用自定义确认对话框
    showDeleteConfirmDialog(userId, () => {
        // 发送删除请求
        fetch(form.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('success', data.message);
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showToast('error', data.message || '删除失败');
            }
        })
        .catch(error => {
            console.error('删除请求失败:', error);
            showToast('error', '删除失败，请稍后重试');
        });
    });
}

// 显示删除确认对话框
function showDeleteConfirmDialog(userId, callback) {
    // 创建模态对话框
    var modalHtml = `
        <div class="modal fade" id="deleteConfirmModal" tabindex="-1" aria-labelledby="deleteConfirmModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="deleteConfirmModalLabel">确认删除</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p class="mb-2">确定要删除这个用户吗？</p>
                        <p class="text-danger mb-0"><small>此操作不可恢复！</small></p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-danger" id="confirmDeleteBtn">
                            <i class="bi bi-trash"></i> 确认删除
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // 如果已存在模态框，则移除
    var existingModal = document.getElementById('deleteConfirmModal');
    if (existingModal) {
        existingModal.remove();
    }

    // 添加模态框到页面
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // 获取模态框实例
    var modalElement = document.getElementById('deleteConfirmModal');
    var modal = new bootstrap.Modal(modalElement, {
        backdrop: 'static',  // 点击背景不关闭
        keyboard: false      // 按ESC键不关闭
    });

    // 绑定确认按钮事件
    modalElement.querySelector('#confirmDeleteBtn').onclick = function() {
        modal.hide();
        callback();
    };

    // 显示模态框
    modal.show();

    // 模态框隐藏后自动删除
    modalElement.addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// 显示错误提示
function showToast(type, message) {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1050';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    const toastBody = document.createElement('div');
    toastBody.className = 'd-flex';
    toastBody.innerHTML = `
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    `;

    toast.appendChild(toastBody);
    document.getElementById('toast-container').appendChild(toast);

    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 3000
    });
    bsToast.show();

    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
        if (document.getElementById('toast-container').children.length === 0) {
            document.getElementById('toast-container').remove();
        }
    });
}

// 处理用户登录
async function handleLogin(event) {
    event.preventDefault();
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;

    // 禁用提交按钮
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 登录中...';

    try {
        const formData = new FormData(form);
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        });

        const data = await response.json();
        if (data.success) {
            showToast('success', data.message);
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 1000);
        } else {
            showToast('error', data.message);
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    } catch (error) {
        console.error('登录请求失败:', error);
        showToast('error', '登录请求失败，请稍后重试');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// 处理用户注册
async function handleRegister(event) {
    event.preventDefault();
    const form = event.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;

    // 禁用提交按钮
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 注册中...';

    try {
        const formData = new FormData(form);
        const response = await fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        });

        const data = await response.json();
        if (data.success) {
            showToast('success', data.message);
            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 1000);
        } else {
            showToast('error', data.message);
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    } catch (error) {
        console.error('注册请求失败:', error);
        showToast('error', '注册请求失败，请稍后重试');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// 处理表单提交
$(document).ready(function() {
    $('#userForm').on('submit', function(e) {
        e.preventDefault();
        
        var form = this;
        var submitBtn = $(form).find('button[type="submit"]');
        var originalText = submitBtn.html();
        
        // 禁用提交按钮
        submitBtn.prop('disabled', true);
        submitBtn.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 提交中...');
        
        // 使用FormData处理表单数据
        var formData = new FormData(form);
        
        $.ajax({
            url: $(form).attr('action'),
            type: 'POST',
            data: formData,
            processData: false,  // 不处理数据
            contentType: false,  // 不设置内容类型
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: function(response) {
                if (response.success) {
                    // 显示成功消息
                    showToast('success', response.message);
                    // 延迟跳转
                    setTimeout(function() {
                        window.location.href = response.redirect_url;
                    }, 1500);
                } else {
                    // 显示错误消息
                    showToast('error', response.message);
                    // 重置提交按钮
                    submitBtn.prop('disabled', false);
                    submitBtn.html(originalText);
                }
            },
            error: function(xhr, status, error) {
                // 显示错误消息
                showToast('error', '系统错误，请稍后重试');
                // 重置提交按钮
                submitBtn.prop('disabled', false);
                submitBtn.html(originalText);
                console.error('提交失败:', error);
            }
        });
    });
}); 