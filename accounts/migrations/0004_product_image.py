# Generated by Django 5.2 on 2025-04-11 19:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_user_user_type_product"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="product_images/"),
        ),
    ]
