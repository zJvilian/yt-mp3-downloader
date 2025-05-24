/**
 * Handles audio player functionality
 */

// Initialize player on DOM content loaded
document.addEventListener("DOMContentLoaded", () => {
  const playButtons = document.querySelectorAll(".yt-btn-play");
  const globalPlayer = document.getElementById("global-audio-player");
  const globalPlayerContainer = document.getElementById("global-player-container");
  const nowPlayingTitle = document.getElementById("now-playing-title");
  const currentTimeLabel = document.getElementById("current-time");
  const durationTimeLabel = document.getElementById("duration-time");
  const pinPlayerButton = document.getElementById("pin-player-button");
  let currentlyPlaying = null;
  
  // Function to update UI when a song is playing
  function updatePlayingState(button, isPlaying) {
    // Update all buttons first (reset them)
    playButtons.forEach(btn => {
      btn.textContent = "▶";
      const listItem = btn.closest('.yt-list-item');
      if (listItem) listItem.classList.remove('playing');
    });
    
    // Then update the currently playing one if applicable
    if (button && isPlaying) {
      button.textContent = "⏸";
      const listItem = button.closest('.yt-list-item');
      if (listItem) listItem.classList.add('playing');
    }
  }
  
  // Format time in MM:SS format
  function formatTime(seconds) {
    seconds = Math.floor(seconds);
    const minutes = Math.floor(seconds / 60);
    seconds = seconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }
  
  // Update time display
  function updateTimeDisplay() {
    if (!globalPlayer.duration) return;
    
    currentTimeLabel.textContent = formatTime(globalPlayer.currentTime);
    durationTimeLabel.textContent = formatTime(globalPlayer.duration);
  }
  
  // Handle player events directly from the audio element
  globalPlayer.addEventListener('play', () => {
    updatePlayingState(currentlyPlaying, true);
  });
  
  globalPlayer.addEventListener('pause', () => {
    updatePlayingState(currentlyPlaying, false);
  });
  
  globalPlayer.addEventListener('ended', () => {
    updatePlayingState(currentlyPlaying, false);
  });
  
  // Set up play button click handlers
  playButtons.forEach(button => {
    button.addEventListener("click", function(event) {
      event.preventDefault();
      event.stopPropagation();
      
      const audioSrc = this.getAttribute('data-audio-src');
      const audioTitle = this.getAttribute('data-audio-title');
      
      // If this is the current track, just toggle play/pause
      if (currentlyPlaying === this) {
        if (globalPlayer.paused) {
          globalPlayer.play();
        } else {
          globalPlayer.pause();
        }
        return;
      }
      
      // Otherwise, load and play the new track
      globalPlayer.src = audioSrc;
      nowPlayingTitle.textContent = audioTitle;
      globalPlayerContainer.style.display = 'flex';
      
      // Update the currently playing reference
      currentlyPlaying = this;
      
      // Show loading state
      this.textContent = "⏳";
      
      // Try to extract artwork for the player if available
      const playerArt = document.querySelector('.yt-global-player-art');
      if (playerArt && audioTitle) {
        // Generate a color based on the song name
        const hash = audioTitle.split('').reduce((acc, char) => {
          return acc + char.charCodeAt(0);
        }, 0);
        
        const hue = hash % 360;
        playerArt.style.background = `hsl(${hue}, 70%, 50%)`;
      }
      
      // Play and handle states
      globalPlayer.load();
      globalPlayer.play().then(() => {
        updatePlayingState(this, true);
      }).catch(err => {
        console.error("Error playing audio:", err);
        updatePlayingState(this, false);
        alert("Unable to play audio. This may be due to browser autoplay restrictions or a network issue.");
      });
    });
  });
  
  // Update current time and duration display
  globalPlayer.addEventListener('loadedmetadata', () => {
    durationTimeLabel.textContent = formatTime(globalPlayer.duration);
  });
  
  globalPlayer.addEventListener('timeupdate', () => {
    currentTimeLabel.textContent = formatTime(globalPlayer.currentTime);
  });
  
  // Pin player to bottom feature
  pinPlayerButton.addEventListener('click', () => {
    const isPinned = globalPlayerContainer.classList.toggle('pinned');
    pinPlayerButton.textContent = isPinned ? '📍' : '📌';
    pinPlayerButton.title = isPinned ? 'Unpin player' : 'Pin player to bottom';
    
    // Save preference to localStorage
    localStorage.setItem('player-pinned', isPinned ? 'true' : 'false');
    
    // If pinned, ensure player is visible
    if (isPinned && globalPlayerContainer.style.display === 'none') {
      globalPlayerContainer.style.display = 'block';
    }
  });
  
  // Restore pinned state if previously set
  if (localStorage.getItem('player-pinned') === 'true') {
    globalPlayerContainer.classList.add('pinned');
    pinPlayerButton.textContent = '📍';
    pinPlayerButton.title = 'Unpin player';
  }
});