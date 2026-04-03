// cart.js - версия для работы с Django БД

// Функция для получения CSRF-токена
function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === 'csrftoken=') {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCSRFToken();

// Обновление счетчика в шапке через API
function updateCartCounter() {
    fetch('/orders/api/cart/count/')
        .then(response => response.json())
        .then(data => {
            const counter = document.getElementById('cartCounter');
            if (counter) {
                const count = data.count || 0;
                counter.textContent = count;
                counter.style.display = count > 0 ? 'flex' : 'none';
            }
        })
        .catch(err => console.error('Ошибка обновления счетчика:', err));
}

// Добавление в корзину (AJAX)
function addToCart(dishId, quantity = 1, dishName = '') {
    fetch(`/orders/cart/add/${dishId}/?quantity=${quantity}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification(`🍽️ ${dishName || 'Блюдо'} добавлен в корзину (${quantity} шт.)`);
            updateCartCounter();
            return data;
        } else {
            showNotification(`Ошибка: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        showNotification('Ошибка при добавлении в корзину', 'error');
    });
}

// Удаление из корзины (AJAX)
function removeFromCart(itemId, itemName) {
    showConfirmModal(`Удалить "${itemName}" из корзины?`, function() {
        fetch(`/orders/cart/remove/${itemId}/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Удаляем элемент из DOM
                const cartItem = document.getElementById(`cart-item-${itemId}`);
                if (cartItem) cartItem.remove();
                showNotification(`"${itemName}" удален из корзины`);
                updateCartCounter();
                
                // Обновляем итоговые суммы на странице корзины
                if (typeof updateTotals === 'function') {
                    updateTotals();
                }
                
                // Если корзина пуста, перезагружаем страницу
                if (document.querySelectorAll('.cart-item').length === 0) {
                    setTimeout(() => window.location.reload(), 1000);
                }
            }
        })
        .catch(error => console.error('Ошибка:', error));
        closeConfirmModal();
    });
}

// Изменение количества (AJAX)
function updateCartQuantity(itemId, newQuantity) {
    fetch(`/orders/cart/update/${itemId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: `quantity=${newQuantity}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const qtySpan = document.getElementById(`quantity-value-${itemId}`);
            const totalSpan = document.getElementById(`item-total-${itemId}`);
            if (qtySpan) qtySpan.textContent = data.new_quantity;
            if (totalSpan) totalSpan.textContent = data.item_total + '₽';
            if (typeof updateTotals === 'function') {
                updateTotals();
            }
            updateCartCounter();
        } else if (data.status === 'deleted') {
            const cartItem = document.getElementById(`cart-item-${itemId}`);
            if (cartItem) cartItem.remove();
            if (typeof updateTotals === 'function') {
                updateTotals();
            }
            updateCartCounter();
        }
    })
    .catch(error => console.error('Ошибка:', error));
}

// Уведомление
function showNotification(message, type = 'success') {
    const oldNotifications = document.querySelectorAll('.custom-notification');
    oldNotifications.forEach(notif => notif.remove());
    
    const notification = document.createElement('div');
    notification.className = 'custom-notification';
    const bgColor = type === 'error' ? '#dc3545' : '#800020';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${bgColor};
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        z-index: 2000;
        animation: slideIn 0.3s ease;
        font-size: 0.95rem;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

// Модальное окно подтверждения
const confirmModal = document.getElementById('confirmModal');
let pendingAction = null;

window.showConfirmModal = function(message, onConfirm) {
    const confirmMessage = document.getElementById('confirmMessage');
    if (confirmMessage) confirmMessage.textContent = message;
    pendingAction = onConfirm;
    if (confirmModal) confirmModal.classList.add('active');
}

window.closeConfirmModal = function() {
    if (confirmModal) confirmModal.classList.remove('active');
    pendingAction = null;
}

window.confirmAction = function() {
    if (pendingAction) {
        pendingAction();
        closeConfirmModal();
    }
}

// Добавляем стили для анимации
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
if (!document.querySelector('style[data-cart-animation]')) {
    style.setAttribute('data-cart-animation', 'true');
    document.head.appendChild(style);
}

// Обработчики для модального окна
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('confirmModal');
    if (modal) {
        const overlay = modal.querySelector('.modal-overlay');
        const cancelBtn = modal.querySelector('.confirm-cancel');
        const okBtn = modal.querySelector('.confirm-ok');
        
        if (overlay) overlay.addEventListener('click', closeConfirmModal);
        if (cancelBtn) cancelBtn.addEventListener('click', closeConfirmModal);
        if (okBtn) okBtn.addEventListener('click', confirmAction);
        
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') closeConfirmModal();
        });
    }
    
    // Обновляем счетчик при загрузке
    updateCartCounter();
});

// Делаем функции глобальными
window.updateCartCounter = updateCartCounter;
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
window.updateCartQuantity = updateCartQuantity;
window.showNotification = showNotification;