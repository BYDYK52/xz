function smoothScrollTo(targetOrPosition, duration = 1500, offset = 0) {
  const start = window.pageYOffset;
  let targetPosition;

  if (typeof targetOrPosition === 'number') {
    // If a number is passed, use it directly as the target scroll position
    targetPosition = targetOrPosition + offset;
  } else {
    // Otherwise, calculate the element's position plus offset
    targetPosition = targetOrPosition.getBoundingClientRect().top + start + offset;
  }

  const distance = targetPosition - start;
  let startTime = null;

  function animation(currentTime) {
    if (!startTime) startTime = currentTime;
    const timeElapsed = currentTime - startTime;

    // EaseInOutCubic easing function for smooth animation
    const ease = (t) =>
      t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

    const progress = Math.min(timeElapsed / duration, 1);
    const easedProgress = ease(progress);

    window.scrollTo(0, start + distance * easedProgress);

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
    const offset = 10; // 10 pixels offset upwards (adjust as needed)

    if (targetId === 'top') {
      // Scroll to very top of the page with offset
      smoothScrollTo(0, 2000, offset);
    } else {
      const target = document.getElementById(targetId);
      if (target) {
        smoothScrollTo(target, 2000, offset);
      }
    }
  });
});
