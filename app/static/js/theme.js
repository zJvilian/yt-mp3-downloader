/**
 * Handles theme toggling functionality
 */

document.addEventListener("DOMContentLoaded", () => {
  const themeCheckbox = document.getElementById('theme-checkbox');
  const body = document.body;
  
  // Check for saved theme preference or default to system preference
  function getInitialTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      return savedTheme;
    }
    
    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    
    return 'light';
  }
  
  // Apply theme
  function applyTheme(theme) {
    body.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    // Update checkbox state (checked = light theme, unchecked = dark theme)
    themeCheckbox.checked = theme === 'light';
  }
  
  // Initialize theme
  const initialTheme = getInitialTheme();
  applyTheme(initialTheme);
  
  // Toggle theme on checkbox change
  themeCheckbox.addEventListener('change', () => {
    // Checkbox checked = light theme, unchecked = dark theme
    const newTheme = themeCheckbox.checked ? 'light' : 'dark';
    applyTheme(newTheme);
  });
  
  // Listen for system theme changes
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      // Only auto-switch if user hasn't manually set a preference
      if (!localStorage.getItem('theme')) {
        applyTheme(e.matches ? 'dark' : 'light');
      }
    });
  }
});