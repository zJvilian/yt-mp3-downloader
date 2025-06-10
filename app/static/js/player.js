// Initialize player on DOM content loaded
document.addEventListener("DOMContentLoaded", () => {
  const playButtons = document.querySelectorAll(".yt-btn-play");
  const globalPlayer = document.getElementById("global-audio-player");
  const globalPlayerContainer = document.getElementById("global-player-container");
  const nowPlayingTitle = document.getElementById("now-playing-title");
  const currentTimeLabel = document.getElementById("current-time");
  const durationTimeLabel = document.getElementById("duration");
  const progressBar = document.getElementById("audio-progress");
  const progressContainer = document.querySelector(".yt-progress");
  const volumeSlider = document.getElementById("volume-slider");
  const muteButton = document.getElementById("mute-button");
  const playPauseGlobal = document.getElementById("play-pause-global");
  
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
    
    // Also update the global play/pause button
    if (playPauseGlobal) {
      playPauseGlobal.textContent = isPlaying ? "⏸" : "▶";
    }
  }
  
  // Format time in MM:SS format
  function formatTime(seconds) {
    if (isNaN(seconds)) return "0:00";
    
    seconds = Math.floor(seconds);
    const minutes = Math.floor(seconds / 60);
    seconds = seconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }
  
  // Update time display and progress bar
  function updateTimeDisplay() {
    if (!globalPlayer.duration) return;
    
    const currentTime = globalPlayer.currentTime || 0;
    const duration = globalPlayer.duration || 0;
    
    // Update text labels
    currentTimeLabel.textContent = formatTime(currentTime);
    durationTimeLabel.textContent = formatTime(duration);
    
    // Update progress bar
    const percent = (currentTime / duration) * 100;
    if (progressBar) {
      progressBar.style.width = `${percent}%`;
    }
    
    // Update grabber position
    const progressGrabber = document.getElementById('audio-progress-grabber');
    if (progressGrabber) {
      progressGrabber.style.left = `${percent}%`;
    }
  }
  
  // Handle progress bar clicks
  if (progressContainer) {
    progressContainer.addEventListener('click', (e) => {
      const bounds = progressContainer.getBoundingClientRect();
      const x = e.clientX - bounds.left;
      const percent = x / bounds.width;
      
      globalPlayer.currentTime = percent * globalPlayer.duration;
      updateTimeDisplay();
    });
  }
  
  // Handle global play/pause button
  if (playPauseGlobal) {
    playPauseGlobal.addEventListener('click', () => {
      if (globalPlayer.paused) {
        globalPlayer.play();
      } else {
        globalPlayer.pause();
      }
    });
  }
  
  // Handle volume slider
  if (volumeSlider) {
    const volumeBar = volumeSlider.querySelector('.yt-progress-bar');
    
    volumeSlider.addEventListener('click', (e) => {
      const bounds = volumeSlider.getBoundingClientRect();
      const x = e.clientX - bounds.left;
      const volumeLevel = Math.max(0, Math.min(1, x / bounds.width));
      
      globalPlayer.volume = volumeLevel;
      volumeBar.style.width = `${volumeLevel * 100}%`;
      
      // Update volume grabber position
      const volumeGrabber = document.getElementById('volume-grabber');
      if (volumeGrabber) {
        volumeGrabber.style.left = `${volumeLevel * 100}%`;
      }
      
      // Update mute button state
      if (muteButton) {
        muteButton.textContent = volumeLevel === 0 ? '🔇' : '🔊';
      }
    });
  }
  
  // Handle mute button
  if (muteButton) {
    muteButton.addEventListener('click', () => {
      globalPlayer.muted = !globalPlayer.muted;
      muteButton.textContent = globalPlayer.muted ? '🔇' : '🔊';
    });
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
  
  // Handle timeupdate for progress bar and time display
  globalPlayer.addEventListener('timeupdate', updateTimeDisplay);
  
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
      if (nowPlayingTitle) nowPlayingTitle.textContent = audioTitle;
      
      // Update the currently playing reference
      currentlyPlaying = this;
      
      // Show loading state
      this.innerHTML = `
        <div class="loader loader-btn">
          <div class="loader-square"></div>
          <div class="loader-square"></div>
          <div class="loader-square"></div>
          <div class="loader-square"></div>
          <div class="loader-square"></div>
          <div class="loader-square"></div>
          <div class="loader-square"></div>
        </div>
      `;
      
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
        this.textContent = "▶"; // Reset to play button if there's an error
        alert("Unable to play audio. This may be due to browser autoplay restrictions or a network issue.");
      });
    });
  });
  
  // Fix: Directly initialize the grabbers here (don't use nested DOMContentLoaded)
  const audioGrabber = document.getElementById('audio-progress-grabber');
  const volumeGrabber = document.getElementById('volume-grabber');
  
  if (audioGrabber) {
    enableDragging(audioGrabber, 'audio');
    console.log("Audio grabber initialized");
  } else {
    console.warn("Audio grabber element not found");
  }
  
  if (volumeGrabber) {
    enableDragging(volumeGrabber, 'volume');
    console.log("Volume grabber initialized");
  } else {
    console.warn("Volume grabber element not found");
  }

  function enableDragging(grabber, type) {
    let isDragging = false;
    
    // Mouse events
    grabber.addEventListener('mousedown', startDrag);
    
    // Touch events for mobile support
    grabber.addEventListener('touchstart', (e) => {
      const touch = e.touches[0];
      startDrag({ 
        clientX: touch.clientX,
        preventDefault: () => e.preventDefault()
      });
    });
    
    function startDrag(e) {
      isDragging = true;
      
      // Add event listeners for mouse/touch move and end
      document.addEventListener('mousemove', handleDrag);
      document.addEventListener('touchmove', handleTouchDrag, { passive: false });
      document.addEventListener('mouseup', stopDrag);
      document.addEventListener('touchend', stopDrag);
      
      // Prevent default to avoid text selection
      e.preventDefault();
      
      // Handle the initial drag position
      if (type === 'audio') {
        handleAudioDrag(e.clientX);
      } else if (type === 'volume') {
        handleVolumeDrag(e.clientX);
      }
    }
    
    function handleTouchDrag(e) {
      e.preventDefault(); // Prevent scrolling while dragging
      if (!isDragging) return;
      
      const touch = e.touches[0];
      if (type === 'audio') {
        handleAudioDrag(touch.clientX);
      } else if (type === 'volume') {
        handleVolumeDrag(touch.clientX);
      }
    }
    
    function handleDrag(e) {
      if (!isDragging) return;
      
      if (type === 'audio') {
        handleAudioDrag(e.clientX);
      } else if (type === 'volume') {
        handleVolumeDrag(e.clientX);
      }
    }
    
    function handleAudioDrag(clientX) {
      const progressContainer = document.querySelector('.yt-progress');
      const bounds = progressContainer.getBoundingClientRect();
      const percent = Math.max(0, Math.min(1, (clientX - bounds.left) / bounds.width));
      
      // Update time and UI immediately for smooth dragging
      globalPlayer.currentTime = percent * globalPlayer.duration;
      
      // Update the progress bar and grabber positions directly
      if (progressBar) {
        progressBar.style.width = `${percent * 100}%`;
      }
      
      grabber.style.left = `${percent * 100}%`;
      
      // Update time display
      if (currentTimeLabel && globalPlayer.currentTime) {
        currentTimeLabel.textContent = formatTime(globalPlayer.currentTime);
      }
    }
    
    function handleVolumeDrag(clientX) {
      const volumeSlider = document.getElementById('volume-slider');
      const bounds = volumeSlider.getBoundingClientRect();
      const percent = Math.max(0, Math.min(1, (clientX - bounds.left) / bounds.width));
      
      // Update volume and UI
      globalPlayer.volume = percent;
      
      // Update volume bar width
      const volumeBar = volumeSlider.querySelector('.yt-progress-bar');
      if (volumeBar) {
        volumeBar.style.width = `${percent * 100}%`;
      }
      
      // Update grabber position
      grabber.style.left = `${percent * 100}%`;
      
      // Update mute button
      if (muteButton) {
        muteButton.textContent = percent < 0.05 ? '🔇' : '🔊';
      }
    }
    
    function stopDrag() {
      if (!isDragging) return;
      
      isDragging = false;
      
      // Remove event listeners
      document.removeEventListener('mousemove', handleDrag);
      document.removeEventListener('touchmove', handleTouchDrag);
      document.removeEventListener('mouseup', stopDrag);
      document.removeEventListener('touchend', stopDrag);
      
      // Final update for both audio and volume
      if (type === 'audio') {
        updateTimeDisplay();
      }
    }
  }
  
  // Previous track button functionality
  const previousTrackBtn = document.getElementById('previous-track');
  if (previousTrackBtn) {
    previousTrackBtn.addEventListener('click', () => {
      if (!currentlyPlaying) return; // Do nothing if no track is playing
      
      const allTracks = Array.from(document.querySelectorAll('.yt-btn-play'));
      const currentIndex = allTracks.indexOf(currentlyPlaying);
      
      if (currentIndex > 0) {
        // There's a previous track - play it
        const previousTrack = allTracks[currentIndex - 1];
        previousTrack.click(); // Trigger the click event on the previous track
      }
    });
  }
  
  // Next track button functionality
  const nextTrackBtn = document.getElementById('next-track');
  if (nextTrackBtn) {
    nextTrackBtn.addEventListener('click', () => {
      if (!currentlyPlaying) return; // Do nothing if no track is playing
      
      const allTracks = Array.from(document.querySelectorAll('.yt-btn-play'));
      const currentIndex = allTracks.indexOf(currentlyPlaying);
      
      if (currentIndex < allTracks.length - 1) {
        // There's a next track - play it
        const nextTrack = allTracks[currentIndex + 1];
        nextTrack.click(); // Trigger the click event on the next track
      }
    });
  }
});
