============
steamstalker
============

When are *your* friends playing?

A Django app that scrape the `Steam Community`_ to give historical data on
when your Steam friends are online.

.. _`Steam Community`: http://steamcommunity.com/


License
=======

New BSD


Requirements
============

* Python 2.6+
* Django 1.4.1+


Installation
============

Within your existing Django project:

* ``pip install https://github.com/toastdriven/steamstalker.git@master#egg=steamstalker``
* ``pip install -r path/to/steamstalker/requirements.txt``
* Add ``'steamstalker',`` to ``INSTALLED_APPS``
* Add ``url(r'^steamstalker/', include('steamstalker.urls')),`` to your ``urls.py``
* ``./manage.py migrate steamstalker``
* ``./manage.py collectstatic``
* Queue up ``./manage.py gotta_stalk_em_all`` in cron, preferably every 5 minutes (or more).
* Hit ``http://whatever.yourdomain.is/steamstalker/<your_steam_username>/`` to automatically start collecting data.
