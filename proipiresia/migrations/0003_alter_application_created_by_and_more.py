# Generated by Django 5.2.3 on 2025-06-12 19:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("proipiresia", "0002_alter_auditlog_user"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="application",
            name="created_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_applications",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Δημιουργήθηκε από",
            ),
        ),
        migrations.AlterField(
            model_name="application",
            name="updated_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="updated_applications",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Ενημερώθηκε από",
            ),
        ),
        migrations.AlterField(
            model_name="priorservice",
            name="created_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_services",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Δημιουργήθηκε από",
            ),
        ),
        migrations.AlterField(
            model_name="priorservice",
            name="updated_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="updated_services",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Ενημερώθηκε από",
            ),
        ),
        migrations.AlterField(
            model_name="priorservice",
            name="verified_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="verified_services",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Ελέγχθηκε από",
            ),
        ),
    ]
