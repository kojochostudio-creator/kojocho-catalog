(function () {
  "use strict";

  var target = document.getElementById("collection-products");
  var status = document.getElementById("collection-status");
  var collectionId = document.body.dataset.collectionId;

  function text(element, value) {
    element.textContent = value;
    return element;
  }

  function storeLink(label, url) {
    var link = document.createElement("a");
    link.className = "store-link";
    link.href = url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    return text(link, label);
  }

  function productCard(product) {
    var card = document.createElement("article");
    card.className = "product-card";
    var image = document.createElement("img");
    image.src = "../" + product.cover_image;
    image.alt = product.title_en;
    image.loading = "lazy";
    card.appendChild(image);
    var content = document.createElement("div");
    content.className = "product-content";
    content.appendChild(text(document.createElement("h2"), product.title_en)).className = "title-en";
    content.appendChild(text(document.createElement("p"), product.title_jp)).className = "title-jp";
    var prices = document.createElement("p");
    prices.className = "prices";
    text(prices, "BOOTH: " + product.booth_price + "  |  itch.io: " + product.itch_price);
    content.appendChild(prices);
    var links = document.createElement("div");
    links.className = "store-links";
    links.appendChild(storeLink("BOOTH", product.booth_url));
    links.appendChild(storeLink("itch.io", product.itch_url));
    content.appendChild(links);
    card.appendChild(content);
    return card;
  }

  Promise.all([fetch("../products.json"), fetch("../site_taxonomy.json")])
    .then(function (responses) {
      if (responses.some(function (response) { return !response.ok; })) throw new Error("catalog data unavailable");
      return Promise.all(responses.map(function (response) { return response.json(); }));
    })
    .then(function (data) {
      var products = data[0];
      var collections = data[1].collections;
      var collection = collections.find(function (entry) { return entry.id === collectionId; });
      if (!collection || !Array.isArray(collection.product_ids)) throw new Error("collection unavailable");
      var byId = new Map(products.map(function (product) { return [product.id, product]; }));
      var selected = collection.product_ids.map(function (id) { return byId.get(id); });
      if (selected.some(function (product) { return !product || !product.booth_url || !product.itch_url || !product.cover_image; })) {
        throw new Error("collection product unavailable");
      }
      selected.forEach(function (product) { target.appendChild(productCard(product)); });
      text(status, selected.length + " collection assets");
    })
    .catch(function (error) {
      console.error(error.message);
      text(status, "Collection data could not be loaded.");
    });
}());
