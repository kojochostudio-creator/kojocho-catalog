(function () {
  "use strict";

  var mainFeature = document.getElementById("main-feature");
  var secondaryFeatures = document.getElementById("secondary-features");
  var collectionFilters = document.getElementById("collection-filters");
  var selectedList = document.getElementById("product-list");
  var exploreToggle = document.getElementById("explore-toggle");
  var status = document.getElementById("catalog-status");
  var selectedProducts = [];
  var selectedIsAll = true;
  var exploreExpanded = false;
  var productPages = new Map([
    [91, "rpg-icons-bundle"],
    [92, "grimoires-arcane-research"],
    [96, "workshop-props-bundle"],
    [98, "sake-brewery-props"],
    [101, "showa-retro-sento-props"]
  ]);

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

  function productCard(product, collectionLabel, variant) {
    var card = document.createElement("article");
    card.className = "product-card" + (variant ? " " + variant : "");

    var image = document.createElement("img");
    image.src = product.cover_image;
    image.alt = product.title_en;
    image.loading = "lazy";
    card.appendChild(image);

    var content = document.createElement("div");
    content.className = "product-content";
    if (collectionLabel) {
      content.appendChild(text(document.createElement("p"), collectionLabel)).className = "collection-label";
    }
    content.appendChild(text(document.createElement("h3"), product.title_en)).className = "title-en";
    content.appendChild(text(document.createElement("p"), product.title_jp)).className = "title-jp";
    var prices = document.createElement("p");
    prices.className = "prices";
    text(prices, "BOOTH: " + product.booth_price + "  |  itch.io: " + product.itch_price);
    content.appendChild(prices);
    var productPageSlug = productPages.get(product.id);
    if (productPageSlug) {
      var detail = document.createElement("a");
      detail.className = "product-detail-link";
      detail.href = "products/" + productPageSlug + "/";
      text(detail, "View details");
      content.appendChild(detail);
    }
    var links = document.createElement("div");
    links.className = "store-links";
    links.appendChild(storeLink("BOOTH · JPY", product.booth_url));
    links.appendChild(storeLink("itch.io · USD", product.itch_url));
    content.appendChild(links);
    card.appendChild(content);
    return card;
  }

  function idList(value, label) {
    if (!Array.isArray(value) || value.some(function (id) { return !Number.isInteger(id); })) {
      throw new Error(label + " must be an array of product IDs");
    }
    return value;
  }

  function collectionProducts(collection, config, byId) {
    var ids = collection.uses_site_config_new_release_ids === true
      ? idList(config.new_release_ids, "new_release_ids")
      : idList(collection.product_ids, collection.label + " product_ids");
    return ids.map(function (id) {
      if (!byId.has(id)) {
        console.warn("Ignoring collection product ID absent from the public assortment:", id);
        return null;
      }
      return byId.get(id);
    }).filter(Boolean);
  }

  function renderShelf(collection, products) {
    var target = document.getElementById("shelf-" + collection.id);
    if (!target) return;
    target.replaceChildren();
    products.slice(0, collection.id === "bundles" ? 4 : 6).forEach(function (product) {
      target.appendChild(productCard(product, collection.label, "shelf-card"));
    });
  }

  function renderSelected() {
    selectedList.replaceChildren();
    var visible = selectedIsAll && !exploreExpanded ? selectedProducts.slice(0, 8) : selectedProducts;
    visible.forEach(function (product) {
      selectedList.appendChild(productCard(product, selectedIsAll ? "" : selectedProducts.collectionLabel, ""));
    });
    text(status, visible.length + " of " + selectedProducts.length + " selected assets");
    exploreToggle.hidden = !selectedIsAll || selectedProducts.length <= 8;
    text(exploreToggle, exploreExpanded ? "Show Less" : "View All Selected Assets");
  }

  function renderCollectionControls(collections, products) {
    var activeId = "all";
    var allButton = document.createElement("button");
    allButton.type = "button";
    allButton.className = "category-filter";
    allButton.dataset.collectionId = "all";
    text(allButton, "All Selected");
    collectionFilters.appendChild(allButton);

    collections.forEach(function (collection) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "category-filter";
      button.dataset.collectionId = collection.id;
      text(button, collection.label);
      collectionFilters.appendChild(button);
    });

    function setActive(collectionId, shouldScroll) {
      activeId = collectionId;
      Array.from(collectionFilters.querySelectorAll("button")).forEach(function (button) {
        button.setAttribute("aria-pressed", String(button.dataset.collectionId === activeId));
      });
      var selectedCollection = collections.find(function (collection) { return collection.id === activeId; });
      selectedProducts = selectedCollection ? selectedCollection.products.slice() : products.slice();
      selectedProducts.collectionLabel = selectedCollection ? selectedCollection.label : "";
      selectedIsAll = !selectedCollection;
      exploreExpanded = false;
      renderSelected();
      if (shouldScroll) {
        document.getElementById("selected-assets").scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }

    Array.from(collectionFilters.querySelectorAll("button")).forEach(function (button) {
      button.addEventListener("click", function () { setActive(button.dataset.collectionId, true); });
    });
    setActive("all", false);
  }

  function validateFeatures(config, byId) {
    if (!Number.isInteger(config.main_feature_id)) {
      throw new Error("main_feature_id must be a product ID");
    }
    if (!byId.has(config.main_feature_id)) {
      throw new Error("main_feature_id is absent from the public assortment");
    }
    var secondaryIds = idList(config.secondary_feature_ids, "secondary_feature_ids");
    if (secondaryIds.length > 2) {
      throw new Error("secondary_feature_ids supports at most two products");
    }
    return {
      main: byId.get(config.main_feature_id),
      secondary: secondaryIds.map(function (id) {
        if (!byId.has(id)) throw new Error("secondary feature is absent from the public assortment: " + id);
        return byId.get(id);
      })
    };
  }

  Promise.all([fetch("products.json"), fetch("site_config.json"), fetch("site_taxonomy.json")])
    .then(function (responses) {
      if (responses.some(function (response) { return !response.ok; })) {
        throw new Error("catalog data unavailable");
      }
      return Promise.all(responses.map(function (response) { return response.json(); }));
    })
    .then(function (data) {
      var products = data[0];
      var config = data[1];
      var taxonomy = data[2];
      var byId = new Map(products.map(function (product) { return [product.id, product]; }));
      var collectionDefinitions = Array.isArray(taxonomy.collections) ? taxonomy.collections : [];
      var collections = collectionDefinitions.map(function (collection) {
        return {
          id: collection.id,
          label: collection.label,
          products: collectionProducts(collection, config, byId)
        };
      });
      if (collections.length !== 7) throw new Error("expected seven customer collections");

      var features = validateFeatures(config, byId);
      var mainCollection = collections.find(function (collection) {
        return collection.products.some(function (product) { return product.id === features.main.id; });
      });
      mainFeature.appendChild(productCard(features.main, mainCollection ? mainCollection.label : "", "main-feature-card"));
      features.secondary.forEach(function (product) {
        var collection = collections.find(function (entry) {
          return entry.products.some(function (item) { return item.id === product.id; });
        });
        secondaryFeatures.appendChild(productCard(product, collection ? collection.label : "", "secondary-feature-card"));
      });

      ["bundles", "rpg-ui-icons", "japanese-props", "workshops-shops", "new-releases"].forEach(function (id) {
        var collection = collections.find(function (entry) { return entry.id === id; });
        if (!collection || !collection.products.length) throw new Error("required collection is empty: " + id);
        renderShelf(collection, collection.products);
      });
      renderCollectionControls(collections, products);
      exploreToggle.addEventListener("click", function () {
        exploreExpanded = !exploreExpanded;
        renderSelected();
      });
    })
    .catch(function (error) {
      console.error(error.message);
      text(status, "Catalog data could not be loaded.");
    });
}());
