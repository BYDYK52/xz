function createCard(product) {
  return `
    <div class="tg_bot_card">
      <h3 class="bot_name">${product.title}</h3>
      <p class="bot_description">${product.content}</p>
      <div class="bot_footer">
        <span class="bot_price">$${product.price}</span>
        <button type="button" class="bot_order_btn" data-bot="${product.title}">Заказать</button>
      </div>
    </div>
  `;
}

// Получаем один продукт по id
const productId = 1; // замените на нужный id

fetch(`/api/v1/product_detail/${productId}`)
  .then(response => {
    if (!response.ok) {
      throw new Error(`Ошибка HTTP: ${response.status}`);
    }
    return response.json();
  })
  .then(product => {
    const container = document.getElementById('products');
    container.innerHTML = createCard(product);
  })
  .catch(error => {
    console.error('Ошибка загрузки продукта:', error);
  });



fetch('/api/v1/products/')
  .then(response => response.json())
  .then(products => {
    const container = document.getElementById('products');
    container.innerHTML = products.map(createCard).join('');
  })
  .catch(error => console.error('Ошибка загрузки продуктов:', error));
