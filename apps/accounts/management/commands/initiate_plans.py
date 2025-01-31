from django.core.management.base import BaseCommand
from django.db import IntegrityError
from apps.accounts.models import SubscriptionPlan
import json
from decimal import Decimal

class Command(BaseCommand):
    help = 'Initiate subscription plans.'

    def handle(self, *args, **options):
        with open('subscription_plans.json', 'r') as f:
            subscription_plans = json.load(f)

        for plan in subscription_plans:
            plan["price"] = Decimal(plan["price"])
            existing_plan = SubscriptionPlan.objects.filter(
                name=plan['name'],
                price=plan['price'],
                billing_interval=plan['billing_interval']
            ).first()

            if not existing_plan:
                try:
                    SubscriptionPlan.objects.create(**plan)
                except IntegrityError:
                    self.stdout.write(self.style.ERROR(f"Failed to create plan: {plan['name']}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Plan already exists: {plan['name']}"))

        self.stdout.write(self.style.SUCCESS('Successfully initiated subscription plans.'))
