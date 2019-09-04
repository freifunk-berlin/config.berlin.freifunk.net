config.berlin.freifunk.net Freifunk Berlin IPAM
===============================================

Our ip address management system is basically a running NIPAP instance
(see https://spritelink.github.io/NIPAP/ ) with two frontends:
* nipap-www for advanced users (typically backbone maintainers)
* nipap-wizard for others (available at https://config.berlin.freifunk.net/ )

How to install nipap for development
------------------------------------
The following is mostly outdated. Just follow
https://spritelink.github.io/NIPAP/docs/INSTALL.html
and use the prebuilt packages.
Make sure the `postgresql-X.Y-ip4r` package is installed as well.

Outdated:
The Makefile in v0.26.4 seems to be broken. There are patches in directory
`patches` to fix this. You will need `postgresql` and `virtualenv2` as well.

Get source and patch it:

```
$ git clone git@github.com:freifunk-berlin/config.berlin.freifunk.net.git
$ git clone https://github.com/SpriteLink/NIPAP
$ cd NIPAP
$ virtualenv2 env
$ . env/bin/activate
$ cd nipap
$ pip install -r requirements.txt
$ cd ..
$ git checkout v0.26.4
$ patch -p1 < ../nipap-wizard/patches/0001-Do-not-install-files-globally-no-root-privileges-nee.patch
$ patch -p1 < ../nipap-wizard/patches/0002-Fix-Makefile-tables-seems-to-be-in-the-wrong-order.patch
$ bash utilities/install-ip4r.sh
```

Install nipap:

```
$ cd nipap
$ python setup install
$ cp nipap.conf.dist nipap.conf
$ vim nipap.conf    # set debug=True, pid_file and db_path (something locally)
$ python nipap-passwd -c nipap.conf --create-database
$ cd ..
```

Install pynipap:

```
$ cd ../pynipap
$ python setup install
```

Install nipap-www:

```
$ cd nipap
# add user 'foo' with password 'bar'
$ python nipap-passwd -c nipap.conf -a foo -p bar -n 'NIPAP web UI' -t
$ vim nipap.conf                  # set xmlrpc_uri
$ cd ../nipap-www
$ cp development.ini devel.ini
$ vim devel.ini                   # set nipap_config_path
$ python setup.py install
$ pip install WebOb==1.3.1        # see https://github.com/SpriteLink/NIPAP/issues/624
$ cd ..
```

Start everything:

```
$ cd nipap
$ python nipapd -c nipap.conf
...
$ cd nipap-www
$ paster serve devel.ini
```

Nipap and nipap-www should run now: http://127.0.0.1:5000

How to run nipap-wizard for development
-------------------------------------------

Install

    $ cd nipap-wizard
    $ pip install -r requirements.txt
    $ cp config.cfg.dist config.cfg
    $ vim config.cfg                    # add MAIL_PORT = 1025 for development

We use flask-migrate for database creation and migrations. To create our
database and tables you have to use the following commands:

    $ python manage.py db init
    $ python manage.py db migrate
    $ python manage.py db upgrade


Dev Server (including dev smtp server for emails)

    $ python -m smtpd -n -c DebuggingServer localhost:1025
    $ python manage.py runserver -p 5001
     * Running on http://127.0.0.1:5001/
     * Restarting with reloader
