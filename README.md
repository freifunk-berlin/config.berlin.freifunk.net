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


How to run nipap-wizard for development
-------------------------------------------

You need to have python-virtualenv installed

Install

    $ git clone https://github.com/freifunk-berlin/config.berlin.freifunk.net.git nipap-wizard
    $ cd nipap-wizard
    $ virtualenv --python=python3 venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt
    $ cp config.cfg.dist config.cfg
    $ vim config.cfg     # add MAIL_PORT = 1025 for development

We use flask-migrate for database creation and migrations. To create our
database and tables you have to use the following commands:

    $ python manage.py db init
    $ python manage.py db migrate
    $ python manage.py db upgrade

Dev Server (including dev smtp server for emails)

    $ python -m smtpd -n -c DebuggingServer localhost:1025
    $ flask run 

