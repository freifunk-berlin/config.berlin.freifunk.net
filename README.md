# Freifunk Berlin IPAM

Our ip address management system is running a
[NIPAP](https://spritelink.github.io/NIPAP/) instance with a custom frontend:
[config.berlin.freifunk.net](https://config.berlin.freifunk.net/)

## CLI User Guide

_Hint: Always manage your own IP addresses through config.berlin.freifunk.net_

**Q: How to lookup a IP from location `foo`?**

**A:**  `nipap address list foo` or short form `nipap a l foo`

**Q: How to lookup more Infos about a IP range?**

**A:**  `nipap address list 10.31.0.1/32` or short form `nipap a l 10.31.0.1/32`

**Q: How to manually modify attributes?**

**A:**  Be careful. You might brake things in the automated pipelines.
        You can use `nipap address modify 10.31.0.1/32 set foo bar`.
        Values for foobar can be looked up by using
        `nipap address view 10.31.0.1/32` on a valid entry.

**Q: Where can I find more CLI commands?**

**A:**  In the [official documentation](https://spritelink.gitbooks.io/nipap-user-guide/).

## Development

### How to install nipap for development

The following is mostly outdated. Just follow
https://spritelink.github.io/NIPAP/docs/INSTALL.html
and use the prebuilt packages.


### How to run nipap-wizard for development

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

