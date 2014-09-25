Freifunk Berlin IPAM
====================

Our ip address management system is basically a running NIPAP instance with two
frontends:

* nipap-www for advanced users (typically backbone maintainers) 
* nipap-wizard for others

How to install nipap for development
------------------------------------

Packages needed: postgresql, virtualenv2

Get source and patch it:

```
$ git clone https://github.com/SpriteLink/NIPAP
$ cd NIPAP
$ virtualenv2 env
$ . env/bin/activate
$ cd nipap
$ pip install -r requirements.txt
$ cd ..
$ git checkout v0.26.4
$ patch -p1 < patches/0001-Do-not-install-files-globally-no-root-privileges-nee.patch
$ patch -p1 < patches/0002-Fix-Makefile-tables-seems-to-be-in-the-wrong-order.patch
$ bash utilities/install-ip4r.sh
```

Install nipap:

```
$ cd nipap
$ python setup install
$ cp nipap.conf.dist nipap.conf
$ vim nipap.conf
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
