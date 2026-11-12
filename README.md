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
