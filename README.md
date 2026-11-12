# Goodfind: five e-commerce microservices

Goodfind is a small Flask storefront backed by five independently runnable
domain services. The browser-facing storefront is an API gateway; it is not one
of the five domain microservices.

| Microservice | Responsibility |
|---|---|
| Catalog | Product details and prices |
| Cart | Shopper carts and item quantities |
| Recommendations | Cart-driven item-to-item recommendations |
| Orders | Checkout, order records, and purchase history |
| Inventory | Available stock and checkout reservations |

The storefront calls these APIs over HTTP. The Cart, Orders, and Inventory
services store relational data in PostgreSQL. Catalog stores product documents
in MongoDB, while Recommendations computes suggestions from Catalog and Orders
APIs. Checkout reserves inventory before saving an order. Local product
photographs are in `static/products/`.

# Goodfind — AI-Assisted E-Commerce Application

Goodfind is a demo e-commerce application with a Flask storefront and five backend microservices. It lets shoppers browse products, manage a cart, view recommendations, and place orders.

The recommendation feature uses cart contents and sample co-purchase history to suggest related products. It is a lightweight, data-driven recommendation approach—not a trained machine-learning model or an LLM.

## Architecture

```text
Shopper's browser
       |
       v
Flask Storefront / API Gateway
       |
       +---- Catalog Service ------------ MongoDB
       |
       +---- Cart Service --------------- PostgreSQL
       |
       +---- Recommendations Service ---- Catalog + Orders APIs
       |
       +---- Orders Service ------------- PostgreSQL
       |          |
       |          +---- Inventory Service
       |
       +---- Inventory Service ---------- PostgreSQL
```

The storefront handles the browser interface and forwards requests to the backend services over HTTP. The services use databases behind their APIs; the storefront does not connect directly to either database.

### Microservices

| Service | Responsibility | Storage |
|---|---|---|
| **Catalog** | Provides product listings and product details. | MongoDB product documents |
| **Cart** | Adds, retrieves, and removes products in a shopper’s cart, including quantities. | PostgreSQL |
| **Recommendations** | Suggests products based on cart contents and co-purchase patterns in sample order history. | Uses the Catalog and Orders APIs |
| **Orders** | Handles checkout, stores orders and sample purchase history, and coordinates inventory reservation. | PostgreSQL |
| **Inventory** | Tracks available stock and reserves or releases stock for orders. | PostgreSQL |

The services share product IDs through their APIs. Product details live in MongoDB; PostgreSQL stores related cart, order, and inventory records. The order stores a snapshot of the purchased item details.

### Database choices

- **MongoDB** stores Catalog products as documents.
- **PostgreSQL** stores Cart, Orders, and Inventory data in relational tables. Transactions help keep checkout and stock updates consistent.
- PostgreSQL and MongoDB are separate services in the local Compose stack. They are not exposed as public web endpoints.

## Checkout flow

1. The shopper adds a product to their cart.
2. The Cart service validates the product through the Catalog API and saves the cart item.
3. The Recommendations service can use cart items and order-history patterns to suggest related products.
4. At checkout, Orders retrieves the cart and product details.
5. Orders asks Inventory to reserve the requested quantities.
6. If the reservation succeeds, Orders saves the order and clears the cart.

## Run locally with Docker Compose

Requirements: Docker Desktop with Docker Compose.

From this directory, run:

```powershell
docker compose up --build
```

Open the storefront at **http://localhost:5001**.

The Compose stack runs eight containers:

- Storefront
- Five microservices
- PostgreSQL
- MongoDB

Check container status with:

```powershell
docker compose ps
```

Stop the stack with `Ctrl+C`, or in another terminal run:

```powershell
docker compose down
```

The named database volumes are preserved when the containers stop. Do not use `docker compose down -v` unless you intend to delete the local database data.

The Compose file has development-only credentials for convenience. Change them before using this stack beyond a local demo.

## Inspect the databases

Open a PostgreSQL shell:

```powershell
docker compose exec postgres psql -U goodfind -d goodfind
```

List tables in PostgreSQL:

```sql
\dt
```

Example queries:

```sql
SELECT * FROM orders;
SELECT * FROM order_items;
SELECT * FROM inventory;
SELECT * FROM cart_items;
SELECT * FROM sample_purchases LIMIT 10;
```

Exit `psql` with:

```text
\q
```

Inspect products in MongoDB:

```powershell
docker compose exec mongodb mongosh --username goodfind --password local-demo-password --authenticationDatabase admin
```

Then, in `mongosh`:

```javascript
use goodfind_catalog
db.products.find({}, { _id: 0 }).sort({ id: 1 })
```

Exit with:

```text
exit
```

## Run tests

Install the Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the unit and service integration tests:

```powershell
python -m unittest discover -s tests -v
```

## Deploy to Kubernetes

The Kubernetes manifests are:

- `deployment.yaml` — application Deployments and PostgreSQL/MongoDB StatefulSets with persistent volume claims.
- `service.yaml` — internal services for the APIs and databases, plus a `LoadBalancer` service for the storefront.

For a remote cluster, build and push the application image to a container registry accessible to that cluster, then update the application image references in `deployment.yaml`.

Create the required Kubernetes secret values before applying the manifests. For example, in PowerShell:

```powershell
$flaskSecret = python -c "import secrets; print(secrets.token_hex(32))"
$postgresPassword = python -c "import secrets; print(secrets.token_urlsafe(32))"
$mongoPassword = python -c "import secrets; print(secrets.token_urlsafe(32))"

kubectl create secret generic goodfind-secrets `
  --from-literal="flask-secret-key=$flaskSecret" `
  --from-literal="postgres-user=goodfind" `
  --from-literal="postgres-password=$postgresPassword" `
  --from-literal="mongo-user=goodfind" `
  --from-literal="mongo-password=$mongoPassword"
```

Apply the manifests:

```powershell
kubectl apply -f deployment.yaml -f service.yaml
kubectl get services
```

The storefront’s `LoadBalancer` service will receive a public address from a supported cluster provider. The databases and microservice APIs remain internal to the cluster. Cluster creation, image-registry setup, and cloud deployment are separate steps.

For production on Azure, consider managed services such as Azure Database for PostgreSQL and Azure Cosmos DB for MongoDB.

## Project structure

```text
newAIapplicationAzure/
├── app.py                         # Flask storefront and API gateway
├── catalog_data.py                # Demo products and sample purchase history
├── recommender.py                 # Recommendation ranking logic
├── microservices/
│   ├── catalog.py                 # MongoDB-backed Catalog API
│   ├── cart.py                    # PostgreSQL-backed Cart API
│   ├── recommendations.py         # Recommendation API
│   ├── orders.py                  # PostgreSQL-backed Orders API
│   ├── inventory.py               # PostgreSQL-backed Inventory API
│   └── common.py                  # Shared database, HTTP, and API helpers
├── templates/                     # Storefront pages
├── static/                        # CSS and product images
├── tests/                         # Unit and integration tests
├── Dockerfile
├── compose.yaml
├── deployment.yaml
├── service.yaml
└── requirements.txt
```

## Repository

Source code: [Lipika-Kaushal/EcommerceAIApp](https://github.com/Lipika-Kaushal/EcommerceAIApp)

## Run locally with Docker Compose

Requirements: Docker Desktop with Docker Compose. From this directory:

```powershell
docker compose up --build
```

Open **http://localhost:5001**. The app uses port 5001 so it can run alongside
the original single-app demo on port 5000. Add items to the bag, view
recommendations, and place a demo order to see the catalog, cart, recommendation,
order, and inventory services work together.

Use `docker compose ps` to check the eight running containers (the five APIs,
the storefront gateway, PostgreSQL, and MongoDB). Stop the app with `Ctrl+C`,
or run `docker compose down`; the database volumes are preserved.

Compose uses development-only database credentials by default. Set
`POSTGRES_PASSWORD`, `MONGO_PASSWORD`, and `FLASK_SECRET_KEY` in the environment
before starting the stack if you need non-demo local credentials.

## Run tests

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

## Build and deploy to Kubernetes

Build the same application image used for every service:

```powershell
docker build -t goodfind-ecommerce:latest .
```

For a remote Kubernetes cluster, push that image to a registry accessible by
the cluster and update the image in `deployment.yaml` to the pushed image name.
For a local cluster, make the locally built image available to that cluster
(for example, load it into Minikube or kind).

Create the application and database credentials, then deploy the workloads:

```powershell
$secret = python -c "import secrets; print(secrets.token_hex(32))"
$postgresPassword = python -c "import secrets; print(secrets.token_urlsafe(32))"
$mongoPassword = python -c "import secrets; print(secrets.token_urlsafe(32))"
kubectl create secret generic goodfind-secrets `
  --from-literal="flask-secret-key=$secret" `
  --from-literal="postgres-user=goodfind" `
  --from-literal="postgres-password=$postgresPassword" `
  --from-literal="mongo-user=goodfind" `
  --from-literal="mongo-password=$mongoPassword"
kubectl apply -f deployment.yaml -f service.yaml
kubectl get services storefront
```

The storefront Service is `type: LoadBalancer`; use its `EXTERNAL-IP` (or
cluster-provider hostname) as the app URL. The five API Services and both
database Services are internal `ClusterIP` endpoints. The PostgreSQL and
MongoDB StatefulSets each request persistent storage. For production Azure
deployments, consider managed Azure Database for PostgreSQL and Azure Cosmos DB
for MongoDB rather than running database containers in the cluster.

## Product photo sources

Photos are sourced from Unsplash and used under the
[Unsplash License](https://unsplash.com/license).

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
