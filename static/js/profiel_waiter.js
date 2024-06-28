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
            <p>First Name: ${data.first_name}</p>
            <p>Last Name: ${data.last_name}</p>
            <p>Workplace: ${data.workplace}</p>
            <p>QR Code: <img src="${data.qr_code}" alt="QR Code"></p>
        `;
    });
});
