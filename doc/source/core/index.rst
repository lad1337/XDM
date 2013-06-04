
Core
****


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

::

   xdm.common -+
               |
               #- instantiated during import #
               +- MM -- xdm.message.MessageManager - instance
               +- SM -- xdm.message.SystemMessageManager - instance
               +- NM -- xdm.news.NewsManager - instance
               +- SCHEDULER -- xdm.scheduler.Scheduler - instance
               |
               #- instantiated during App.__init__() #               
               +- PM -- xdm.plugin.pluginManager.PluginManager - instance
               +- SYSTEM -- plugins.system.System.System - instance
               +- UPDATER -- xdm.updater.Updater - instance
               +- REPOMANAGER -- xdm.plugins.repository.RepoManager - instance
               +- APIKEY -- str
               |
               # Statuses available for Elements 
               # set during xdm.init_checkDefaults() (done in xdm.init.db() in App.__init__()) #
               +- UNKNOWN -- xdm.classes.Status - instance # no status
               +- WANTED -- xdm.classes.Status - instance # default status
               +- SNATCHED -- xdm.classes.Status - instance # well snatched and the downloader is getting it ... so we hope
               +- DOWNLOADING -- xdm.classes.Status - instance # its currently downloading woohhooo
               +- DOWNLOADED -- xdm.classes.Status - instance # no status thingy
               +- COMPLETED -- xdm.classes.Status - instance # downloaded and pp_success
               +- FAILED -- xdm.classes.Status - instance # download failed
               +- PP_FAIL -- xdm.classes.Status - instance # post processing failed
               +- DELETED -- xdm.classes.Status - instance # marked as deleted
               +- IGNORE -- xdm.classes.Status - instance # ignore this item
               +- TEMP -- xdm.classes.Status - instance # temporary item like from a search
               |


.. autoclass:: xdm.Common
   :members:

