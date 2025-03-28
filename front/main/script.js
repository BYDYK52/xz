document.querySelectorAll('.highlight').forEach(element => {
    element.addEventListener('mouseenter', () => {
        const word = element.getAttribute('data-word');
        highlightWord(word);
    });

    element.addEventListener('mouseleave', () => {
        const word = element.getAttribute('data-word');
        removeHighlight(word);
    });
});

function highlightWord(word) {
    document.querySelectorAll(.highlight[data-word="${word}"]).forEach(el => {
        el.classList.add('highlighted');
    });
}

function removeHighlight(word) {
    document.querySelectorAll(.highlight[data-word="${word}"]).forEach(el => {
        el.classList.remove('highlighted');
    });
}
