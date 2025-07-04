# Generated by Django 5.2 on 2025-04-20 11:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("shangrila_backend", "0006_destination_itinerary"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="travelpackage",
            name="destination",
        ),
        migrations.AddField(
            model_name="travelpackage",
            name="destinations",
            field=models.ManyToManyField(
                related_name="packages", to="shangrila_backend.destination"
            ),
        ),
    ]
