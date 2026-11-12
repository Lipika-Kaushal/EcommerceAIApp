# Goodfind AI Product Recommendations

A small Flask e-commerce demo with an open product catalog, session-based cart,
and item-to-item product recommendations. Add items to your bag to personalize
recommendations from products bought together in sample shopping history.
Suggestions include an explanation; the cart works without a username or password.
Real product photos are included as local files, so images work without external
image services. The photos are sourced from Unsplash and used under the
[Unsplash License](https://unsplash.com/license).

## Run locally

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 to browse the 10-product collection. Add a product to your bag,
then select **For you** to see recommendations shaped by your current cart.
The app initializes a set of illustrative products and sample shopper
purchase records on first run and creates `ecommerce.db` in this folder.

Set `DATABASE_PATH` to use a different SQLite file, and set `FLASK_SECRET_KEY`
to a private, persistent random value outside local development.

## Run tests

```powershell
python -m unittest discover -s tests
```

## Deploy to Azure App Service

Deploy this folder as a Python App Service application. Set
`SCM_DO_BUILD_DURING_DEPLOYMENT=true`, configure a private `FLASK_SECRET_KEY`,
and set `DATABASE_PATH` to a writable persistent location. Use this startup
command:

```text
gunicorn --bind=0.0.0.0 --timeout 600 app:app
```

The demo uses SQLite and illustrative sample data; use a managed database and
production-grade authentication before deploying a real storefront.

## Product photo sources

- Laptop: [Unsplash](https://unsplash.com/photos/macbook-pro-on-table-1496181133206-80ce9b88a853)
- Mobile: [Unsplash](https://unsplash.com/photos/black-android-smartphone-1511707171634-5f897ff02aa9)
- Keyboard: [Unsplash](https://unsplash.com/photos/white-computer-keyboard-1587829741301-dc798b83add3)
- Mouse: [Unsplash](https://unsplash.com/photos/white-and-black-computer-mouse-1527814050087-3793815479db)
- Headphones: [Unsplash](https://unsplash.com/photos/black-wireless-headphones-1505740420928-5e560c06d30e)
- Smartwatch: [Unsplash](https://unsplash.com/photos/round-white-smartwatch-1523275335684-37898b6baf30)
- Camera: [Unsplash](https://unsplash.com/photos/black-dslr-camera-1516035069371-29a1b244cc32)
- Speaker: [Unsplash](https://unsplash.com/photos/black-portable-speaker-1608043152269-423dbba4e7e1)
- Tablet: [Unsplash](https://unsplash.com/photos/black-tablet-computer-1544244015-0df4b3ffc6b0)
- Backpack: [Unsplash](https://unsplash.com/photos/black-backpack-1553062407-98eeb64c6a62)
