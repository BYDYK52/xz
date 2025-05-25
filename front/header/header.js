function smoothScrollTo(targetOrPosition, duration = 1500, offset = 0) {
  const start = window.pageYOffset;
  let targetPosition;

  if (typeof targetOrPosition === 'number') {
    // If a number is passed, use it directly as the target scroll position + offset
    targetPosition = targetOrPosition + offset;
  } else {
    // Calculate the element's position relative to the document + offset
    targetPosition = targetOrPosition.getBoundingClientRect().top + window.pageYOffset + offset;
  }

  // Clamp targetPosition to valid scroll range (0 to max scroll)
  const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
  targetPosition = Math.min(Math.max(targetPosition, 0), maxScroll);

  const distance = targetPosition - start;
  let startTime = null;

  // Easing function (easeInOutCubic)
  const ease = (t) =>
    t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

  function animation(currentTime) {
    if (!startTime) startTime = currentTime;
    const timeElapsed = currentTime - startTime;
    const progress = Math.min(timeElapsed / duration, 1);
    const easedProgress = ease(progress);
    const currentScroll = start + distance * easedProgress;

    window.scrollTo(0, currentScroll);

    if (timeElapsed < duration) {
      requestAnimationFrame(animation);
    }
  }

  requestAnimationFrame(animation);
}

// Attach event listeners to all buttons with class 'scroll-btn'
document.querySelectorAll('.scroll-btn').forEach(button => {
  button.addEventListener('click', () => {
    const targetId = button.getAttribute('data-target');
    const offset = 10; // Scroll 10px above the target element

    if (targetId === 'top') {
      smoothScrollTo(0, 2000, offset);
    } else {
      const target = document.getElementById(targetId);
      if (target) {
        smoothScrollTo(target, 2000, offset);
      }
    }
  });
});
