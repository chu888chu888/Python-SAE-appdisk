## **Appdisk** 是什么?

- Appdisk 是基于[新浪 AppEngine](http://sinaapp.com) (SAE) 的 Storage 服务开发的 Django app
- 简单的说，如果你的 SAE 程序是用 [Django](http://djangoproject.com) 写的，那么你只需要把 Appdisk 加入到
  **INSTALLED_APPS**，就能给你的程序添加一个在线存储文件的功能
  
## Demo

[点此查看 Demo](http://appdisk.sinaapp.com/demo/)

## 提供的功能

- 上传、下载文件
- 创建、删除文件夹

## 配置

* 将 **appdisk** 源代码放到 project 路径下
* 在 `settings.py` 的 `INSTALLED_APPS` 里加入 **appdisk**

```python
INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'appdisk',
)
```

* 修改你项目中的 urls.py，添加以下几行：

```python
from appdisk import urls as appdisk_urls

urlpatterns = patterns('',
    # 你的其他 url 规则
    # .....
    (r'^appdisk/', include(appdisk_urls)),
)
```

* 在 `config.yaml` 里添加 appdisk 的静态文件规则

```yaml
handlers:
- url: /static/appdisk
  static_dir: appdisk/static/appdisk
```

* 在 SAE 的 MYSQL 管理面板中创建 appdisk 所需要的 table

先导出SQL语句：
```sh
python manage.py sqlall appdisk
```

再登录 SAE 的 MYSQL 管理面板， 运行上面导出的 SQL 语句

* 为 appdisk 创建一个 storage domain

注意这个 storage domain 的名字要设置为 "appdisk"

* 访问你的项目的 `/appdisk` 路径，查看 appdisk 是否正常工作
