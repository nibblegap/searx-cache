searx
=====

A privacy-respecting, hackable `metasearch
engine <https://en.wikipedia.org/wiki/Metasearch_engine>`__.

Pronunciation: səːks

List of `running
instances <https://github.com/asciimoo/searx/wiki/Searx-instances>`__.

See the `documentation <https://asciimoo.github.io/searx>`__ and the `wiki <https://github.com/asciimoo/searx/wiki>`__ for more information.

|OpenCollective searx backers|
|OpenCollective searx sponsors|

Setup MySql
~~~~~~~~~~~

**Install MySql**
 ``$ sudo apt-get install mysql-server
 $ pip install pymysql``

**Start MySql**
 ``$ sudo service mysql start
 $ mysql -u root -p``

**Create a new database and give all rights to a new searx user**
 change password!
 
 ``mysql> create database searx;
 mysql> create user "searx"@"localhost" identified by "password";
 mysql> grant all on searx.* to "searx"@"localhost" identified by "password";``

**You can now quit the MySql console by typing ``quit`` and connect as searx user**
 ``$ mysql -u searx -p``
 
**Here are some commands to init the database**
 ``mysql> use searx;``

 ``mysql> create table SEARCH_HISTORY(QUERY varchar(512), CATEGORY varchar(256), PAGENO int(11), PAGING tinyint(1), SAFE_SEARCH int(11), LANGUAGE varchar(8), TIME_RANGE varchar(16), ENGINES varchar(4096), RESULTS mediumtext, RESULTS_NUMBER int(11), ANSWERS varchar(2048), CORRECTIONS varchar(256), INFOBOXES varchar(8192), SUGGESTIONS varchar(1024), UNRESPONSIVE_ENGINES varchar(1024));``
 
 ``mysql> quit``
 
 MySql is done !

Installation
~~~~~~~~~~~~

-  clone source:
   ``git clone https://gitlab.eelo.io/spot/my-spot.git && cd my-spot``
-  install dependencies: ``./manage.sh update_packages``
-  edit your
   `settings.yml <https://github.com/asciimoo/searx/blob/master/searx/settings.yml>`__
   (set your ``secret_key`` and ``mysql password``!)
-  run ``python searx/webapp.py`` to start the application

For all the details, follow this `step by step
installation <https://github.com/asciimoo/searx/wiki/Installation>`__.

Bugs
~~~~

Bugs or suggestions? Visit the `issue
tracker <https://github.com/asciimoo/searx/issues>`__.

`License <https://github.com/asciimoo/searx/blob/master/LICENSE>`__
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

More about searx
~~~~~~~~~~~~~~~~

-  `openhub <https://www.openhub.net/p/searx/>`__
-  `twitter <https://twitter.com/Searx_engine>`__
-  IRC: #searx @ freenode


.. |OpenCollective searx backers| image:: https://opencollective.com/searx/backers/badge.svg
   :target: https://opencollective.com/searx#backer


.. |OpenCollective searx sponsors| image:: https://opencollective.com/searx/sponsors/badge.svg
   :target: https://opencollective.com/searx#sponsor
