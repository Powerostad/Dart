from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings

class Command(BaseCommand):
    help = 'Set Mariadb collation for handling Multi language'

    def handle(self, *args, **options):
        db_name = connection.settings_dict['NAME']
        charset = "utf8mb4"
        collation = "utf8mb4_unicode_ci"
        self.stdout.write(f'Setting Mariadb collation to {collation} and charset to {charset},'
                          f'for handling Multi language DB')

        with connection.cursor() as cursor:
            sql = f"""
            ALTER DATABASE {db_name}
            CHARACTER SET {charset}
            COLLATE {collation};
            """
            cursor.execute(sql)

        self.stdout.write(self.style.SUCCESS('Successfully set Mariadb collation and charset'))