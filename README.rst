.. image:: https://img.shields.io/pypi/v/django-getpaid.svg
    :target: https://pypi.org/project/django-getpaid/
    :alt: Latest PyPI version
.. image:: https://img.shields.io/travis/sunscrapers/django-getpaid.svg
    :target: https://travis-ci.org/sunscrapers/django-getpaid
.. image:: https://api.codacy.com/project/badge/Coverage/d25ba81e2e4740d6aac356f4ac90b16d
    :target: https://www.codacy.com/manual/dekoza/django-getpaid
.. image:: https://img.shields.io/pypi/wheel/django-getpaid.svg
    :target: https://pypi.org/project/django-getpaid/
.. image:: https://img.shields.io/pypi/l/django-getpaid.svg
    :target: https://pypi.org/project/django-getpaid/
.. image:: https://api.codacy.com/project/badge/Grade/d25ba81e2e4740d6aac356f4ac90b16d
    :target: https://www.codacy.com/manual/dekoza/django-getpaid

=============================
Welcome to django-getpaid
=============================


django-getpaid is payment processing framework for Django

Documentation
=============

The full documentation is at https://django-getpaid.readthedocs.io.

Features
========

* support for multiple payment brokers at the same time
* very flexible architecture
* support for asynchronous status updates - both push and pull
* support for modern REST-based broker APIs
* support for multiple currencies (but one per payment)
* support for global and per-plugin validators
* easy customization with provided base abstract models and swappable mechanic (same as with Django's User model)


Quickstart
==========

Install django-getpaid and at least one payment backend:

.. code-block:: console

    pip install django-getpaid

Add them to your ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        'getpaid',
        'getpaid.backends.payu',  # one of plugins
        ...
    ]

Add getpaid to URL patterns:

.. code-block:: python

    urlpatterns = [
        ...
        path('payments/', include('getpaid.urls')),
        ...
    ]

Define an ``Order`` model by subclassing ``getpaid.models.AbstractOrder``
and define some required methods:

.. code-block:: python

    # orders/order_status.py
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    FAILED = "failed"

    ORDER_STATUSES = (
        (PENDING, _("PENDING")),
        (PROCESSING, _("PROCESSING")),
        (COMPLETED, _("COMPLETED")),
        (ON_HOLD, _("ON HOLD")),
        (CANCELLED, _("CANCELLED")),
        (REFUNDED, _("REFUNDED")),
        (FAILED, _("FAILED")),
    )

    # orders/models.py
    from getpaid.models import AbstractOrder
    from orders import order_status

    class MyCustomOrder(AbstractOrder):
        amount = models.DecimalField(decimal_places=2, max_digits=8)
        description = models.CharField(max_length=128)
        buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
        status = FSMField(
            choices=order_status.ORDER_STATUSES,
            default=order_status.PENDING,
            db_index=True,
            protected=True,
            editable=False,
        )
        is_paid = models.BooleanField(
            default=False,
            editable=False
        )
        paid_date = models.DateTimeField(
                blank=True,
                null=True,
                editable=False
            )
        def get_absolute_url(self):
            return urljoin(settings.FRONTEND_URL, f"order/{self.pk}")

        def get_total_amount(self):
            return self.amount

        def get_buyer_info(self):
            return {"email": self.buyer.email}

        def get_currency(self):
            return "EUR"

        def get_description(self):
            return self.description

        @transaction.atomic
        @transition(
            field=status,
            source=[order_status.PENDING],
            target=order_status.PROCESSING,
        )
        def set_as_paid(self):
            self.is_paid = True
            self.paid_date = timezone.now()

        @transaction.atomic
        @transition(
            field=status,
            source=[
                order_status.PENDING,
                order_status.PROCESSING,
                order_status.ON_HOLD,
                order_status.FAILED,
            ],
            target=order_status.CANCELLED,
        )
        def set_as_cancelled(self):
            pass

        @transaction.atomic
        @transition(
            field=status, source=order_status.PROCESSING, target=order_status.COMPLETED
        )
        def set_as_completed(self):
            pass

.. note:: If you already have an Order model and don't want to subclass ``AbstractOrder``
    just make sure you implement all methods.

Define a ``Payment`` model by subclassing ``getpaid.models.AbstractPayment``
and define some required methods:

.. code-block:: python

    # payments/models.py
    from getpaid.models import AbstractPayment

    class MyCustomPayment(AbstractPayment):

        def __str__(self):
            return f"Payment #{self.id}"

        def on_mark_as_paid(self, **kwargs):
            self.order.set_as_paid()
            self.order.save()

.. note:: If you already have an Order model and don't want to subclass ``AbstractOrder``
    just make sure you implement all methods.

Inform getpaid of your Order & Payment model in ``settings.py`` and provide settings for payment backends:

.. code-block:: python

    FRONTEND_URL = "https://mydomain.tld"
    assert not FRONTEND_URL.endswith("/")
    BACKEND_URL = "https://backend.mydomain.tld"

    GETPAID_ORDER_MODEL = 'yourapp.MyCustomOrder'
    GETPAID_PAYMENT_MODEL = "yourapp.MyCustomPayment"
    GETPAID_PAYU_SLUG = "getpaid.backends.payu"
    GETPAID_BACKEND_HOST = BACKEND_URL
    GETPAID_FRONTEND_HOST = FRONTEND_URL

    PAYMENT_CONTINUE_URL = "{frontend_host}/payment/{payment_id}/end/"
    PAYMENT_RETRY_URL = "{frontend_host}/payment/{order_id}/retry/"

    GETPAID_BACKEND_SETTINGS = {
        GETPAID_PAYU_SLUG: {
            # take these from your merchant panel:
            "pos_id": 12345,
            "second_key": "91ae651578c5b5aa93f2d38a9be8ce11",
            "oauth_id": 12345,
            "oauth_secret": "12f071174cb7eb79d4aac5bc2f07563f",
            "continue_url": PAYMENT_CONTINUE_URL,
            "retry_url": PAYMENT_RETRY_URL,
        },
    }


Write a view that will create the Payment.

An example view and its hookup to urls.py can look like this:

.. code-block:: python

    # orders/views.py
    from rest_framework import mixins, permissions, viewsets
    from getpaid.rest_framework.payment_creator import PaymentCreator

    class OrderViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
        serializer_class = OrderSerializer
        queryset = Order.objects.all()
        permission_classes = (permissions.IsAuthenticated,)

        @transaction.atomic()
        def perform_create(self, serializer):
            super().perform_create(serializer)
            self.create_payment(serializer.instance)

        def create_payment(self, order):
            payment_data = self.request.data.get("payment", {})
            return PaymentCreator(order, payment_data).create()

    # orders/urls.py
    router = DefaultRouter()
    router.register("", OrderViewSet)

    urlpatterns = router.urls

You can optionally override callback handler. Example for PayU backend:

.. code-block:: python

    from getpaid.backends.payu.processor import PaymentProcessor as GetpaidPayuProcessor

    class PayuCallbackHandler:
        def __init__(self, payment):
            self.payment = payment

        def handle(self, data):
            pass

    class PayuPaymentProcessor(GetpaidPayuProcessor):
        callback_handler_class = PayuCallbackHandler

=============================
PAYU
=============================
TODO: improve docs

Running Tests
=============

.. code-block:: console

    poetry install
    poetry run tox


Alternatives
============

* `django-payments <https://github.com/mirumee/django-payments>`_


Credits
=======

Created by `Krzysztof Dorosz <https://github.com/cypreess>`_.
Redesigned and rewritten by `Dominik Kozaczko <https://github.com/dekoza>`_.

Proudly sponsored by `SUNSCRAPERS <http://sunscrapers.com/>`_

Redesigned to be compatible with rest-framework by `Panowie Programiści <https://p-programisci.pl>`__

Disclaimer
==========

This project has nothing in common with `getpaid <http://code.google.com/p/getpaid/>`_ plone project.
