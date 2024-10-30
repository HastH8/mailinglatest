function hideNotification() {
    setTimeout(() => {
      const notification = document.querySelector('.notification');
      if (notification) notification.style.display = 'none';
    }, 5000);
  }