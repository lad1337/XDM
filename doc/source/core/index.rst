
Core
****

.. toctree::
   :glob:
   
   *


Boot structure
==============

::

   XDM.py
   main() -+
           |
         App() --+
                 |
                 +- __init__() -+
                 |              |
                 |              +-- command line options handling / parsing
                 |              +-- xdm.init.preDB(): path and folder setup
                 |              +-- xdm.init.db(): dabase initialisation and migration
                 |              +-- xdm.init.postDB(): plugin loading
                 |              +-- init.schedule(): recuring shedular setup and starting
                 |              +-- init.runTasks(): initial (cleanup) tasks
                 |
                 +- startWebServer(): (optional)
                 |
                 |
                 +- starting of the API: (optional)
                 |
                 |
                 +- main while loop with KeyboardInterrupt handler
                 
The common object
=================

There is a xdm.common object based on xdm.Common_

.. _xdm.Common: #xdm.Common

**instantiated during import**

- ``MM`` -- xdm.message.MessageManager_ - instance
- ``SM`` -- xdm.message.SystemMessageManager_ - instance
- ``NM`` -- xdm.news.NewsManager_ - instance
- ``SCHEDULER`` -- xdm.scheduler.Scheduler_ - instance

.. _xdm.message.MessageManager: message.html#xdm.message.MessageManager
.. _xdm.message.SystemMessageManager: message.html#xdm.message.SystemMessageManager
.. _xdm.news.NewsManager: news.html#xdm.news.NewsManager
.. _xdm.scheduler.Scheduler: scheduler.html#xdm.scheduler.Scheduler

**instantiated during boot**

- ``PM`` -- xdm.plugin.pluginManager.PluginManager_ - instance
- ``SYSTEM`` -- plugins.system.System.System_ - instance
- ``UPDATER`` -- xdm.updater.Updater_ - instance
- ``REPOMANAGER`` -- xdm.plugins.repository.RepoManager_ - instance
- ``APIKEY`` -- str

.. _xdm.plugin.pluginManager.PluginManager: ../plugin/pluginManager.html
.. _plugins.system.System.System: ../plugin/plugins/System.html
.. _xdm.updater.Updater: updater.html#Updater
.. _xdm.plugins.repository.RepoManager: ../plugin/repo.html#RepoManager

**Statuses available for Elements**
set during xdm.init_checkDefaults() (done in xdm.init.db() in App.__init__())

- ``UNKNOWN`` -- xdm.classes.Status - instance # no status
- ``WANTED`` -- xdm.classes.Status - instance # default status
- ``SNATCHED`` -- xdm.classes.Status - instance # well snatched and the downloader is getting it ... so we hope
- ``DOWNLOADING`` -- xdm.classes.Status - instance # its currently downloading woohhooo
- ``DOWNLOADED`` -- xdm.classes.Status - instance # no status thingy
- ``COMPLETED`` -- xdm.classes.Status - instance # downloaded and pp_success
- ``FAILED`` -- xdm.classes.Status - instance # download failed
- ``PP_FAIL`` -- xdm.classes.Status - instance # post processing failed
- ``DELETED`` -- xdm.classes.Status - instance # marked as deleted
- ``IGNORE`` -- xdm.classes.Status - instance # ignore this item
- ``TEMP`` -- xdm.classes.Status - instance # temporary item like from a search



.. autoclass:: xdm.Common
   :members:

