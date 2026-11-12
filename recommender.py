from collections import Counter, defaultdict
import sqlite3


def get_recommendations(
    connection: sqlite3.Connection, interests: list[str], limit: int = 5
) -> list[dict]:
    """Recommend products often bought alongside the shopper's selected items."""
    products = connection.execute(
        "SELECT id, name, price FROM products ORDER BY id"
    ).fetchall()
    orders = connection.execute(
        "SELECT username, product FROM orders"
    ).fetchall()
    selected = set(interests)
    popularity = Counter(product for _, product in orders)
    co_purchases = defaultdict(Counter)

    customer_purchases = defaultdict(set)
    for customer, product in orders:
        customer_purchases[customer].add(product)
    for purchases in customer_purchases.values():
        for source in purchases:
            co_purchases[source].update(purchases - {source})

    scores = Counter()
    reasons = {}
    for source in selected:
        for candidate, score in co_purchases[source].items():
            if candidate not in selected:
                scores[candidate] += score
                if candidate not in reasons or score > reasons[candidate][0]:
                    reasons[candidate] = (score, source)

    ranked = sorted(
        (product for product in products if product[1] not in selected),
        key=lambda product: (
            -scores[product[1]],
            -popularity[product[1]],
            product[0],
        ),
    )

    recommendations = []
    for product_id, name, price in ranked[: max(0, limit)]:
        if scores[name]:
            reason = f"Often bought alongside {reasons[name][1]}"
        elif popularity[name]:
            reason = "Popular with other shoppers"
        else:
            reason = "A great place to start"
        recommendations.append(
            {
                "id": product_id,
                "name": name,
                "price": price,
                "reason": reason,
            }
        )
    return recommendations
