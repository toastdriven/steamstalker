# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Game'
        db.create_table('steamstalker_game', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal('steamstalker', ['Game'])

        # Adding model 'SteamProfile'
        db.create_table('steamstalker_steamprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128, db_index=True)),
            ('avatar_url', self.gf('django.db.models.fields.URLField')(default='', max_length=200, blank=True)),
            ('import_me', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('last_import', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal('steamstalker', ['SteamProfile'])

        # Adding model 'SteamFriend'
        db.create_table('steamstalker_steamfriend', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('from_friend', self.gf('django.db.models.fields.related.ForeignKey')(related_name='from_friends', to=orm['steamstalker.SteamProfile'])),
            ('to_friend', self.gf('django.db.models.fields.related.ForeignKey')(related_name='to_friends', to=orm['steamstalker.SteamProfile'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal('steamstalker', ['SteamFriend'])

        # Adding model 'ProfileSeen'
        db.create_table('steamstalker_profileseen', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('seen', self.gf('django.db.models.fields.related.ForeignKey')(related_name='seen', to=orm['steamstalker.SteamProfile'])),
            ('current_name', self.gf('django.db.models.fields.CharField')(default='', max_length=128, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='online', max_length=10, db_index=True)),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='friends_seen', null=True, to=orm['steamstalker.Game'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal('steamstalker', ['ProfileSeen'])


    def backwards(self, orm):
        # Deleting model 'Game'
        db.delete_table('steamstalker_game')

        # Deleting model 'SteamProfile'
        db.delete_table('steamstalker_steamprofile')

        # Deleting model 'SteamFriend'
        db.delete_table('steamstalker_steamfriend')

        # Deleting model 'ProfileSeen'
        db.delete_table('steamstalker_profileseen')


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
            'from_friend': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'from_friends'", 'to': "orm['steamstalker.SteamProfile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'to_friend': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'to_friends'", 'to': "orm['steamstalker.SteamProfile']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        },
        'steamstalker.steamprofile': {
            'Meta': {'object_name': 'SteamProfile'},
            'avatar_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'import_me': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_import': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128', 'db_index': 'True'})
        }
    }

    complete_apps = ['steamstalker']