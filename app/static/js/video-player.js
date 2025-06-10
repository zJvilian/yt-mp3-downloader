// Video player modal using Video.js

document.addEventListener('DOMContentLoaded', function() {
  const modal = document.getElementById('video-modal');
  const closeBtn = document.getElementById('video-modal-close');
  let player;

  if (window.videojs) {
    player = window.videojs('video-player');
  } else {
    player = document.getElementById('video-player');
  }

  function showModal(src) {
    if (player.src) {
      player.src({ type: 'video/mp4', src: src });
      player.play();
    } else {
      player.setAttribute('src', src);
      player.play();
    }
    modal.classList.add('active');
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', function() {
      modal.classList.remove('active');
      if (player.pause) player.pause();
    });
  }

  // Close the modal when clicking outside the video container
  modal.addEventListener('click', function(e) {
    if (e.target === modal) {
      modal.classList.remove('active');
      if (player.pause) player.pause();
    }
  });

  // Allow closing with the Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
      modal.classList.remove('active');
      if (player.pause) player.pause();
    }
  });

  window.initVideoButton = function(button) {
    if (!button) return;
    button.addEventListener('click', function(e) {
      e.preventDefault();
      const src = button.getAttribute('data-video-src');
      showModal(src);
    });
  };

  document.querySelectorAll('.yt-btn-video-play').forEach(btn => {
    window.initVideoButton(btn);
  });
});
