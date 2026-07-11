from django.db import migrations


def create_missing_contact_tables(apps, schema_editor):
    existing_tables = set(schema_editor.connection.introspection.table_names())

    for model_name in ("Contact", "ContactRequest", "UserBlock"):
        model = apps.get_model("chat", model_name)
        if model._meta.db_table not in existing_tables:
            schema_editor.create_model(model)
            existing_tables.add(model._meta.db_table)


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0002_conversation_conversationparticipant_and_more"),
    ]

    operations = [
        migrations.RunPython(create_missing_contact_tables, migrations.RunPython.noop),
    ]
