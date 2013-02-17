# coding: utf-8
from __future__ import unicode_literals
import json
import urllib2

from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_GET, require_POST

from appdisk.utils import *

from django.conf import settings

# test compiled js?
USE_COMPILED_JS = True

def test(request):
    ctx = RequestContext(request)
    return render_to_response('appdisk/test.html', {},
                              context_instance=ctx)

def render_error_page(request, error_msg='出错了...'):
    return render_to_response('appdisk/error.html', {
        'error_msg': error_msg
    }, context_instance=RequestContext(request))

def render_ok_json():
    content_type = 'application/json; charset=utf-8'
    ret = {'success': True}
    return HttpResponse(json.dumps(ret), content_type=content_type)
    
def render_error_json(error_msg='出错了...'):
    content_type = 'application/json; charset=utf-8'
    ret = {'error': error_msg, 
           'success': False}
    return HttpResponse(json.dumps(ret), content_type=content_type)

@require_GET
def files(request):
    path = request.GET.get('p', '/')
    files = get_dir_entries(path)
    navlinks = gen_nav_links(path)
    return render_to_response('appdisk/files.html', {
        'path': path,
        'navlinks': navlinks,
        'files': files,
        'SAE': settings.SAE,
        'USE_COMPILED_JS': USE_COMPILED_JS,
    }, context_instance=RequestContext(request))

@require_POST
def upload(request):
    parent_dir = request.GET.get('p', '/')
    try:
        file_name, content = get_uploaded_file(request)
    except  Exception, e:
        return render_error_page(request, '上传文件失败: %s' % e)

    try:
        add_file(parent_dir, file_name, content)
    except Exception, e:
        return render_error_page(request, '上传文件失败: %s' % e)

    # TODO: add flash message
    url = reverse(files)
    url += '?p=' + urllib2.quote(parent_dir.encode('utf-8'))

    return HttpResponseRedirect(url)

@require_POST    
def newdir(request):
    parent_dir = request.POST.get('p', None)
    newdir_name = request.POST.get('name', None)

    if not parent_dir or not newdir_name or not is_valid_name(newdir_name):
        return render_error_json('错误的参数')

    try:
        add_dir(parent_dir, newdir_name)
    except  Exception, e:
        return render_error_json('创建新文件夹失败: %s' % e)

    return render_ok_json()
        
@require_POST    
def remove(request):
    path = request.POST.get('p', '')
    ftype = request.POST.get('t', '')
    if path == '' or path == '/' or ftype not in ['f', 'd']:
        return render_error_json('错误的参数')

    try:
        if ftype == 'f':
            remove_file(path)
        else:
            remove_dir(path)
    except Exception, e:
        return render_error_json('删除失败: %s' % e)

    return render_ok_json()

def redirect_to_path(path):
    url = reverse(files)
    url += '?p=' + urllib2.quote(path.encode('utf-8'))

    return HttpResponseRedirect(url)

def subdir(request):
    ret = {}
    content_type = 'application/json; charset=utf-8'
    try:
        path = request.GET['p']
    except KeyError:
        ret['error'] = "what's the path?"
        return HttpResponse(json.dumps(ret), content_type=content_type)

    if path == '':
        ret['error'] = "what's the path?"
        return HttpResponse(json.dumps(ret), content_type=content_type)

    files = get_dir_entries(path)
    ret['success'] = True
    ret['files'] = files
    return HttpResponse(json.dumps(ret), content_type=content_type)
