from django.db import models, connections
from django.db.utils import ProgrammingError
import json
import requests
import importlib
import os
import psycopg2
import sqlite3
from dorkbot.dorkbot import TargetDatabase
from contextlib import closing
import jobs.models
from django.db.models.signals import post_save
from django.conf import settings

class Organization(models.Model):
    name = models.CharField(max_length=48, unique=True)
    enabled = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

    def _get_target_count(self):
        db_prefix = settings.DORKBOT_DATABASE_PREFIX
        db_name = db_prefix + self.name

        if not self.name:
            count = '-'

        elif 'postgres' in settings.DATABASES:
            db = settings.DATABASES['postgres']
            db_user = db['USER']
            db_credentials = ':'.join([db_user, db['PASSWORD']])
            db_server = ':'.join([db['HOST'], db['PORT']])
            db_connection_string = 'postgresql://' + db_credentials + '@' + db_server + '/' + db_name

            conn = psycopg2.connect(db_connection_string)
            with conn, closing(conn.cursor()) as c:
                c.execute('SELECT COUNT(*) FROM targets')
                count = int(c.fetchone()[0])

        else:
            dorkbot_directory = os.path.abspath(settings.DORKBOT_DIRECTORY)
            db_filename = os.path.join(dorkbot_directory, db_name + '.sqlite3')
            conn = sqlite3.connect(db_filename)
            with conn, closing(conn.cursor()) as c:
                c.execute('SELECT COUNT(*) FROM targets')
                count = c.fetchone()[0]

        return count
    total_targets = property(_get_target_count)

    def _get_scanned_count(self):
        db_prefix = settings.DORKBOT_DATABASE_PREFIX
        db_name = db_prefix + self.name

        if not self.name:
            count = '-'

        elif 'postgres' in settings.DATABASES:
            db = settings.DATABASES['postgres']
            db_user = db['USER']
            db_credentials = ':'.join([db_user, db['PASSWORD']])
            db_server = ':'.join([db['HOST'], db['PORT']])
            db_connection_string = 'postgresql://' + db_credentials + '@' + db_server + '/' + db_name

            conn = psycopg2.connect(db_connection_string)
            with conn, closing(conn.cursor()) as c:
                c.execute('SELECT COUNT(*) FROM targets WHERE scanned = 1')
                count = int(c.fetchone()[0])

        else:
            dorkbot_directory = os.path.abspath(settings.DORKBOT_DIRECTORY)
            db_filename = os.path.join(dorkbot_directory, db_name + '.sqlite3')
            conn = sqlite3.connect(db_filename)
            with conn, closing(conn.cursor()) as c:
                c.execute('SELECT COUNT(*) FROM targets WHERE scanned = 1')
                count = c.fetchone()[0]

        return count
    scanned_targets = property(_get_scanned_count)

    def _get_unscanned_count(self):
        db_prefix = settings.DORKBOT_DATABASE_PREFIX
        db_name = db_prefix + self.name

        if not self.name:
            count = '-'

        elif 'postgres' in settings.DATABASES:
            db = settings.DATABASES['postgres']
            db_user = db['USER']
            db_credentials = ':'.join([db_user, db['PASSWORD']])
            db_server = ':'.join([db['HOST'], db['PORT']])
            db_connection_string = 'postgresql://' + db_credentials + '@' + db_server + '/' + db_name

            conn = psycopg2.connect(db_connection_string)
            with conn, closing(conn.cursor()) as c:
                c.execute('SELECT COUNT(*) FROM targets WHERE scanned != 1')
                count = int(c.fetchone()[0])

        else:
            dorkbot_directory = os.path.abspath(settings.DORKBOT_DIRECTORY)
            db_filename = os.path.join(dorkbot_directory, db_name + '.sqlite3')
            conn = sqlite3.connect(db_filename)
            with conn, closing(conn.cursor()) as c:
                c.execute('SELECT COUNT(*) FROM targets WHERE scanned != 1')
                count = c.fetchone()[0]

        return count
    unscanned_targets = property(_get_unscanned_count)

    def _get_fingerprint_count(self):
        db_prefix = settings.DORKBOT_DATABASE_PREFIX
        db_name = db_prefix + self.name

        if not self.name:
            count = '-'

        elif 'postgres' in settings.DATABASES:
            db = settings.DATABASES['postgres']
            db_user = db['USER']
            db_credentials = ':'.join([db_user, db['PASSWORD']])
            db_server = ':'.join([db['HOST'], db['PORT']])
            db_connection_string = 'postgresql://' + db_credentials + '@' + db_server + '/' + db_name

            conn = psycopg2.connect(db_connection_string)
            with conn, closing(conn.cursor()) as c:
                c.execute('SELECT COUNT(*) FROM fingerprints')
                count = int(c.fetchone()[0])

        else:
            dorkbot_directory = os.path.abspath(settings.DORKBOT_DIRECTORY)
            db_filename = os.path.join(dorkbot_directory, db_name + '.sqlite3')
            conn = sqlite3.connect(db_filename)
            with conn, closing(conn.cursor()) as c:
                c.execute('SELECT COUNT(*) FROM fingerprints')
                count = c.fetchone()[0]

        return count
    fingerprint_count = property(_get_fingerprint_count)

    def save(self):
        db_prefix = settings.DORKBOT_DATABASE_PREFIX
        db_name = db_prefix + self.name

        if 'postgres' in settings.DATABASES:
            db = settings.DATABASES['postgres']
            db_user = db['USER']
            db_credentials = ':'.join([db_user, db['PASSWORD']])
            db_server = ':'.join([db['HOST'], db['PORT']])
            db_connection_string = 'postgresql://' + db_credentials + '@' + db_server + '/' + db_name

            try:
                with connections['postgres'].cursor() as c:
                    c.execute('CREATE DATABASE "' + db_name + '" OWNER "' + db_user + '"')
                TargetDatabase(db_connection_string)
            except ProgrammingError as e:
                if "already exists" in str(e):
                    pass
                else:
                    raise
        else:
            dorkbot_directory = os.path.abspath(settings.DORKBOT_DIRECTORY)
            db_filename = os.path.join(dorkbot_directory, db_name + '.sqlite3')
            TargetDatabase(db_filename)

        return super().save()

    def delete(self):
        db_prefix = settings.DORKBOT_DATABASE_PREFIX
        db_name = db_prefix + self.name

        if 'postgres' in settings.DATABASES:
            with connections['postgres'].cursor() as c:
                c.execute('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid() AND datname = \'' + db_name + '\'')
                c.execute('DROP DATABASE "' + db_name + '"')
        else:
            dorkbot_directory = os.path.abspath(settings.DORKBOT_DIRECTORY)
            db_filename = os.path.join(dorkbot_directory, db_name + '.sqlite3')
            try:
                os.remove(db_filename)
            except FileNotFoundError as e:
                pass

        return super().delete()


class Domain(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name

    def delete(self):
        db_prefix = settings.DORKBOT_DATABASE_PREFIX
        db_name = db_prefix + self.organization.name
        domain = self.name

        if 'postgres' in settings.DATABASES:
            db = settings.DATABASES['postgres']
            db_credentials = ':'.join([db['USER'], db['PASSWORD']])
            db_server = ':'.join([db['HOST'], db['PORT']])
            db_connection_string = 'postgresql://' + db_credentials + '@' + db_server + '/' + db_name

            db = psycopg2.connect(db_connection_string)
            with db, closing(db.cursor()) as c:
                c.execute('DELETE FROM targets WHERE url LIKE \'%://%' + domain + '%\'')

        else:
            dorkbot_directory = os.path.abspath(settings.DORKBOT_DIRECTORY)
            db_filename = os.path.join(dorkbot_directory, db_name + '.sqlite3')
            db = sqlite3.connect(db_filename)
            with db, closing(db.cursor()) as c:
                c.execute('DELETE FROM targets WHERE url LIKE \'%://%' + domain + '%\'')

        return super().delete()


def create_job(sender, instance, **kwargs):
    if instance.organization.enabled:
        job = jobs.models.Job(task='index', organization=instance.organization, domain=instance)
        job.save()

post_save.connect(create_job, sender=Domain)

