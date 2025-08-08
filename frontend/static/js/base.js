// 監聽側邊欄切換按鈕的點擊事件
document.getElementById('toggleSidebar').addEventListener('click', function () {
    document.getElementById('sidebar').classList.toggle('collapsed');
    document.querySelector('.main-content').classList.toggle('shifted');
});

// 監聽使用者頭像的點擊事件
document.getElementById('avatar').addEventListener('click', function (event) {
    event.stopPropagation();
    document.getElementById('userDropdown').classList.toggle('active');
});

// 監聽整個文檔（頁面任何地方）的點擊事件
document.addEventListener('click', function (e) {
    const avatarContainer = document.getElementById('avatar');
    const userDropdown = document.getElementById('userDropdown');

    if (!avatarContainer.contains(e.target) && !userDropdown.contains(e.target)) {
        userDropdown.classList.remove('active');;
    }
});