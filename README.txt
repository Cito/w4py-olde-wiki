Ian's Webware Wiki version 0.2
==============================

How to install this thing:
--------------------------

The Webware Wiki requires the following software:

* Python >= 2.3 (http://www.python.org)

* uTidylib >= 0.2 (http://utidylib.berlios.de) or
  mxTidy >= 3.0 (http://www.egenix.com/products/python/mxExperimental/mxTidy/)

* Docutils >= 0.4 (http://docutils.sourceforge.net)

* If you want to run the test modules, you need to install
  py.test (http://codespeak.net/py/dist/test.html).

* Webware version 1.0 and the Component 0.2 and LoginKit 0.1 plug-ins,
  (http://www.webwareforpython.org/downloads/Webware/Webware-1.0.tar.gz,
  http://www.webwareforpython.org/downloads/Component/Component-0.2.tar.gz,
  http://www.webwareforpython.org/downloads/LoginKit/LoginKit-0.1.tar.gz)

  In order to install Webware, unpack it to a directory like /usr/local/Webware
  and move the Component and LoginKit directories into the Webware directory.
  Then run the install.py script inside the Webware directory.

* Now you need to install the actual Wiki software. The download location is

    http://www.webwareforpython.org/downloads/Wiki/WebwareWiki-0.2.tar.gz

  You can unpack it as a subdirectory of the Webware directory or anywhere
  else, since this is not a Webware plugin, but just an additional library.

  You can also check out the latest version from the Subversion repository::

    svn co svn://svn.w4py.org/Wiki/trunk Wiki

* For WYSIWYG editing, the Wiki software needs to be supplemented with Xinha
  (http://xinha.webfactional.com), we were using Xinha 0.95 for this version.
  Unpack the software into the subdirectory ``Wiki/Context/xinha`` (note that
  the xinha subdirectory does not yet exist).

* The next step is to set up a new Webware Wiki working directory::

    $WEBWARE_DIR/bin/MakeAppWorkDir.py \
        -c Wiki -d $WIKI_DIR/Context -l $WIKI_DIR $WIKI_WORKDIR

  Here, WEBWARE_DIR is the directory where Webware is installed
  (e.g. /usr/local/Webware), WIKI_DIR is the directory where the Wiki
  library is installed (e.g. /usr/local/Webware/Wiki), and WIKI_WORKDIR
  is where the Webware Wiki working directory shall be created
  (e.g. /home/wiki/WorkDir).

* Copy the standard ``wiki.ini`` configuration file to the working directory::

    cp $WIKI_DIR/wiki.ini $WIKI_WORKDIR/Configs

  Customize ``$WIKI_WORKDIR/Configs/wiki.ini`` to fit your needs. The
  ``basepath`` setting in the global section is where all your Wikis will
  be stored (e.g. /var/lib/wiki). This should be writable by the AppServer.
  Also, for any domains there should be a section, like ``[vhost(localhost)]``
  -- if you have multiple domains that should serve the same wiki, use::

    [vhost(localhost)]
    canonical = canonical.domain.name

  You must also customize the configuration files used by Webware.
  Particularly, in ``$WIKI_WORKDIR/Configs/Application.config``, set::

    ExtraPathInfo = True

  Also, set ``ErrorEmailServer`` and ``ErrorEmailHeaders``.
  Remove all Webware contexts that you don't want to use.
  You should also customize the app server using the configuration file
  ``$WIKI_WORKDIR/Configs/AppServer.config``.

  In ``$WIKI_WORKDIR/Configs/AppServer.config``, add the path ``$WIKI_DIR``
  to the PlugInDirs list and make other appropriate changes.

Then you should be all set!

How to run this thing:
----------------------

Start the Webware application as usual, e.g. by running

    $WIKI_WORKDIR/AppServer

or by running the ``webkit`` start script under Unix. Under Windows,
you need to run ``AppServer.bat`` or use ``AppServerService.py``.
See also http://www.webwareforpython.org/Webware/WebKit/Docs/UsersGuide.html.

With the default settings in ``$WIKI_WORKDIR/Configs/AppServer.config``
you should now be able to access the Wiki at http://localhost:8080.

If you want to use Apache or another web server see also
http://www.w4py.org/Webware/WebKit/Docs/InstallGuide.html
and http://wiki.w4py.org/webserverintegration.html.

After creating a user account on the login page, you should grant yourself
as the first user the "admin" role, by editing the users/User-1.txt file
in the directory where the wiki is stored, so you can administer the wiki.


  -- Ian Bicking, 26 Apr 2004
  -- Updated by Christoph Zwerschke, 3 Jan 2009
