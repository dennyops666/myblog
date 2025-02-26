// 用户删除功能
function deleteUser(userId) {
    console.log('删除用户函数被调用，用户ID:', userId);
    
    // 查找删除表单
    var form = document.getElementById('delete-form-' + userId);
    if (!form) {
        console.log('找不到删除表单，表单ID:', 'delete-form-' + userId);
        showErrorAlert('删除操作失败：找不到删除表单');
        return;
    }

    // 显示确认对话框
    showDeleteConfirmDialog(userId, function() {
        console.log('用户确认删除，准备提交表单...');
        try {
            // 确保表单方法为POST
            form.method = 'post';
            // 提交表单
            form.submit();
            console.log('表单已提交');
        } catch (error) {
            console.error('删除操作出错:', error);
            showErrorAlert('删除操作失败：' + error.message);
        }
    });
}

// 显示删除确认对话框
function showDeleteConfirmDialog(userId, callback) {
    // 创建模态对话框
    var modalHtml = `
        <div class="modal fade" id="deleteConfirmModal" tabindex="-1" aria-labelledby="deleteConfirmModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="deleteConfirmModalLabel">确认删除</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        确定要删除这个用户吗？此操作不可恢复！
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="button" class="btn btn-danger" id="confirmDeleteBtn">删除</button>
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
    var modal = new bootstrap.Modal(modalElement);

    // 绑定确认按钮事件
    modalElement.querySelector('#confirmDeleteBtn').onclick = function() {
        modal.hide();
        callback();
    };

    // 显示模态框
    modal.show();
}

// 显示错误提示
function showErrorAlert(message) {
    var alertHtml = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    document.querySelector('.container-fluid').insertAdjacentHTML('afterbegin', alertHtml);
}

// 在页面加载完成后检查所有删除表单
document.addEventListener('DOMContentLoaded', function() {
    var forms = document.querySelectorAll('form[id^="delete-form-"]');
    console.log('找到删除表单数量:', forms.length);
    
    forms.forEach(function(form) {
        console.log('表单信息:', {
            id: form.id,
            action: form.action,
            method: form.method,
            csrfToken: form.querySelector('input[name="csrf_token"]')?.value || '不存在'
        });
    });
}); 