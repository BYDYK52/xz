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

const productId = 1; // You can change this as needed

// Fetch and display a single product detail
fetch('http://127.0.0.1:8000/api/v1/product_detail/' + productId)
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

// Fetch and display list of products
fetch('http://127.0.0.1:8000/api/v1/products/')
  .then(response => {
    if (!response.ok) {
      throw new Error(`Ошибка HTTP: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    console.log('API response for products:', data); // Debug: check structure

    const container = document.getElementById('products');

    // Check if products are inside 'results' or data itself is an array
    const productsArray = Array.isArray(data) ? data : data.results;

    if (Array.isArray(productsArray)) {
      container.innerHTML = productsArray.map(createCard).join('');
    } else {
      console.error('Ошибка: products is not an array.', productsArray);
      container.innerHTML = '<p>Не удалось загрузить список продуктов.</p>';
    }
  })
  .catch(error => {
    console.error('Ошибка загрузки продуктов:', error);
    const container = document.getElementById('products');
    container.innerHTML = '<p>Ошибка при загрузке продуктов.</p>';
  });
