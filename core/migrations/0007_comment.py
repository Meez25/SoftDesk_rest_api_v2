# Generated by Django 4.1.5 on 2023-01-16 19:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_issue"),
    ]

    operations = [
        migrations.CreateModel(
            name="Comment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("description", models.TextField()),
                ("created_time", models.DateTimeField(auto_now_add=True)),
                (
                    "author_user_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "issue_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.issue"
                    ),
                ),
            ],
        ),
    ]
