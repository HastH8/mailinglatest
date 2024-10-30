function hideNotification() {
    setTimeout(function() {
      const notification = document.querySelector('.notification');
      if (notification) {
        notification.style.display = 'none';
      }
    }, 5000); // 5000 ms = 5 seconds
  }