/**
 * Handles UI interactions like collapsible sections
 */

// Add fade out animation for deleted items
document.head.insertAdjacentHTML('beforeend', `
  <style>
    @keyframes fadeOut {
      from { opacity: 1; transform: translateY(0); }
      to { opacity: 0; transform: translateY(-10px); }
    }
  </style>
`);

// Section collapsing functionality
function toggleSection(sectionId) {
  const section = document.getElementById(sectionId);
  const sectionHeader = section.previousElementSibling;
  const isCollapsed = section.classList.toggle('collapsed');
  
  // Also add collapsed class to the header for styling
  sectionHeader.classList.toggle('collapsed');
  
  // Store the state in localStorage
  localStorage.setItem(`${sectionId}-collapsed`, isCollapsed);
}

// Initialize collapsed state from localStorage
document.addEventListener('DOMContentLoaded', function() {
  const sections = ['mp3-list', 'mp4-list'];
  
  sections.forEach(sectionId => {
    const isCollapsed = localStorage.getItem(`${sectionId}-collapsed`) === 'true';
    if (isCollapsed) {
      const section = document.getElementById(sectionId);
      const sectionHeader = section.previousElementSibling;
      
      section.classList.add('collapsed');
      sectionHeader.classList.add('collapsed');
    }
  });
});