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
let catalog = false;

document.getElementById("tg_bot_button_catalog").onclick = function() {
  catalog = !catalog;
  console.log("Значение переменной catalog изменено на:", catalog);

  const catalogTitle = document.querySelector('.catalog_title');
  if (catalog) {
    catalogTitle.style.display = 'block';
  } else {
    catalogTitle.style.display = 'none';
  }
};



let order = false;

document.getElementById("tg_bot_button_order").onclick = function() {
  order = !order;
  console.log("Значение переменной order изменено на:", order);

  const catalogTitle = document.querySelector('.mine_bot');
  if (order) {
    catalogTitle.style.display = 'block';
  } else {
    catalogTitle.style.display = 'none';
  }
};
  const catalogTitle = document.querySelector('.mine_bot_2');
  if (order) {
    catalogTitle.style.display = 'block';
  } else {
    catalogTitle.style.display = 'none';
  }
};
