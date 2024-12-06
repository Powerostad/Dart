from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Collects Forex Data'

    def add_arguments(self, parser):
        parser.add_argument('stock', nargs='+', type=str)
        parser.add_argument("timeframe", nargs='+', type=int, default=5)

    def handle(self, *args, **options):
        timeframe = options["timeframe"]
        stock = options["stock"]

        print(stock, timeframe)