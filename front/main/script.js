//let catalog = false
//
//
//
//document.getElementById("tg_bot_button_catalog").onclick = function() {
//  catalog = true ;
//  console.log("Значение переменной успешно изменено!");
//};
//
//
//<script>
//  document.getElementById('tg_bot_button_catalog').addEventListener('click', function() {
//    const catalogTitle = document.querySelector('.catalog_title');
//    if (catalogTitle.style.display === 'none' || catalogTitle.style.display === '') {
//      catalogTitle.style.display = 'block'; // показываем элемент
//    } else {
//      catalogTitle.style.display = 'none'; // скрываем элемент (если нужно toggle)
//    }
//  });
//</script>
// --- Модальное окно "каталог" ---
const openBtnCatalog = document.getElementById('tg_bot_button_catalog');
const modalCatalog = document.getElementById('myModal_2');
const closeBtnCatalog = document.getElementById('closeModalBtn_2');

openBtnCatalog.addEventListener('click', () => {
  modalCatalog.style.display = 'flex';
  document.body.style.overflow = 'hidden';
});

closeBtnCatalog.addEventListener('click', () => {
  modalCatalog.style.display = 'none';
  document.body.style.overflow = '';
});

window.addEventListener('click', e => {
  if (e.target === modalCatalog) {
    modalCatalog.style.display = 'none';
    document.body.style.overflow = '';
  }
});

window.addEventListener('keydown', e => {
  if (e.key === 'Escape' && modalCatalog.style.display === 'flex') {
    modalCatalog.style.display = 'none';
    document.body.style.overflow = '';
  }
});

// --- Модальное окно "заказать" ---
const openBtnOrder = document.getElementById('tg_bot_button_order');
const modalOrder = document.getElementById('myModal');
const closeBtnOrder = document.getElementById('closeModalBtn');

openBtnOrder.addEventListener('click', () => {
  modalOrder.style.display = 'flex';
  document.body.style.overflow = 'hidden';
});

closeBtnOrder.addEventListener('click', () => {
  modalOrder.style.display = 'none';
  document.body.style.overflow = '';
});

window.addEventListener('click', e => {
  if (e.target === modalOrder) {
    modalOrder.style.display = 'none';
    document.body.style.overflow = '';
  }
});

window.addEventListener('keydown', e => {
  if (e.key === 'Escape' && modalOrder.style.display === 'flex') {
    modalOrder.style.display = 'none';
    document.body.style.overflow = '';
  }
});
