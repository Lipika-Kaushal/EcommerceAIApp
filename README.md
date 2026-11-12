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

The storefront calls these APIs over HTTP. The services own separate SQLite
databases, and checkout reserves inventory before saving an order. Local
product photographs are in `static/products/`.

## Run locally with Docker Compose

Requirements: Docker Desktop with Docker Compose. From this directory:

```powershell
docker compose up --build
```

Open **http://localhost:5001**. The app uses port 5001 so it can run alongside
the original single-app demo on port 5000. Add items to the bag, view
recommendations, and place a demo order to see the catalog, cart, recommendation,
order, and inventory services work together.

Use `docker compose ps` to check the six running containers (the five APIs and
the storefront gateway). Stop the app with `Ctrl+C`, or run
`docker compose down`; the named local data volume is preserved.

## Run tests

```powershell
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

Create the Flask session secret and deploy the workloads:

```powershell
$secret = python -c "import secrets; print(secrets.token_hex(32))"
kubectl create secret generic goodfind-secrets --from-literal="flask-secret-key=$secret"
kubectl apply -f deployment.yaml -f service.yaml
kubectl get services storefront
```

The storefront Service is `type: LoadBalancer`; use its `EXTERNAL-IP` (or
cluster-provider hostname) as the app URL. The five API Services are internal
`ClusterIP` endpoints. The Deployment manifest includes persistent volume
claims for the catalog, cart, order, and inventory SQLite databases. SQLite
storage is configured for one replica per service; use a managed database
before scaling services horizontally.

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
