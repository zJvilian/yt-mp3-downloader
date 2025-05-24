/**
 * Handles real-time updates via Server-Sent Events
 */

document.addEventListener("DOMContentLoaded", () => {
  // Check if the browser supports EventSource for SSE
  if (typeof EventSource !== "undefined") {
    setupSSE();
  } else {
    // Fallback to polling for older browsers
    setupPolling();
  }
  
  function setupSSE() {
    const evtSource = new EventSource("/events");
    
    evtSource.onmessage = function(event) {
      const data = JSON.parse(event.data);
      
      if (data.type === "heartbeat") {
        return; // Just a keepalive message
      }
      
      updateFilesList(data);
    };
    
    evtSource.onerror = function(err) {
      console.error("SSE Error:", err);
      evtSource.close();
      
      // Fallback to polling if SSE fails - reduced wait time
      setTimeout(() => {
        setupPolling();
      }, 1000); // Reduced from 5000ms to 1000ms for faster recovery
    };
    
    // Close EventSource when the page is unloaded
    window.addEventListener('beforeunload', () => {
      evtSource.close();
    });
  }
  
  function setupPolling() {
    // Poll for changes more frequently (every 1 second instead of 5)
    const intervalId = setInterval(pollForChanges, 1000);
    
    // Clear interval when the page is unloaded
    window.addEventListener('beforeunload', () => {
      clearInterval(intervalId);
    });
  }
  
  function pollForChanges() {
    fetch('/api/file-list')
      .then(response => response.json())
      .then(data => {
        updateFilesList(data);
      })
      .catch(error => {
        console.error("Polling error:", error);
      });
  }
  
  function updateFilesList(data) {
    // Update MP3 files
    updateFileList('mp3-list', data.mp3_files, createMP3Item);
    
    // Update MP4 files
    updateFileList('mp4-list', data.mp4_files, createMP4Item);
    
    // Update active downloads
    updateActiveDownloads(data.active_downloads);
  }
  
  function updateFileList(listId, files, createItemFunc) {
    const list = document.getElementById(listId);
    if (!list) return;
    
    // Clear existing "No files" message if present
    const emptyMessage = list.querySelector('.yt-list-empty');
    if (emptyMessage && files.length > 0) {
      emptyMessage.remove();
    }
    
    // Get current file elements
    const currentFiles = Array.from(list.querySelectorAll('.yt-list-item'))
      .map(item => {
        const filename = item.querySelector('.yt-filename').textContent;
        return { element: item, filename: filename };
      });
    
    // Add new files
    files.forEach((filename, index) => {
      const existing = currentFiles.find(item => item.filename === filename);
      
      if (!existing) {
        const newItem = createItemFunc(filename, index);
        list.appendChild(newItem);
      }
    });
    
    // Remove files that no longer exist
    currentFiles.forEach(item => {
      if (!files.includes(item.filename)) {
        item.element.style.animation = 'fadeOut 0.3s ease-in-out';
        setTimeout(() => {
          if (item.element.parentNode === list) {
            item.element.remove();
          }
          
          // Add empty message if no files left
          if (list.children.length === 0) {
            const emptyMessage = document.createElement('li');
            emptyMessage.className = 'yt-list-empty';
            emptyMessage.textContent = `No ${listId === 'mp3-list' ? 'MP3s' : 'MP4s'} yet.`;
            list.appendChild(emptyMessage);
          }
        }, 300);
      }
    });
  }
  
  function createMP3Item(filename, index) {
    const li = document.createElement('li');
    li.className = 'yt-list-item';
    li.id = `mp3-item-${index + 1}`;
    li.innerHTML = `
      <button
        class="yt-btn yt-btn-play"
        data-audio-src="/mp3s/${encodeURIComponent(filename)}"
        data-audio-title="${filename}"
        aria-label="Play/Pause"
      >▶</button>
      <span class="yt-filename">${filename}</span>
      <div class="yt-item-actions">
        <a
          href="/mp3s/${encodeURIComponent(filename)}"
          download
          class="yt-btn yt-btn-download"
          aria-label="Download"
        >⬇</a>
        <button
          class="yt-btn yt-btn-delete"
          onclick="deleteFile('mp3', '${filename}', 'mp3-item-${index + 1}')"
          aria-label="Delete"
        >🗑️</button>
      </div>
    `;
    // Animation for new items
    li.style.animation = 'fadeIn 0.3s ease-in-out';
    
    // Attach event listener to the play button
    const playBtn = li.querySelector('.yt-btn-play');
    attachPlayButtonHandler(playBtn);
    
    return li;
  }
  
  function createMP4Item(filename, index) {
    const li = document.createElement('li');
    li.className = 'yt-list-item';
    li.id = `mp4-item-${index + 1}`;
    li.innerHTML = `
      <span class="yt-icon">🎬</span>
      <span class="yt-filename">${filename}</span>
      <div class="yt-item-actions">
        <a
          href="/mp4s/${encodeURIComponent(filename)}"
          download
          class="yt-btn yt-btn-download"
          aria-label="Download"
        >⬇</a>
        <button
          class="yt-btn yt-btn-delete"
          onclick="deleteFile('mp4', '${filename}', 'mp4-item-${index + 1}')"
          aria-label="Delete"
        >🗑️</button>
      </div>
    `;
    // Animation for new items
    li.style.animation = 'fadeIn 0.3s ease-in-out';
    return li;
  }
  
  function updateActiveDownloads(activeDownloads) {
    const section = document.getElementById('active-downloads-section');
    const list = document.getElementById('active-downloads-list');
    
    if (!section || !list) return;
    
    // Show/hide the section based on whether there are active downloads
    const downloadCount = Object.keys(activeDownloads).length;
    section.style.display = downloadCount > 0 ? 'block' : 'none';
    
    if (downloadCount === 0) {
      // Clear the list if no active downloads
      list.innerHTML = '';
      return;
    }
    
    // Get current download elements
    const currentDownloads = Array.from(list.querySelectorAll('.yt-list-item'))
      .map(item => {
        const id = item.id.replace('download-', '');
        return { element: item, id: id };
      });
    
    // Add new downloads
    for (const [id, download] of Object.entries(activeDownloads)) {
      if (download.status === 'downloading') {
        const existing = currentDownloads.find(item => item.id === id);
        
        if (!existing) {
          const newItem = document.createElement('li');
          newItem.className = 'yt-list-item';
          newItem.id = `download-${id}`;
          newItem.innerHTML = `
            <div class="loader">
              <div class="loader-square"></div>
              <div class="loader-square"></div>
              <div class="loader-square"></div>
              <div class="loader-square"></div>
              <div class="loader-square"></div>
              <div class="loader-square"></div>
              <div class="loader-square"></div>
            </div>
            <span class="yt-filename">${download.url} (${download.format})</span>
            <button 
              class="yt-btn yt-btn-cancel" 
              data-download-id="${id}"
              aria-label="Cancel"
              onclick="cancelDownload('${id}')"
            >✖</button>
          `;
          list.appendChild(newItem);
        }
      }
    }
    
    // Remove completed/cancelled downloads
    currentDownloads.forEach(item => {
      const id = item.id;
      if (!activeDownloads[id] || activeDownloads[id].status !== 'downloading') {
        item.element.style.animation = 'fadeOut 0.3s ease-in-out';
        setTimeout(() => {
          if (item.element.parentNode === list) {
            item.element.remove();
          }
          
          // Hide section if no downloads left
          if (list.children.length === 0) {
            section.style.display = 'none';
          }
        }, 300);
      }
    });
  }
  
  function attachPlayButtonHandler(button) {
    // Copy event handler from player.js
    button.addEventListener("click", function(event) {
      event.preventDefault();
      event.stopPropagation();
      
      const audioSrc = this.getAttribute('data-audio-src');
      const audioTitle = this.getAttribute('data-audio-title');
      const globalPlayer = document.getElementById("global-audio-player");
      const globalPlayerContainer = document.getElementById("global-player-container");
      const nowPlayingTitle = document.getElementById("now-playing-title");
      
      // If this is already playing, toggle play/pause
      if (globalPlayer.src.endsWith(encodeURIComponent(audioTitle))) {
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
      
      // Try to play
      globalPlayer.load();
      globalPlayer.play().then(() => {
        this.textContent = "⏸";
        
        // Mark this item as playing
        const listItem = this.closest('.yt-list-item');
        if (listItem) {
          // Remove "playing" class from all items
          document.querySelectorAll('.yt-list-item.playing').forEach(item => {
            item.classList.remove('playing');
          });
          
          // Add "playing" class to this item
          listItem.classList.add('playing');
        }
      }).catch(err => {
        console.error("Error playing audio:", err);
        this.textContent = "▶"; // Reset to play button if there's an error
        alert("Unable to play audio. This may be due to browser autoplay restrictions or a network issue.");
      });
    });
  }
});