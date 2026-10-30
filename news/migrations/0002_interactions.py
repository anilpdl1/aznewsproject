from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("news", "0001_initial")]

    operations = [
        migrations.RenameField(model_name="comment", old_name="message", new_name="content"),
        migrations.AddField(
            model_name="contactmessage", name="subject",
            field=models.CharField(default="", max_length=200), preserve_default=False,
        ),
        migrations.CreateModel(
            name="Subscriber",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("subscribed_at", models.DateTimeField(auto_now_add=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["-subscribed_at"]},
        ),
    ]
