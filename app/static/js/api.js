/**
 * Handles API calls for file operations
 */

// Delete file function
function deleteFile(type, filename, itemId) {
  if (confirm(`Are you sure you want to delete ${filename}?`)) {
    fetch(`/delete/${type}/${encodeURIComponent(filename)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Remove the element from the DOM
        const element = document.getElementById(itemId);
        if (element) {
          element.style.animation = 'fadeOut 0.3s ease-in-out';
          setTimeout(() => element.remove(), 300);
        }
      } else {
        alert(`Error deleting file: ${data.error || 'Unknown error'}`);
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('Failed to delete file. Please try again.');
    });
  }
}

// Function for download cancellation
function cancelDownload(downloadId) {
  if (confirm("Are you sure you want to cancel this download?")) {
    fetch(`/cancel/${downloadId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Remove the download from the list
        const element = document.getElementById(`download-${downloadId}`);
        if (element) {
          element.remove();
        }
      } else {
        alert("Failed to cancel download.");
      }
    })
    .catch(error => {
      console.error("Error cancelling download:", error);
      alert("Error cancelling download. See console for details.");
    });
  }
}