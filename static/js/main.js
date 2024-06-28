document.addEventListener('DOMContentLoaded', function() {
    const clientButton = document.querySelector('#client-button');
    const waiterButton = document.querySelector('#waiter-button');
    clientButton.addEventListener('click', function() {
        window.location.href = '/register?user_type=client';
    });
    waiterButton.addEventListener('click', function() {
        window.location.href = '/register?user_type=waiter';
    });
});
