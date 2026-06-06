---
name: django-patterns
description: Django architecture patterns including DRF, ORM optimization, signals, middleware, and project structure
---

# Django Patterns

## Project Structure

Organize Django projects with a clear separation between apps, shared utilities, and configuration.

```
project/
  config/
    settings/
      base.py
      local.py
      production.py
    urls.py
    wsgi.py
  apps/
    users/
      models.py
      serializers.py
      views.py
      services.py
      selectors.py
      urls.py
      tests/
    orders/
      ...
  common/
    models.py
    permissions.py
    pagination.py
```

Keep business logic in `services.py` (write operations) and `selectors.py` (read operations). Views should remain thin.

## ORM Optimization

```python
# select_related for ForeignKey / OneToOne (SQL JOIN)
orders = Order.objects.select_related("customer", "customer__profile").all()

# prefetch_related for ManyToMany / reverse FK (separate query)
authors = Author.objects.prefetch_related(
    Prefetch("books", queryset=Book.objects.filter(published=True))
).all()

# Defer fields you don't need
posts = Post.objects.defer("body", "metadata").filter(status="published")

# Use .only() when you need just a few columns
emails = User.objects.only("id", "email").filter(is_active=True)

# Bulk operations
Product.objects.bulk_create(products, batch_size=1000)
Product.objects.bulk_update(products, ["price", "stock"], batch_size=1000)
```

Always check queries with `django-debug-toolbar` or `connection.queries` in tests.

## Django REST Framework Serializers

```python
class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ["id", "customer_name", "items", "total", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_total(self, obj):
        return sum(item.price * item.quantity for item in obj.items.all())

    def validate(self, data):
        if data.get("start_date") and data.get("end_date"):
            if data["start_date"] >= data["end_date"]:
                raise serializers.ValidationError("end_date must be after start_date")
        return data
```

## Signals

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Order)
def order_created_handler(sender, instance, created, **kwargs):
    if created:
        send_order_confirmation.delay(instance.id)
        update_inventory.delay(instance.id)
```

Prefer signals for cross-app side effects. For same-app logic, call services directly.

## Custom Middleware

```python
import time
import logging

logger = logging.getLogger(__name__)

class RequestTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration = time.monotonic() - start
        logger.info(f"{request.method} {request.path} {response.status_code} {duration:.3f}s")
        return response
```

## Anti-Patterns

- Putting business logic in views or serializers instead of service layers
- Using `Model.objects.all()` without pagination in list endpoints
- N+1 queries from missing `select_related` / `prefetch_related`
- Overusing signals for same-app logic (makes flow hard to trace)
- Storing secrets in `settings.py` instead of environment variables
- Running raw SQL without parameterized queries

## Checklist

- [ ] Business logic lives in services/selectors, not views
- [ ] All list queries use `select_related` or `prefetch_related` where needed
- [ ] Serializers validate input data with custom `validate` methods
- [ ] Settings split into base/local/production modules
- [ ] Migrations are reviewed before merging
- [ ] Bulk operations used for batch inserts/updates
- [ ] Custom middleware follows the WSGI callable pattern
- [ ] Tests cover model constraints, serializer validation, and view permissions
