# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'SteamProfile', fields ['import_me']
        db.create_index('steamstalker_steamprofile', ['import_me'])


    def backwards(self, orm):
        # Removing index on 'SteamProfile', fields ['import_me']
        db.delete_index('steamstalker_steamprofile', ['import_me'])


    models = {
        'steamstalker.game': {
            'Meta': {'object_name': 'Game'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        },
        'steamstalker.profileseen': {
            'Meta': {'object_name': 'ProfileSeen'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'current_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128', 'blank': 'True'}),
            'game': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'friends_seen'", 'null': 'True', 'to': "orm['steamstalker.Game']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'seen': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'seen'", 'to': "orm['steamstalker.SteamProfile']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'online'", 'max_length': '10', 'db_index': 'True'})
        },
        'steamstalker.steamfriend': {
            'Meta': {'object_name': 'SteamFriend'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'from_friend': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_friends'", 'to': "orm['steamstalker.SteamProfile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'to_friend': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'from_friends'", 'to': "orm['steamstalker.SteamProfile']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        },
        'steamstalker.steamprofile': {
            'Meta': {'object_name': 'SteamProfile'},
            'avatar_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_me': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'last_import': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128', 'db_index': 'True'})
        }
    }

    complete_apps = ['steamstalker']