# Generated by Django 4.2 on 2025-01-31 18:46

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Signal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=20)),
                ('timeframe', models.CharField(max_length=10)),
                ('signal_type', models.CharField(choices=[('BUY', 'BUY'), ('SELL', 'SELL'), ('NEUTRAL', 'NEUTRAL')], max_length=10)),
                ('confidence', models.FloatField()),
                ('algorithms_triggered', models.JSONField(null=True)),
                ('entry_price', models.DecimalField(decimal_places=10, max_digits=20, null=True)),
                ('take_profit', models.DecimalField(decimal_places=10, max_digits=20, null=True)),
                ('stop_loss', models.DecimalField(decimal_places=10, max_digits=20, null=True)),
                ('status', models.CharField(choices=[('PENDING', 'PENDING'), ('ACTIVE', 'ACTIVE'), ('TRIGGERED', 'TRIGGERED'), ('EXPIRED', 'EXPIRED'), ('INVALIDATED', 'INVALIDATED')], default='PENDING', max_length=20)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('valid_until', models.DateTimeField(null=True)),
                ('risk_reward_ratio', models.FloatField(null=True)),
            ],
            options={
                'ordering': ('-generated_at',),
            },
        ),
        migrations.AddIndex(
            model_name='signal',
            index=models.Index(fields=['symbol', 'timeframe', 'status'], name='forex_signa_symbol_81c4f6_idx'),
        ),
        migrations.AddIndex(
            model_name='signal',
            index=models.Index(fields=['generated_at', 'valid_until'], name='forex_signa_generat_b23569_idx'),
        ),
    ]
