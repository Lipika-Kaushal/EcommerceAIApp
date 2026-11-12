from collections import Counter, defaultdict


def build_recommendations(
    products: list[dict],
    interests: list[int],
    purchases: list[dict],
    limit: int = 5,
) -> list[dict]:
    """Recommend items bought with the shopper's selected product IDs."""
    selected = set(interests)
    popularity = Counter(purchase["product_id"] for purchase in purchases)
    co_purchases = defaultdict(Counter)

    customer_purchases = defaultdict(set)
    for purchase in purchases:
        customer_purchases[purchase["customer_id"]].add(purchase["product_id"])
    for customer_products in customer_purchases.values():
        for source in customer_products:
            co_purchases[source].update(customer_products - {source})

    scores = Counter()
    reasons = {}
    for source in selected:
        for candidate, score in co_purchases[source].items():
            if candidate not in selected:
                scores[candidate] += score
                if candidate not in reasons or score > reasons[candidate][0]:
                    reasons[candidate] = (score, source)

    product_by_id = {product["id"]: product for product in products}
    ranked = sorted(
        (product for product in products if product["id"] not in selected),
        key=lambda product: (
            -scores[product["id"]],
            -popularity[product["id"]],
            product["id"],
        ),
    )

    recommendations = []
    for product in ranked[: max(0, limit)]:
        product_id = product["id"]
        if scores[product_id]:
            source_name = product_by_id[reasons[product_id][1]]["name"]
            reason = f"Often bought alongside {source_name}"
        elif popularity[product_id]:
            reason = "Popular with other shoppers"
        else:
            reason = "A great place to start"
        recommendations.append({**product, "reason": reason})
    return recommendations
