from django.core.management.base import BaseCommand
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
            SubscriptionPlan.objects.get_or_create(**plan)

        self.stdout.write(self.style.SUCCESS('Successfully initiated subscription plans.'))
