# -*- coding: utf-8 -*-
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: eXtentable Download Manager.
#
# XDM: eXtentable Download Manager. Plugin based media collection manager.
# Copyright (C) 2013  Dennis Lutter
#
# XDM is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# XDM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
import os
import types
import json
from functools import wraps

from datetime import date, datetime
import pytz
import requests
import xdm
import helper
from xdm import common
from xdm.logger import *
import mongoengine
from mongoengine.context_managers import switch_collection, no_dereference
from mongoengine import *

from bson.dbref import DBRef


# workaround for spinxy not installing _ and ngettext
try:
    _()
except NameError:
    _ = lambda x: x
except TypeError:
    pass

try:
    ngettext()
except NameError:
    ngettext = lambda x: x
except TypeError:
    pass


mongoengine.connection._connection_settings["default"] = {
    "name": "data",
    "username": False,
    "password": False
}
mongoengine.connection._connections["default"] = xdm.MONGO_CONNECTION



# from jinja2 import FileSystemBytecodeCache
from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader, DictLoader, FunctionLoader, BaseLoader, TemplateNotFound
import urllib

# bcc = FileSystemBytecodeCache(pattern='%s.cache')
# , bytecode_cache=bcc

WIDGET_PATH = os.path.join('html', 'templates', 'widget')
elementWidgetEnvironment = Environment(
    loader=FileSystemLoader(WIDGET_PATH), extensions=['jinja2.ext.i18n'])
elementWidgetEnvironment.install_gettext_callables(_, ngettext, newstyle=True)
elementWidgetEnvironment.filters['relativeTime'] = helper.reltime
elementWidgetEnvironment.filters['idSafe'] = helper.idSafe
elementWidgetEnvironment.filters['derefMe'] = helper.dereferMe
elementWidgetEnvironment.filters['derefMeText'] = helper.dereferMeText
elementWidgetEnvironment.filters['from_json'] = json.loads

WIDGETS = []
for root, folders, files in os.walk(WIDGET_PATH):
    for curFile in files:
        WIDGETS.append(os.path.basename(curFile.split('.')[0]))

def fake_load(template):
    return (template, None, lambda: True)

class MyLoader(BaseLoader):

    def get_source(self, environment, template):
        return (template, None, lambda: True)

elementEnviroment = Environment(
    loader=FunctionLoader(fake_load), extensions=['jinja2.ext.i18n'])
elementEnviroment.install_gettext_callables(_, ngettext, newstyle=True)
elementEnviroment.filters['relativeTime'] = helper.reltime
elementEnviroment.filters['idSafe'] = helper.idSafe
elementEnviroment.filters['derefMe'] = helper.dereferMe
elementEnviroment.filters['derefMeText'] = helper.dereferMeText
elementEnviroment.filters['json_loads'] = json.loads
elementEnviroment.filters['items'] = helper.items




class Status(Document):
    name = StringField(required=True)
    hidden = BooleanField(default=False)

    @property
    def screenName(self):
        return _(self.name)


class MediaType(Document):
    name = StringField()
    identifier = StringField(unique=True)

    def __str__(self):
        return str(self.identifier)


class Field(EmbeddedDocument):
    name = StringField(required=True)
    provider = StringField(required=True)
    value = DynamicField()

    def __cmp__(self, other):
        if self.provider == other.provider:
            return 0
        provider_tags = common.getProviderTags()
        if self.provider not in provider_tags:
            return 1
        if other.provider not in provider_tags:
            return -1

        if provider_tags.index(self.provider) < provider_tags.index(other.provider):
            return -1
        return 1

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value and self.provider and other.provider

    def __hash__(self):
        return hash("{s.name}:{s.value}:{s.provider}".format(s=self))

    def __repr__(self):
        return "<{}>".format(self)

    def __str__(self):
        return "Field {s.name}:{s.value} - {s.provider}".format(
            s=self
        )

class Location(EmbeddedDocument):
    download = ReferenceField("Download")
    path = StringField()


class Config(EmbeddedDocument):
    name = StringField(required=True)
    value = DynamicField()
    hidden = BooleanField(default=False)

    def cur_type(self):
        return type(self.value).__name__


class Image(EmbeddedDocument):
    name = StringField(required=True)
    url = URLField(required=True)
    provider = StringField(required=True)
    type = StringField()

    header_map = {
        "image/jpeg": "jpeg",
        "image/png": "png",
        "image/gif": "gif",
        "image/bmp": "bmp"
    }

    def __str__(self):
        return self.get_src()

    def delete_file(self):
        try:
            os.remove(self.get_path())
        except OSError:
            pass

    def download(self):
        if not self.url:
            return
        log("Downloading image: %s %s" % (self.name, self.url))
        try:
            r = requests.get(self.url)
        except requests.RequestException:
            log.error("Downloading image %s failed" % self.url)
            self.type = "jpeg"
            return

        self.type = {
            "image/jpeg": "jpeg",
            "image/png": "png",
            "image/gif": "gif",
            "image/bmp": "bmp"
        }.get(r.headers['content-type'], "jpeg")
        dst_path = self.get_path()
        log("Saving image to %s" % dst_path)
        if r.status_code == 200:
            with open(dst_path, 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)

    def get_path(self):
        directory = os.path.join(
            xdm.IMAGEPATH, unicode(self._instance.media_type))
        if not os.path.exists(directory):
            os.makedirs(directory)

        return os.path.join(directory, self.img_name())

    @property
    def saved(self):
        return os.path.isfile(self.get_path())

    def get_src(self):
        if self.saved: # type is only set after we down loaded the image
            url = u'/'.join((xdm.IMAGEPATH_RELATIVE,
                             unicode(self._instance.media_type),
                             unicode(self.img_name())
                             ))
            webrooted_url = u'%s/%s' % (common.SYSTEM.c.webRoot, url)
            return urllib.quote(webrooted_url.encode('utf-8'))
        else:
            return self.url

    def img_name(self):
        return helper.fileNameClean(
            u"{s._instance.id}-{s.name}-{s.provider}.{s.type}".format(s=self))

    def __cmp__(self, other):
        if self.provider == other.provider:
            return 0
        provider_tags = common.getProviderTags()
        if self.provider not in provider_tags:
            return 1
        if other.provider not in provider_tags:
            return -1

        if provider_tags.index(self.provider) < provider_tags.index(other.provider):
            return -1
        return 1

    def __repr__(self):
        return "Image: %s" % self.url


def overwriteable(func):
    def wrapper(self, *args, **kwargs):
        fn = self.manager.getFn(self.type, func.__name__)
        if fn:
            return fn(self, *args, **kwargs)
        return func(self, *args, **kwargs)
    return wrapper


class Element(Document):
    media_type = ReferenceField(MediaType, required=True)
    type = StringField(required=True)
    status = ReferenceField(Status, required=True, default=lambda: common.UNKNOWN)
    fields = ListField(EmbeddedDocumentField(Field))
    configs = ListField(EmbeddedDocumentField(Config))
    locations = ListField(EmbeddedDocumentField(Location))
    images = ListField(EmbeddedDocumentField(Image))
    #parent = ReferenceField("self")
    parent = GenericReferenceField()

    meta= {
        "cascade": False
    }


    __field_cache = {}
    __decendents_cache = []
    __ancestors_cache = []
    __XDMID_cache = {}


    def __init__(self, *args, **kwargs):
        super(Element, self).__init__(*args, **kwargs)
        self.clear_cache()

    def get_XDMID(self, tag=None):
        if tag not in self.__XDMID_cache:
            print "self:", self, self._get_collection(), self._get_collection_name()
            if self.parent:
                print "parent:", self.parent, self._get_collection(), self._get_collection_name()

            #if self.parent and not isinstance(self.parent, DBRef):
                XDMID = u"{}-{}".format(
                    self.parent.get_XDMID(tag),
                    self.getIdentifier(tag)
                )
            else:
                XDMID = u'r'
            self.__XDMID_cache[tag] = XDMID
        print self, self.__XDMID_cache[tag]
        return self.__XDMID_cache[tag]

    XDMID = property(get_XDMID)

    def clear_cache(self):
        self.__field_cache = {}
        self.__ancestors_cache = []
        self.__decendents_cache = []
        self.__XDMID_cache = {}

    def clear_lower_tree_cache(self):
        for child in self.children:
            child.clear_lower_tree_cache()
        self.clear_cache()

    def clear_upper_tree_cache(self):
        if self.parent:
            self.parent.clear_upper_tree_cache()
        self.clear_cache()

    def clear_tree_cache(self):
        self.clear_lower_tree_cache()
        self.clear_upper_tree_cache()

    def __str__(self):
        return '{s.type}({s.media_type.identifier})[{s.id}]'.format(
            s=self
        )

    def __repr__(self):
        return "<%s-%s>" % (self.type, self.id)

    def __eq__(self, other):
        if self.type != other.type:
            return False
        a_fields = list(self.fields)
        b_fields = list(other.fields)
        a_fields_dict = {f.name: f.value for f in a_fields}
        b_fields_dict = {f.name: f.value for f in b_fields}

        for b_name, b_value in b_fields_dict.items():
            if b_name not in a_fields_dict:

                print self, "!=", other
                return False
            if b_value != a_fields_dict[b_name]:
                print self, "!=", other
                return False
        print self, "==", other
        return True

    @overwriteable
    def get_name(self):
        return repr(self)

    @overwriteable
    def getTemplate(self):
        if self.leaf:
            return helper.getLeafTpl()
        else:
            return helper.getContainerTpl()

    @overwriteable
    def getSearchTemplate(self):
        return self.getTemplate()

    @overwriteable
    def getReleaseDate(self):
        return datetime.now()

    @overwriteable
    def getIdentifier(self, tag):
        return self.get_name()

    def isReleaseDateInPast(self):
        if isinstance(self.getReleaseDate(), (date, datetime)):
            return self.getReleaseDate() < datetime.now()
        return True

    @property
    def manager(self):
        if self.media_type is None:
            raise LookupError("No MediaType set! on %s" % self.id)
        try:
            return common.PM.getMediaTypeManager(self.media_type.identifier)[0]
        except IndexError:
            raise LookupError(
                "Could not find MediaTypeManager %s" % self.media_type.identifier)

    @property
    def orderReverse(self):
        return self.manager.getOrderReverse(self.type)

    @property
    def leaf(self):
        return self.manager.isTypeLeaf(self.type)

    @property
    def children(self):
        return Element.objects(parent=self)

    @property
    def ancestors(self):
        if not self.__ancestors_cache:
            if not self.parent:
                return []
            p = [self.parent]
            p.extend(self.parent.ancestors)
            self.__ancestors_cache = p
        return self.__ancestors_cache

    @property
    def decendants(self):
        # this is much faster with the cache !! wohhoo
        if not self.__decendents_cache:
            if not self.children:
                return []
            d = []
            for c in self.children:
                d.append(c)
                d.extend(c.decendants)
            self.__decendents_cache = d
        return self.__decendents_cache

    @property
    def order_by_fields(self):
        return self.manager.getOrderFields(self.type)

    @property
    def order_by_values(self):
        out = []
        for field in self.order_by_fields:
            out.append(self.get_field(field))
        return out

    def get_field(self, name, provider=None, returnObject=False):
        xdm_field = None
        for f in sorted(self.fields):
            if f.name == name and provider and f.provider == provider:
                if returnObject:
                    return f
                return f.value
            elif f.name == name and not provider:
                if f.provider == 'XDM':
                    xdm_field = f
                    continue
                if returnObject:
                    return f
                return f.value
        else:
            if xdm_field is not None:
                if returnObject:
                    return xdm_field
                return xdm_field.value
            return None

    def set_field(self, name, value, provider=''):
        if isinstance(value, date):
            value = datetime.combine(value, datetime.min.time())
        if isinstance(value, datetime):
            value = value.replace(tzinfo=pytz.UTC)

        f = self.get_field(name, provider, returnObject=True)
        if f is not None:
            f.value = value
            f.provider = provider
        else:
            f = Field()
            f.name = name
            f.value = value
            f.provider = provider
            self.fields.append(f)

    def _replace_fn(self, name):
        if name in self._overwriteable_functions and name not in self._fnChecked:
            fn = self.manager.getFn(self.type, name)
            self._fnChecked.append(name)
            if fn is not None:
                setattr(self, '_' + name, types.MethodType(fn, self))

        if name == 'getSearchTerms':
            return getattr(self, '_getSearchTermsWrapper')
        else:
            return getattr(self, '_' + name)

    def __getattr__(self, item):
        fd = self.get_field(item)
        if fd is not None:
            return fd
        else:
            raise AttributeError(
                "No attribute '%s' nor field with that name" % item)

    def paint(self, search=False, single=False, status=None, curIndex=0, onlyChildren=False):
        if status is None:
            if search:
                status = [common.TEMP]
            else:
                status = common.getHomeStatuses()
        if self.manager.download.__name__ == self.type and self.status not in status:
            return ''

        if not onlyChildren:
            html = self.buildHtml(search, curIndex=curIndex)
        else:
            html = '{{children}}'
        if single:
            return html

        children = self.children
        curIndex = 0
        orderReverse = False
        if len(children):
            orderReverse = children[0].orderReverse
        if '{{children}}' in html:
            for child in sorted(children,
                                key=lambda c: c.order_by_values,
                                reverse=orderReverse
                                ):
                html = html.replace(
                    '{{children}}',
                    '%s{{children}}' % child.paint(
                        search=search,
                        single=single,
                        status=status,
                        curIndex=curIndex),
                    1
                )
                curIndex += 1

        html = html.replace('{{children}}', '')
        return html

    def buildHtml(self, search=False, curIndex=0):
        if search:
            tpl = self.getSearchTemplate()
        else:
            tpl = self.getTemplate()
        tpl = unicode(tpl)
        webRoot = common.SYSTEM.c.webRoot
        elementTemplate = elementEnviroment.get_template(tpl)
        widgets_html = {}
        useInSearch = {'actionButtons': 'addButton',
                       'actionButtonsIcons': 'addButtonIcon',
                       'released': 'released'}

        for widget in WIDGETS:
            if (widget in useInSearch and search) or not search:
                if "{{%s}}" % widget not in tpl:
                    continue
                templateName = '%s.html' % widget
                if search:
                    templateName = '%s.html' % useInSearch[widget]
                curTemplate = elementWidgetEnvironment.get_template(
                    templateName)
                widgets_html[widget] = curTemplate.render(
                    this=self,
                    globalStatus=Status.objects,
                    webRoot=webRoot,
                    common=common)

        # Static infos / render stuff
        # status class
        statusCssClass = 'status-any status-%s' % self.status.name.lower()
        # add the field values to the widgets dict.
        # this makes the <field_name> available as {{<field_name>}}
        # in the templates
        widgets_html.update(self.buildFieldDict())

        return elementTemplate.render(
            children='{{children}}',
            this=self,
            statusCssClass=statusCssClass,
            loopIndex=curIndex,
            webRoot=webRoot,
            myUrl=self.manager.myUrl(),
            common=common,
            **widgets_html
        )

    def buildFieldDict(self):
        out = {}
        for f in self.fields:
            out[f.name] = f.value
            out['%s_%s' % (f.provider, f.name)] = f.value
        out['type'] = self.type
        return out

    @classmethod
    def object_by_fields(cls, fields, provider=None, media_type=None, parent=None):
        if provider:
            _fields = dict(fields)
            fields = [
                Field(name=field_name, provider=provider, value=field_value)
                for field_name, field_value in _fields.items()]
        criterion = {}
        if media_type:
            criterion["media_type"] = media_type
        if parent:
            criterion["parent"] = parent
        elements = Element.objects(**criterion)

        results = []
        for element in elements:
            if provider is None:
                attached_fields = [
                    Field(name=field.name, value=field.value)
                    for field in element.fields]
            else:
                attached_fields = element.fields
            if set(attached_fields) == set(fields):
                results.append(element)
        return results

    def switch_to_permanent(self, status=None, parent=None):
        child_cache = list(self.children)
        self.switch_collection("element")
        if status:
            self.status = status
        if parent:
            self.parent = parent
        self.save()
        log("made {} permanent, parent: {} ".format(
            self, parent))

        for child in child_cache:
            child.switch_to_permanent(status, self)

    def is_descendant_of(self, granny):
        return granny in self.ancestors

    def is_ancestor_of(self, jungstar):
        return jungstar in self.decendants

    def get_image_names(self):
        return [
            image_name for image_name in self.manager.getAttrs(self.type)
            if 'image' in image_name]

    def get_image(self, name, provider=''):
        for img in sorted(self.images):
            if img.name == name and provider and img.provider == provider:
                return img
            elif img.name == name and not provider:
                return img
        else:
            return None

    def getAnyImage(self):
        images = sorted(self.images)
        names = self.get_image_names()
        if names:
            for image in images:
                if names[0] == image.name:
                    return image
        return (images + [None])[0]

    def download_images(self):
        for image_name in self.get_image_names():
            for provider in common.getProviderTags():
                if self.get_field(image_name, provider):
                    self.download_image(image_name, provider)

    def download_image(self, image_name, provider=''):
        image = self.get_image(image_name, provider)
        if image is None:
            image = Image()
            image.name = image_name
        url = self.get_field(image_name, provider)
        if image.url == url and image.saved:
            return
        else:
            image.delete_file()
        image.url = url
        image.provider = provider
        image.download()
        image.save()
        self.images.append(image)
        self.save()

    def cascade_delete(self):
        for child in self.children:
            child.cascade_delete()
        self.delete()

    temp_collection = "temp_Element"

Element.with_temp = switch_collection(Element, "temp_Element")
Element.with_no_dereference = no_dereference(Element)


class Download(Document):
    element = ReferenceField(Element)
    name = StringField()
    url = URLField(unique=True)
    size = IntField()
    status = ReferenceField(Status)
    type = StringField()
    indexer = StringField()
    indexer_instance = StringField()
    external_id = StringField()
    pp_log = LineStringField()

    class Meta:
        db_table = 'Download'

    def humanSize(self):
        num = self.size
        if not num:
            return 'Unknown'
        for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if num < 1024.0:
                return "%3.1f %s" % (num, x)
            num /= 1024.0

class Repo(Document):
    name = StringField()
    url = URLField(unique=True)
    info_url = URLField()

    meta = {
        'ordering': ['name']
    }

class PluginConfig(DynamicDocument):
    name = StringField(required=True)
    instance = StringField(default='Default')
    configs = ListField(EmbeddedDocumentField(Config))

import inspect
def switch_collection_decorator(func):
    @wraps(func)
    def decorator(self, *args, **kwargs):
        with switch_collection(Element, Element.temp_collection):
            return func(self, *args, **kwargs)
    return decorator


def temp_element_wrapper(*args):
    """ Return a metaclass.
    usese the list of arguments as names of functions to wrap
    wraped functions are in a switch_collection context
    Elements are using the temp_Element collection
    """
    class TempElement(type):
        def __new__(cls, name, bases, local):
            for attr in local:
                if not attr in args:
                    continue
                value = local[attr]
                if callable(value):
                    local[attr] = switch_collection_decorator(value)
            return type.__new__(cls, name, bases, local)

    return TempElement


__all__ = [
    "Status",
    "Config",
    "MediaType",
    "Element",
    "Repo",
    "PluginConfig",
    "DoesNotExist",
    "Download",
    "switch_collection"]
