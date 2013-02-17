# coding: utf-8
from __future__ import unicode_literals

import os
import datetime
import hashlib
import logging
import traceback

import sae.storage

from django.db import IntegrityError
from django.template import defaultfilters as django_filters

#from django.conf import settings
from appdisk.models import Entry

class NoSuchEntry(Exception):
    def __init__(self, name):
        Exception.__init__(self)
        self.name = name
    def __str__(self):
        return '%s does not exist' % self.name

class AlreadyExistError(Exception):
    def __init__(self, name):
        Exception.__init__(self)
        self.name = name
    def __str__(self):
        return 'An entry with name "%s" already exists' % self.name

class StorageError(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg
    def __str__(self):
        return self.msg

def _sanitize_path(path, is_dir):
    '''Path should start with a backslash. Dir path MUST end with backslash,
    and file path MUST NOT end with backslash

    '''
    if not path.startswith('/'):
        path = '/' + path

    if is_dir:
        if not path.endswith('/'):
            path += '/'
    else:
        path = path.rstrip('/')

    return path

def sanitize_file_path(path):
    return _sanitize_path(path, False)

def sanitize_dir_path(path):
    return _sanitize_path(path, True)

def hash_dir_name(dir_name):
    return hashlib.sha1(dir_name.encode('UTF-8')).hexdigest()

def get_root_dir():
    dir_name = ''
    base_name = '/'
    try:
        return Entry.objects.get(dir_name_hash=hash_dir_name(dir_name),
                                base_name=base_name,
                                is_dir=True)
    except Entry.DoesNotExist:
        d = Entry(dir_name='',
                  base_name='/',
                  is_dir=True)
        d.save()
        return d

def get_dir(path):
    '''Return the entry of dir <dirpath>'''
    if path == '/':
        return get_root_dir()
    path = path.rstrip('/')
    dir_name = sanitize_dir_path(os.path.dirname(path))
    base_name = os.path.basename(path)
    return Entry.objects.get(dir_name_hash=hash_dir_name(dir_name),
                             base_name=base_name,
                             is_dir=True)

def get_file(dir_name, base_name):
    dir_name = sanitize_dir_path(dir_name)

    return Entry.objects.get(dir_name_hash=hash_dir_name(dir_name),
                             base_name=base_name,
                             is_dir=False)

def _get_dir_entries(dirpath):
    ''' '''
    dirpath = sanitize_dir_path(dirpath)
    try:
        get_dir(dirpath)
    except Entry.DoesNotExist:
        return NoSuchEntry(dirpath)

    entries = Entry.objects.filter(dir_name_hash=hash_dir_name(dirpath))

    return entries

def transform_entry(parent_dir, entry):
    ee = {}
    ee['name'] = entry.base_name
    ee['size'] = django_filters.filesizeformat(entry.size)
    ee['ctime'] = django_filters.date(entry.ctime, 'Y-m-d H:i:s')
    ee['url']   = entry.url
    if entry.is_dir:
        ee['fullpath'] = sanitize_dir_path(os.path.join(parent_dir, entry.base_name))
    else:
        ee['fullpath'] = sanitize_file_path(os.path.join(parent_dir, entry.base_name))
    ee['isDir'] = entry.is_dir

    return ee

def get_dir_entries(dirpath):
    '''Get the entry list of the directory'''
    entries = _get_dir_entries(dirpath)

    ret = []
    for entry in entries:
        ret.append(transform_entry(dirpath, entry))

    return ret

def get_storage_objname(parent_dir, filename):
    '''In SAE, every storage domain have to be created manually in admin
    console, so we choose a flat directory structure. With each filename
    prefixed with the hash value of its path.

    '''
    parent_dir = sanitize_dir_path(parent_dir)
    return hash_dir_name(parent_dir) + '-' + filename

def save_file_obj(parent_dir, filename, content):
    '''Save file object to storage, return its pubic url'''
    domain = 'appdisk'
    filename = get_storage_objname(parent_dir, filename)

    obj = sae.storage.Object(content, content_type='application/octet-stream')
    client = sae.storage.Client()
    return client.put(domain.encode('UTF-8'), filename.encode('UTF-8'), obj)

def add_file(parent_dir, filename, content):
    # First check if parent dir exist
    parent_dir = sanitize_dir_path(parent_dir)
    try:
        dir = get_dir(parent_dir)
    except Entry.DoesNotExist:
        raise NoSuchEntry(parent_dir)

    # save file in Stroage
    filepath = os.path.join(parent_dir, filename)
    try:
        url = save_file_obj(parent_dir, filename, content)
    except:
        tb = traceback.format_exc()
        logging.exception('Failed to save file %s', filepath)
        raise StorageError('Failed to save %s: %s' % (filepath, tb))

    newfile = Entry(dir_name=parent_dir, base_name=filename, size=len(content), is_dir=False, url=url)
    try:
        newfile.save()
    except IntegrityError:
        raise AlreadyExistError(filepath)

    dir.ctime = datetime.datetime.now()
    dir.save()

    return transform_entry(parent_dir, newfile)

def remove_file_obj(parent_dir, filename):
    '''Remove a file from Stroage'''
    domain = 'appdisk'
    filename = get_storage_objname(parent_dir, filename)
    client = sae.storage.Client()
    client.delete(domain.encode('UTF-8'), filename.encode('UTF-8'))

def remove_file(filepath):
    '''Remove a file from appdisk'''
    # First remove its from meta info
    dirpath = os.path.dirname(filepath)
    filename = os.path.basename(filepath)

    dirpath = sanitize_dir_path(dirpath)
    try:
        file = get_file(dirpath, filename)
    except Entry.DoesNotExist:
        return

    file.delete()

    remove_file_obj(dirpath, filename)

def get_file_url(path):
    parent_dir = sanitize_dir_path(os.path.dirname(path))
    filename = os.path.basename(path)

    try:
        f = get_file (parent_dir, filename)
    except Entry.DoesNotExist:
        raise NoSuchEntry(path)
    else:
        return f.url

def get_uploaded_file(request):
    try:
        file = request.FILES['file']
    except KeyError, e:
        print e
        raise Exception('请选择一个文件进行上传!')
    content = file.read()

    return file.name, content

def add_dir(parent_dir, dname):
    # Ensure the parent dir exist
    parent_dir = sanitize_dir_path(parent_dir)
    try:
        get_dir(parent_dir)
    except Entry.DoesNotExist:
        raise NoSuchEntry(parent_dir)

    newdir = Entry(dir_name=parent_dir,
                   base_name=dname,
                   is_dir=True)

    try:
        newdir.save()
    except IntegrityError:
        raise AlreadyExistError(os.path.join(parent_dir, dname))

    return transform_entry(parent_dir, newdir)

def remove_dir(dirpath):
    '''To remove a directory: First remove its descendents. Then remove
    itself.

    '''
    dirpath = sanitize_dir_path(dirpath)
    try:
        dir = get_dir(dirpath)
    except Entry.DoesNotExist:
        return

    entries = Entry.objects.filter(dir_name_hash=hash_dir_name(dirpath))

    for e in entries:
        subpath = os.path.join(dirpath, e.base_name)
        if e.is_dir:
            remove_dir(subpath)
        else:
            remove_file(subpath)

    dir.delete()

def gen_nav_links(path):
    # path is like '/a/b/c'
    # parts is like [ 'a', 'b', 'c']
    # we want [ ('a', '/a'), ('b', '/a/b'), ('c', '/a/b/c')]
    parts = [ p for p in path.split('/') if p.strip() != '' ]
    accu = []
    ret = []
    for part in parts:
        name = part
        accu.append(part)
        fullpath = os.path.join('/', *accu)
        ret.append((name, fullpath))

    return ret

def is_valid_name(name):
    return '/' not in name