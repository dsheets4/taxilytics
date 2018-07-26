# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2016-08-31 10:03
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django_util.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('query', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TopicModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='TopicModelConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('algorithm', models.CharField(choices=[('MalletLda', 'LDA MALLET'), ('GensimLda', 'LDA Gensim'), ('GensimLsi', 'LSI')], max_length=16)),
                ('num_topics', models.IntegerField(default=300)),
                ('arguments', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default={}, help_text='Additional arguments to pass to the topic model.', null=True, validators=[django_util.validators.JsonValidator()])),
            ],
        ),
        migrations.AddField(
            model_name='topicmodel',
            name='config',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='topic.TopicModelConfig'),
        ),
        migrations.AddField(
            model_name='topicmodel',
            name='data',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='query.TripQuery'),
        ),
    ]