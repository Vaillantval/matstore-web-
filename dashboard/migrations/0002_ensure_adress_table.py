from django.db import migrations


def ensure_adress_table(apps, schema_editor):
    """
    Gère 3 cas :
      1. dashboard_adress existe déjà → rien à faire
      2. dashboard_adresses existe (ancien nom) → renommer
      3. Aucune des deux → créer la table from scratch
    """
    conn   = schema_editor.connection
    tables = conn.introspection.table_names()

    if 'dashboard_adress' in tables:
        return  # déjà correct

    if 'dashboard_adresses' in tables:
        schema_editor.execute(
            'ALTER TABLE "dashboard_adresses" RENAME TO "dashboard_adress"'
        )
        return

    # Table absente : la créer directement
    schema_editor.execute("""
        CREATE TABLE "dashboard_adress" (
            "id"           integer NOT NULL PRIMARY KEY AUTOINCREMENT,
            "name"         varchar(100) NOT NULL,
            "full_name"    varchar(100) NOT NULL,
            "street"       varchar(255) NOT NULL,
            "code_postal"  varchar(10)  NOT NULL,
            "city"         varchar(255) NOT NULL,
            "country"      varchar(255) NOT NULL,
            "more_details" text NULL,
            "adress_type"  varchar(255) NOT NULL,
            "created_at"   datetime NOT NULL,
            "updated_at"   datetime NOT NULL,
            "author_id"    integer NULL
                REFERENCES "accounts_customer" ("id")
                DEFERRABLE INITIALLY DEFERRED
        )
    """)


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(ensure_adress_table, migrations.RunPython.noop),
    ]
