document.addEventListener('DOMContentLoaded', function() {
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
        window.location.href = '/login';
    }

    fetch('/api/profile/', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    })
    .then(response => response.json())
    .then(data => {
        const profileContent = document.querySelector('#profile-content');
        profileContent.innerHTML = `
            <p>Nickname: ${data.nickname}</p>
            <p>Payment Method: ${data.payment_method_id}</p>
        `;
    });
});
