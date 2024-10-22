import factory
import swapper
from django.conf import settings
from factory.django import DjangoModelFactory

from tests.factories import OrderFactory


class PaymentFactory(DjangoModelFactory):
    order = factory.SubFactory(OrderFactory)
    amount_required = factory.SelfAttribute("order.total")
    currency = factory.SelfAttribute("order.currency")
    description = factory.SelfAttribute("order.name")
    backend = settings.GETPAID_PAYU_SLUG

    class Meta:
        model = swapper.load_model("getpaid", "Payment")
