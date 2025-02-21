import swapper
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import permissions, views, viewsets
from rest_framework.response import Response

from getpaid.rest_framework.serializers import PaymentDetailSerializer
from getpaid.status import PaymentStatus as ps

Payment = swapper.load_model("getpaid", "Payment")
Order = swapper.load_model("getpaid", "Order")


class PaymentDetailViewSet(viewsets.GenericViewSet):
    # Pop `redirect_uri` from response to let frontend know
    # if it should redirect user or not.
    POP_REDIRECT_URI_WHEN_PENDING = True

    serializer_class = PaymentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Payment.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(order__user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        payment = self.get_object()
        if not payment.redirect_uri and payment.status == ps.NEW:
            payment.prepare_transaction(request=request, view=self)
        response_data = self.get_serializer(payment).data
        if self.POP_REDIRECT_URI_WHEN_PENDING is True and (
            payment.status not in (ps.NEW, ps.PREPARED)
        ):
            response_data.pop("redirect_uri")

        return Response(response_data)


class CallbackDetailView(views.APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request, pk, *args, **kwargs):
        try:
            payment = (
                Payment.objects.select_related("order")
                .select_for_update(of=("self", "order"))
                .get(pk=pk)
            )
        except Payment.DoesNotExist:
            raise Http404("No %s matches the given query." % Payment._meta.object_name)
        return payment.handle_paywall_callback(request, *args, **kwargs)
