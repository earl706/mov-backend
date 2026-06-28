from django.db import migrations, models


def backfill_seconds(apps, schema_editor):
    FocusSession = apps.get_model("focus", "FocusSession")
    for session in FocusSession.objects.all():
        if not session.actual_seconds and session.actual_minutes:
            session.actual_seconds = session.actual_minutes * 60
        if not session.planned_seconds and session.planned_minutes:
            session.planned_seconds = session.planned_minutes * 60
        session.save(update_fields=["actual_seconds", "planned_seconds"])


class Migration(migrations.Migration):

    dependencies = [
        ("focus", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="focussession",
            name="actual_seconds",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="focussession",
            name="planned_seconds",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(backfill_seconds, migrations.RunPython.noop),
    ]
