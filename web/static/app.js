// Highlight current nav item
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname.split('/')[1];
  document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
    const href = link.getAttribute('href')?.replace('/', '');
    if (href && path === href) link.classList.add('active', 'fw-semibold');
  });
  if (!path) {
    document.querySelector('.navbar-brand')?.classList.add('active');
  }
});
