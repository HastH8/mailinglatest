
function hideNotification() {
    setTimeout(() => {
      const notification = document.querySelector('.notification');
      if (notification) notification.style.display = 'none';
    }, 5000);
  }

  function toggleTheme() {
    const isDarkMode = document.body.classList.toggle('dark-mode');
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
    document.getElementById('theme-toggle').checked = isDarkMode;
  }

  function applyTheme() {
    const savedTheme = localStorage.getItem('theme');
    const isDarkMode = savedTheme === 'dark';
    document.body.classList.toggle('dark-mode', isDarkMode);
    document.getElementById('theme-toggle').checked = isDarkMode;
  }

  function openModal() {
    document.getElementById("modal").style.display = "block";
  }
  
  function closeModal() {
    document.getElementById("modal").style.display = "none";
  }
  
  document.addEventListener("keydown", function(event) {
    if (event.key === "Escape") {
      closeModal();
    }
  });

  function toggleProfileMenu() {
    const menu = document.getElementById("profile-menu");
    menu.style.display = menu.style.display === "block" ? "none" : "block";
}

window.addEventListener("click", function(event) {
    const menu = document.getElementById("profile-menu");
    const profilePic = document.querySelector(".profile-pic");

    if (event.target !== menu && event.target !== profilePic && !menu.contains(event.target)) {
        menu.style.display = "none";
    }
});

function startTutorial() {
  introJs().start();
}

document.addEventListener("DOMContentLoaded", function () {
  const notification = document.querySelector(".notification");
  if (notification) {
    setTimeout(() => {
      notification.style.display = "none";
    }, 15000); 
  }

});