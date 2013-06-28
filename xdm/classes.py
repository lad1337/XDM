# -*- coding: utf-8 -*-
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://github.com/lad1337/XDM
#
# This file is part of XDM: eXtentable Download Manager.
#
#XDM: eXtentable Download Manager. Plugin based media collection manager.
#Copyright (C) 2013  Dennis Lutter
#
#XDM is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#XDM is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see http://www.gnu.org/licenses/.

from lib.peewee import *
from lib.peewee import QueryCompiler
import os
import xdm
from lib import requests
from logger import *
from xdm import common, helper, profileMeMaybe
import datetime
import json
from jsonHelper import MyEncoder
from xdm.helper import dict_diff
import types

#from jinja2 import FileSystemBytecodeCache
from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader, DictLoader

#bcc = FileSystemBytecodeCache(pattern='%s.cache')
#, bytecode_cache=bcc

WIDGET_PATH = os.path.join('html', 'templates', 'widget')
elementWidgetEnvironment = Environment(loader=FileSystemLoader(WIDGET_PATH), extensions=['jinja2.ext.i18n'])
elementWidgetEnvironment.install_gettext_callables(_, ngettext, newstyle=True)
elementWidgetEnvironment.filters['relativeTime'] = helper.reltime
elementWidgetEnvironment.filters['idSafe'] = helper.replace_some

WIDGETS = []
for root, folders, files in os.walk(WIDGET_PATH):
    for curFile in files:
        WIDGETS.append(os.path.basename(curFile.split('.')[0]))


class BaseModel(Model):

    @classmethod
    def _checkForColumn(cls, field):
        table = cls._meta.db_table
        fields = cls._meta.database.execute_sql('PRAGMA table_info(%s)' % table).fetchall()
        for f in fields:
            if f[1] == field.db_column:
                return True
        else:
            return False

    @classmethod
    def _migrate(cls):
        return True # True like its all good !

    @classmethod
    def _migrateNewField(cls, newField):
        field = QueryCompiler().field_sql(newField)
        table = cls._meta.db_table
        if cls._checkForColumn(newField):
            return False # False like: dude stop !
        cls._meta.database.execute_sql('ALTER TABLE %s ADD COLUMN %s' % (table, field))
        return True

    @classmethod
    def updateTable(cls):
        supers = list(cls.__bases__)
        if supers[0] == BaseModel:
            log("no previous versions found for " + cls.__name__)
            return False
        for super_c in supers:
            next_super = None
            if super_c.__bases__:
                next_super = super_c.__bases__[0]
            if not next_super or next_super == BaseModel:
                break
            else:
                supers.append(next_super) # i know this is not 'cool' but this whole thing is pretty cool imo
        supers.reverse()
        log("found " + str(len(supers)) + " previous versions for " + cls.__name__)
        supers.append(cls)
        for super_c in supers:
            log("Calling _migrate() on %s" % super_c.__name__)
            if not super_c._migrate():
                log("Looks like we already migrated %s" % super_c.__name__)
                continue
        log("Create the final class: %s" % cls.__name__)
        try:
            cls.select().execute()
        except Exception, e:
            log("Error migrating: %s" % cls.__name__)
            raise e
        else:
            log("Migrating %s DONE!" % cls.__name__)
            return True

    class Meta:
        database = xdm.DATABASE

    def __str__(self):
        if hasattr(self, 'name'):
            return u'%s' % self.name
        super(BaseModel, self).__str__()

    def __add__(self, other):
        return str(self) + other

    def __radd__(self, other):
        return other + str(self)

    def save(self, force_insert=False, only=None):
        if self.__class__.__name__ == 'Element':
            if self.status != common.TEMP:
                History.createEvent(self)
        elif hasattr(self, 'element') and self:
            if self.element is not None and self.element.status != common.TEMP:
                History.createEvent(self)

        Model.save(self, force_insert=force_insert, only=only)

    def __json__(self):
        dic = dict(self.__dict__)
        if self.__class__.__name__ == 'Element':
            if '_tmp_fields' in dic:
                del dic['_tmp_fields']
                pass
            #TODO: rather check for bound method type
            for method in self._overwriteableFunctions:
                if method in dic:
                    del dic[method]
                if '_%s' % method in dic:
                    del dic['_%s' % method]
        return dic

    def _getEvents(self):
        return History.select().where(History.obj_class == self.__class__.__name__, History.obj_id == self.id)
    #events = property(_getEvents)


class Status_V0(BaseModel):
    name = CharField()

    class Meta:
        db_table = 'Status'

    def save(self, do=False):
        if do:
            super(Status_V0, self).save()


# thats how you update a model
class Status(Status_V0):
    hidden = BooleanField(True, default=False)

    @classmethod
    def _migrate(cls):
        field = QueryCompiler().field_sql(cls.hidden)
        table = cls._meta.db_table
        if cls._checkForColumn(cls.hidden):
            return False # False like: dude stop !
        cls._meta.database.execute_sql('ALTER TABLE %s ADD COLUMN %s' % (table, field))
        return True

    def _screenName(self):
        return lgettext(self.name)
    screenName = property(_screenName)


class MediaType(BaseModel):
    name = CharField()
    identifier = CharField()

    def _getMyManager(self):
        return common.PM.getMediaTypeManager(self.identifier)[0]
    manager = property(_getMyManager)

    def __str__(self):
        return str(self.identifier)

    class Meta:
        indexes = (
            # create a unique on from/to
            (('identifier',), True),
        )


class Element(BaseModel):
    mediaType = ForeignKeyField(MediaType)
    type = CharField()
    parent = ForeignKeyField('self', related_name='children', null=True)
    status = ForeignKeyField(Status)
    _overwriteableFunctions = ('getTemplate', 'getSearchTerms', 'getName', 'getSearchTemplate', 'getReleaseDate')
    _tmp_fields = []

    def __init__(self, *args, **kwargs):
        self._tmp_fields = []
        self._fnChecked = []
        super(Element, self).__init__(*args, **kwargs)
        self.__fieldCache = list(self.fields)

    def __str__(self):
        return '%s(%s)[%s] %s' % (self.type, self.mediaType, self.get_id(), self.getName())

    def copy(self):
        new = Element()
        new.mediaType = self.mediaType
        new.type = self.type
        new.parent = self.parent
        new.status = self.status
        new.id = None
        for f in self.fields:
            new.setField(f.name, f.value, f.provider)
        return new

    def _replaceFn(self, name):
        if name in self._overwriteableFunctions and name not in self._fnChecked:
            fn = self.manager.getFn(self.type, name)
            self._fnChecked.append(name)
            if fn is not None:
                    setattr(self, '_' + name, types.MethodType(fn, self))

        if name == 'getSearchTerms':
            return getattr(self, '_getSearchTermsWrapper')
        else:
            return getattr(self, '_' + name)

    def __getattribute__(self, name):
        if name in BaseModel.__getattribute__(self, '_overwriteableFunctions'):
            return self._replaceFn(name)
        try:
            return BaseModel.__getattribute__(self, name)
        except AttributeError: #WARNING this can hide Attribute errors of other classes / instances down the road and will report a false error message!
            if 'image' in name:
                img = self.getImage(name)
                if img is not None:
                    return img.getSrc()
            fd = self.getField(name)
            if fd is not None:
                return fd
            else:
                raise AttributeError("No attribute '%s' nor field with that name" % name)

    def getImage(self, name, provider=''):
        for img in self.images:
            if img.name == name and provider and img.provider == provider:
                return img
            elif img.name == name:
                return img
        else:
            return None

    def getField(self, name, provider=None, returnObject=False):
        #this is faster then a db query oO
        #my mother had me tested
        xdm_field = None
        for f in list(self.fields) + self._tmp_fields:
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

    def setField(self, name, value, provider=''):
        f = self.getField(name, provider, returnObject=True)
        if f is not None:
                f.value = value
                f.provider = provider
                f.save()
        else: # field does not exist
            if  self.id: # do we exist ? yes
                f = Field()
                f.element = self
                f.name = name
                f.value = value
                f.provider = provider
                f.save()
            else: # we dont exist and we need to create your field
                f = Field()
                f.name = name
                f.value = value
                f.provider = provider
                self._tmp_fields.append(f)

    def saveTemp(self):
        self.status = common.TEMP
        self.save(fixTemp=False)

    def save(self, fixTemp=True):
        try:
            self.status
        except Status.DoesNotExist:
            self.status = common.UNKNOWN
        if fixTemp and self.status == common.TEMP:
            self.status = common.UNKNOWN
        super(Element, self).save()
        for f in self._tmp_fields:
            #print 'saving tmp field on', self.id, f.name, f.value
            f.element = self
            f.save()
        self._tmp_fields = []

    def _getMyManager(self):
        return common.PM.getMediaTypeManager(self.mediaType.identifier)[0]
    manager = property(_getMyManager)

    def _amIaLeaf(self):
        return self.manager.isTypeLeaf(self.type)
    leaf = property(_amIaLeaf)

    def getTemplate(self):
        return self._getTemplate()

    def _getTemplate(self):
        if self.leaf:
            return helper.getLeafTpl()
        else:
            return helper.getContainerTpl()

    def getSearchTemplate(self):
        return self.getTemplate()

    def _getSearchTemplate(self):
        return self.getTemplate()

    def getSearchTerms(self):
        return self._getSearchTermsWrapper()

    def _getSearchTerms(self):
        return [self.getName()]

    def _getSearchTermsWrapper(self):
        terms = self._getSearchTerms()
        for curFilter in common.PM.getSearchTermFilters(runFor=self.manager):
            log('Running %s on terms: %s' % (curFilter, terms))
            terms += curFilter.compare(self, terms)
        finalSet = list(set(terms))
        log('Final search term set for %s is: %s' % (self, finalSet))
        return finalSet

    def imgName(self):
        return "%s (%s).jpeg" % (helper.replace_all(self.name), self.id)

    def imgPath(self):
        return os.path.join(xdm.IMAGEPATH_RELATIVE, self.type, self.imgName())

    def buildHtml(self, search=False, curIndex=0):
        if search:
            tpl = self.getSearchTemplate()
        else:
            tpl = self.getTemplate()
        #print "template for %s is #####:\n%s\n" % (self, tpl)

        webRoot = common.SYSTEM.c.webRoot
        env = Environment(loader=DictLoader({'this': tpl}), extensions=['jinja2.ext.i18n'])
        env.install_gettext_callables(_, ngettext, newstyle=True)
        env.filters['relativeTime'] = helper.reltime
        env.filters['idSafe'] = helper.replace_some
        elementTemplate = env.get_template('this')

        widgets_html = {}
        useInSearch = {'actionButtons': 'addButton', 'actionButtonsIcons': 'addButtonIcon', 'released': 'released'}

        for widget in WIDGETS:
            if (widget in useInSearch and search) or not search:
                if "{{%s}}" % widget in tpl:
                    templateName = '%s.html' % widget
                    if search:
                        templateName = '%s.html' % useInSearch[widget]
                    curTemplate = elementWidgetEnvironment.get_template(templateName)
                    widgets_html[widget] = curTemplate.render(this=self, globalStatus=Status.select(), webRoot=webRoot)

        #Static infos / render stuff
        # status class
        statusCssClass = 'status-any status-%s' % self.status.name.lower()
        # add the field values to the widgets dict. this makes the <field_name> available as {{<field_name>}} in the templates
        widgets_html.update(self.buildFieldDict())

        return elementTemplate.render(children='{{children}}',
                                      this=self,
                                      statusCssClass=statusCssClass,
                                      loopIndex=curIndex,
                                      webRoot=webRoot,
                                      **widgets_html)

    def buildFieldDict(self):
        out = {}
        for f in self.fields:
            out[f.name] = f.value
            out['%s_%s' % (f.provider, f.name)] = f.value
        out['type'] = self.type
        return out

    def getDefinedAttr(self):
        attrs = {}
        for attr in self.manager.getAttrs(self.type):
            attrs[attr] = self.getField(attr)
        return attrs

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

        children = Element.select().where(Element.parent == self.id)
        curIndex = 0
        if '{{children}}' in html:
            for child in sorted(children, key=lambda c: c.orderFieldValues):
                html = html.replace('{{children}}', '%s{{children}}' % child.paint(search=search, single=single, status=status, curIndex=curIndex), 1)
                curIndex += 1

        html = html.replace('{{children}}', '')
        return html

    def _getOrderFields(self):
        return self.manager.getOrderFields(self.type)

    orderFields = property(_getOrderFields)

    def _getOrderFieldValues(self):
        out = []
        for field in self.orderFields:
            out.append(self.getField(field))
        return out

    orderFieldValues = property(_getOrderFieldValues)

    def _getAllAncestorss(self):
        if not self.parent:
            return []
        p = [self.parent]
        p.extend(self.parent.ancestors)
        return p

    ancestors = property(_getAllAncestorss)

    def _getAllDescendants(self):
        if not self.children:
            return []
        d = []
        for c in Element.select().where(Element.parent == self.id):
            d.append(c)
            d.extend(c.decendants)
        return d

    decendants = property(_getAllDescendants)

    def getName(self):
        return self._getName

    def _getName(self):
        return ' '.join([str(x.value) for x in self.fields])

    def getReleaseDate(self):
        return self._getReleaseDate

    def _getReleaseDate(self):
        return datetime.datetime.now()

    def isReleaseDateInPast(self):
        if type(self.getReleaseDate()).__name__ in ('date', 'datetime'):
            return self.getReleaseDate() < datetime.datetime.now()
        return True

    def isDescendantOf(self, granny):
        return granny in self.ancestors

    def isAncestorOf(self, jungstar):
        return jungstar in self.decendants

    def downloadImages(self):
        imageNames = [imageName for imageName in self.manager.getAttrs(self.type) if 'image' in imageName]
        for cImageName in imageNames:
            if self.getField(cImageName):
                self.downloadImage(cImageName)

    def downloadImage(self, imageName):
        img = self.getImage(imageName)
        if img is None:
            img = Image()
            img.name = imageName
            img.element = self
        img.url = self.getField(imageName)
        img.cacheImage()
        img.save()

    @classmethod
    def getWhereField(cls, mt, type, attributes, provider='', parent=0):
        fs = list(Field.select().where(Field.name << attributes.keys(), Field.provider == provider).order_by(Field.element))
        last_e = None
        lastAttributeOK = False
        for f in fs:
            if parent and f.element.parent != parent:
                continue
            if last_e != f.element:
                if lastAttributeOK:
                    #last one was cool
                    return last_e
                lastAttributeOK = False
                last_e = f.element
            lastAttributeOK = u'%s' % attributes[f.name] == u'%s' % f.value
        raise Element.DoesNotExist

    def deleteWithChildren(self, silent=False):
        if not silent:
            log.info("Deleting: %s(%s)" % (self, self.id))
        cs = list(Element.select().where(Element.parent == self.id))
        for c in cs:
            c.deleteWithChildren(silent)
        self.delete_instance(silent)

    def deleteFields(self):
        for f in list(self.fields):
            f.delete_instance()

    def deleteImages(self):
        for i in list(self.images):
            i.delete_instance()

    def deleteDownloads(self):
        return Download.delete().where(Download.element == self).execute()

    def deleteHistory(self):
        return History.delete().where(History.obj_id == self.id).execute()

    def deleteConfig(self):
        return Config.delete().where(Config.element == self.id).execute()

    def delete_instance(self, silent=False):
        if not silent:
            log("Deleting instance: %s(%s)" % (self, self.id))
        self.deleteImages()
        self.deleteFields()
        self.deleteDownloads()
        self.deleteHistory()
        self.deleteConfig()
        super(Element, self).delete_instance()

    def getConfigs(self):
        return Config.select().where(Config.obj_id == self.id)

    def getConfig(self, plugin, configName):
        try:
            return Config.get(Config.element == self,
                              Config.name == configName,
                              Config.instance == plugin.instance,
                              Config.section == plugin.type,
                              Config.module == 'Plugin')
        except Config.DoesNotExist:
            return None


class Field_V0(BaseModel):
    element = ForeignKeyField(Element, related_name='fields')
    name = CharField()
    provider = CharField()
    _value_int = FloatField(True)
    _value_char = TextField(True)
    _value_bool = IntegerField(True)

    class Meta:
        db_table = 'Field'

    def __str__(self):
        return 'Field of %s name:%s value:%s' % (self.element, self.name, self.value)


class Field(Field_V0):
    _value_datetime = DateTimeField(True)

    @classmethod
    def _migrate(cls):
        return cls._migrateNewField(cls._value_datetime)

    def _get_value(self):
        if self._value_bool in (1, 0):
            return self._value_bool
        elif self._value_int != None:
            # this is only not a float when the field was not saved
            if type(self._value_int) is not int and self._value_int.is_integer():
                return int(self._value_int)
            return self._value_int
        elif self._value_datetime != None:
            return self._value_datetime
        else:
            return self._value_char

    def _set_value(self, value):

        # convert strings such as '12' to ints
        try:
            value = int(value)
        except (ValueError, TypeError):
            pass

        if type(value).__name__ in ('int', 'float'):
            self._value_char = None
            self._value_bool = None
            self._value_datetime = None
            self._value_int = value
            return
        if type(value).__name__ in ('str', 'unicode'):
            self._value_bool = None
            self._value_int = None
            self._value_datetime = None
            self._value_char = value
            return
        if type(value).__name__ in ('bool', 'NoneType'):
            self._value_char = None
            self._value_int = None
            self._value_datetime = None
            self._value_bool = value
            return
        if type(value).__name__ in ('date', 'datetime'):
            self._value_char = None
            self._value_int = None
            self._value_bool = None
            self._value_datetime = value
            return
        raise TypeError('unknown config save type %s for config %s' % (type(value), self.name))

    value = property(_get_value, _set_value)


class Config(BaseModel):
    module = CharField(default='system') # system, plugin ... you know this kind of thing
    section = CharField() # sabnzb, newznab -> plugin name or system section
    instance = CharField(default='Default') # for multiple configurations for the same plugin
    name = CharField() # name of the value to save
    type = CharField(null=True) # the type of the config like category enabled or stuff
    mediaType = ForeignKeyField(MediaType, null=True) # this is used when a media type creates a config for someone else
    element = ForeignKeyField(Element, null=True) # this is used when a config is created from a media type for an element
    _value_int = FloatField(True)
    _value_char = CharField(True)
    _value_bool = BooleanField(True)

    class Meta:
        database = xdm.CONFIG_DATABASE
        order_by = ('name',)

    def copy(self):
        new = Config()
        new.module = self.module
        new.section = self.section
        new.instance = self.instance
        new.name = self.name
        new.type = self.type
        new.mediaType = self.mediaType
        new.element = self.element
        new.id = None
        return new

    def _get_value(self):
        if self._value_bool in (1, 0):
            return self._value_bool
        elif self._value_int != None:
            if float(self._value_int).is_integer():
                return int(self._value_int)
            return self._value_int
        else:
            return self._value_char

    def _set_value(self, value):
        if type(value).__name__ in ('float', 'int'):
            self._value_char = None
            self._value_bool = None
            self._value_int = value
            return
        if type(value).__name__ in ('str', 'unicode'):
            self._value_bool = None
            self._value_int = None
            self._value_char = value
            return
        if type(value).__name__ in ('bool', 'NoneType'):
            self._value_char = None
            self._value_int = None
            self._value_bool = value
            return
        raise Exception('unknown config save type %s for config %s' % (type(value), self.name))

    value = property(_get_value, _set_value)

    def curType(self):
        if self._value_bool in (1, 0):
            return 'bool'
        elif self._value_int:
            return 'int'
        else:
            return 'str'


class Download_V0(BaseModel):
    element = ForeignKeyField(Element, related_name='downloads')
    name = CharField()
    url = CharField(unique=True)
    size = IntegerField(True)
    status = ForeignKeyField(Status)
    type = CharField()
    indexer = CharField(True)
    indexer_instance = CharField(True)
    external_id = CharField(True)
    pp_log = TextField(True)

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


class Download(Download_V0):
    pp_log = TextField(True)

    @classmethod
    def _migrate(cls):
        field = QueryCompiler().field_sql(cls.pp_log)
        table = cls._meta.db_table
        if cls._checkForColumn(cls.pp_log):
            return False # False like: dude stop !
        cls._meta.database.execute_sql('ALTER TABLE %s ADD COLUMN %s' % (table, field))
        return True


class History(BaseModel):
    time = DateTimeField(default=datetime.datetime.now())
    event = CharField()
    obj_id = IntegerField()
    obj_class = CharField()
    obj_type = CharField()
    old_obj = TextField()
    new_obj = TextField()

    class Meta():
        database = xdm.HISTORY_DATABASE
        order_by = ('-time',)

    def save(self, force_insert=False, only=None):
        self.time = datetime.datetime.now()
        Model.save(self, force_insert=force_insert, only=only)

    @classmethod
    def createEvent(thisCls, obj):
        h = thisCls()
        try:
            old = obj.__class__.get(obj.__class__.id == obj.id)
        except obj.__class__.DoesNotExist:
            old = {}
            h.obj_id = 0
            h.event = 'insert'
        else:
            h.obj_id = old.id
            h.event = 'update'
        if obj.__class__.__name__ == 'Element':
            h.game = obj.id
        elif hasattr(obj, 'element'):
            h.game = obj.element
        h.old_obj = json.dumps(old, cls=MyEncoder)
        h.new_obj = json.dumps(obj, cls=MyEncoder)
        h.obj_class = obj.__class__.__name__
        if hasattr(obj, 'type'):
            h.obj_type = obj.type
        else:
            h.obj_type = obj.__class__.__name__

        if not h.obj_type:
            log.warning('While creating a history event had no obj_type not creating event. %s' % obj)
            return

        if h.event == 'insert' and dict_diff(old, obj.__dict__):
            h.save()
        if h.event == 'update' and dict_diff(old.__dict__, obj.__dict__):
            h.save()

    def _old(self):
        myJ = json.loads(self.old_obj)
        if '_data' in myJ:
            return myJ['_data']
        else:
            return False

    def _new(self):
        myJ = json.loads(self.new_obj)
        if '_data' in myJ:
            return myJ['_data']
        else:
            return False

    def human(self):
        if self.obj_class == 'Element':
            return self._humanElement()
        elif self.obj_class == 'Download':
            return self._humanDownload()
        elif self.obj_class == 'GenericEvent':
            return self._new()['msg']
        elif self.obj_class == 'Config':
            return self._humanConfig()
        return "not implemented for %s" % self.obj_class

    def _humanConfig(self):
        data_o = self._old()
        data_n = self._new()
        if data_n and data_o:
            return '%s' % self._humanDict(dict_diff(data_n, data_o))
        return 'unknown Config change'

    def _humanElement(self):
        data_o = self._old()
        data_n = self._new()
        if data_n and data_o:
            if self.event == 'update':
                if 'status' in data_n:
                    if data_n['status'] != data_o['status']:
                        return 'new status %s ' % Status.get(Status.id == data_n['status'])
                    elif data_n['status'] == data_o['status'] and data_o['status'] == common.SNATCHED.id:
                        return 'Resantched: %s' % Element.get(Element.id == data_n['id'])
                diff = dict_diff(data_n, data_o)
                if diff:
                    return '%s' % diff
                else:
                    return 'Save without a data change.'
            else:
                return data_n['msg']
        return 'this case of Element history is not implemented'

    def _humanDownload(self):
        data_o = self._old()
        data_n = self._new()
        if data_n and data_o:
            if self.event == 'update':
                if data_n['status'] != data_o['status']:
                    return 'marked download as %s ' % Status.get(Status.id == data_n['status'])
                elif data_n['status'] == data_o['status'] and data_o['status'] == common.SNATCHED.id:
                    return 'Download resantched: %s' % Download.get(Download.id == data_n['id'])
                diff = dict_diff(data_n, data_o)
                if diff:
                    return '%s' % diff
                else:
                    return 'Save without a data change.'
            else:
                return data_n['msg']
        return 'this case of download history is not implemented'

    def _humanDict(self, diff):
        out = []
        for k, vs in diff.items():
            if '_value' in k:
                k = 'value'
            out.append("%s from '%s' to '%s'" % (k, vs[1], vs[0]))
        return u'updated %s' % ", ".join(out)


class Image(BaseModel):
    name = TextField()
    url = TextField()
    type = TextField()
    element = ForeignKeyField(Element, related_name='images')

    def _extByHeader(self, contentType):
        out = 'jpeg'
        if contentType == 'image/jpeg':
            out = 'jpeg'
        if contentType == 'image/png':
            out = 'png'
        if contentType == 'image/gif':
            out = 'gif'
        if contentType == 'image/bmp':
            out = 'bmp'
        return out

    def __str__(self):
        return self.getSrc()

    def delete_instance(self):
        try:
            os.remove(self.getPath())
        except OSError:
            pass
        super(Image, self).delete_instance()

    def cacheImage(self):
        if not self.url:
            return
        log("Downloading image: %s %s" % (self.name, self.url))
        try:
            r = requests.get(self.url)
        except requests.exceptions.MissingSchema:
            log.error("Downloading image %s failed" % self.url)
            self.type = self._extByHeader('')
            return
        self.type = self._extByHeader(r.headers['content-type'])
        if r.status_code == 200:
            with open(self.getPath(), 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)

    def getPath(self):
        directory = os.path.join(xdm.IMAGEPATH, str(self.element.mediaType))
        if not os.path.exists(directory):
            os.makedirs(directory)

        return os.path.join(directory, self.imgName())

    def getSrc(self):
        if self.type: # type is only set after we down loaded the image
            return '%s/%s' % (common.SYSTEM.c.webRoot, os.path.join(xdm.IMAGEPATH_RELATIVE, str(self.element.mediaType), self.imgName()).replace(xdm.PROGDIR, ''))
        else:
            return self.url

    def imgName(self):
        return helper.fileNameClean("%s (%s) %s.%s" % (helper.replace_all(self.element.getName()), self.element.id, self.name, self.type))


class Repo(BaseModel):
    name = CharField()
    url = CharField()
    info_url = CharField()

    class Meta:
        database = xdm.CONFIG_DATABASE
        order_by = ('name',)


__all__ = ['Status', 'Config', 'Download', 'History', 'Element', 'MediaType', 'Field', 'Image', 'Repo']
