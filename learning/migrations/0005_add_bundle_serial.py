from django.db import migrations, models


def backfill_serial(apps, schema_editor):
    Lesson = apps.get_model('learning', 'Lesson')
    Segment = apps.get_model('learning', 'Segment')

    for segment in Segment.objects.all():
        bundles = Lesson.objects.filter(segment=segment).order_by('created_at', 'id')
        for index, bundle in enumerate(bundles, start=1):
            bundle.serial = index
            bundle.save(update_fields=['serial'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0004_backfill_segment'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='serial',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RunPython(backfill_serial, noop_reverse),
        migrations.AlterField(
            model_name='lesson',
            name='serial',
            field=models.PositiveIntegerField(),
        ),
        migrations.AddConstraint(
            model_name='lesson',
            constraint=models.UniqueConstraint(fields=('segment', 'serial'), name='unique_serial_within_segment'),
        ),
        migrations.AlterModelOptions(
            name='lesson',
            options={'ordering': ['segment__name', 'serial']},
        ),
    ]
