# Generated by Django 3.0.5 on 2020-04-17 21:07

import uuid

import django_fsm
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("paywall", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(model_name="paymententry", name="payment",),
        migrations.AddField(
            model_name="paymententry",
            name="ext_id",
            field=models.CharField(db_index=True, default=uuid.uuid4, max_length=100),
        ),
        migrations.AddField(
            model_name="paymententry",
            name="fraud_status",
            field=django_fsm.FSMField(
                choices=[
                    ("unknown", "unknown"),
                    ("accepted", "accepted"),
                    ("rejected", "rejected"),
                    ("check", "needs manual verification"),
                ],
                default="unknown",
                max_length=50,
                protected=True,
            ),
        ),
        migrations.AddField(
            model_name="paymententry",
            name="payment_status",
            field=django_fsm.FSMField(
                choices=[
                    ("new", "new"),
                    ("prepared", "in progress"),
                    ("pre-auth", "pre-authed"),
                    ("charge_started", "charge process started"),
                    ("partially_paid", "partially paid"),
                    ("paid", "paid"),
                    ("failed", "failed"),
                    ("refund_started", "refund started"),
                    ("refunded", "refunded"),
                ],
                default="prepared",
                max_length=50,
                protected=True,
            ),
        ),
    ]