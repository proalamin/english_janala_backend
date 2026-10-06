from django.db import migrations, models


def reset_to_empty_json(apps, schema_editor):
    Vocabulary = apps.get_model('learning', 'Vocabulary')
    Vocabulary.objects.update(synonyms='[]', antonyms='[]')


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0005_add_bundle_serial'),
    ]

    operations = [
        migrations.RunPython(reset_to_empty_json, noop_reverse),
        migrations.AlterField(
            model_name='vocabulary',
            name='synonyms',
            field=models.JSONField(blank=True, default=list, help_text='List of {"word": ..., "meaning": ...} objects.'),
        ),
        migrations.AlterField(
            model_name='vocabulary',
            name='antonyms',
            field=models.JSONField(blank=True, default=list, help_text='List of {"word": ..., "meaning": ...} objects.'),
        ),
    ]
