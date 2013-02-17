# coding: utf8

from django.db import models
import datetime
import hashlib

class Entry(models.Model):
    '''An entry is either a file or a diretory'''

    dir_name = models.TextField()
    dir_name_hash = models.CharField(max_length=40, db_index=True)
    base_name = models.CharField(max_length=255)
    # file or dir
    is_dir = models.BooleanField()
    # download link, only set for regular files
    url = models.TextField(default='')
    size = models.IntegerField(default=0)

    # last modifed
    ctime = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        unique_together = ('dir_name_hash', 'base_name')

    def save(self, *args, **kwargs):
        self.dir_name_hash = hashlib.sha1(self.dir_name.encode('UTF-8')).hexdigest()
        super(Entry, self).save(*args, **kwargs)