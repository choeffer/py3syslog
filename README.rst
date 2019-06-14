py3syslog
=========

Python 3 implementation of a simple UDP syslog server which inserts the recieved 
messages into a MariaDB_ or MySQL_ database.

About
-----

The Python script will start a syslog server which inserts the recieved messages
into a MariaDB_ or MySQL_ database. 

Every time the script is executed it will check if the database and table exist 
and if not create them. Then the script is executed until it will be 
manually closed. Every time a message is recieved on the defined port the 
data will be decoded as UTF-8, inserted in the database and printed out in 
the terminal.

Be aware that the UDP packages are not encypted. It is taken care off avoiding 
SQL injections because the server might be facing the internet.

The script uses the python module socketserver_ and the external module
mysql-connector-python_ . See ``requirements.txt`` for installed packages and the 
used versions. The file is created with ``pip3 freeze > requirements.txt``.

Usage
-----

First install the required mysql-connector-python module in the global Python 3 
environment or in a virtual Python 3 environment. The latter has the advantage that 
the packages are isolated from other projects and also from the system wide 
installed global once. If things get messed up, the virtual environment can 
just be deleted and created from scratch again. For more informations about 
virtual environments in Python 3, see venv1_ and venv2_ .

.. code-block:: console

    pip3 install mysql-connector-python

Then modify the ``PORT``, ``db_name``, ``table_name``, ``db_user``, ``db_password``, 
``db_host`` and ``db_port`` parameters in the ``syslogserver.py`` script and 
execute it.

.. code-block:: console

    python3 syslogserver.py

Or use e.g. tmux_ to execute it in the background.

Systemd service
^^^^^^^^^^^^^^^

An example .service file is also included to show how to run the syslog server
as a systemd service at startup. For more informations, see `systemd.service`_ .
In the example .service file a virtual Python 3 environment is used to execute
the script. Also the script will be automatically restarted if it crashes to
ensure that the syslog server is always running. The local user name and the
path to the virtual Python 3 environment needs to be adjusted before it can be
used.

To activate the systemd service execute the following commands.

.. code-block:: console

    sudo cp syslogserver.service /etc/systemd/system/

    sudo systemctl daemon-reload

    sudo systemctl start syslogserver.service

    sudo systemctl enable syslogserver.service


Example Mikrotik RouterOS
-------------------------

The script was developed to recieve syslog messages from a MikroTik_ `wAP LTE kit`_ 
and insert them into a MariaDB_ database to be able to display them via Grafana_ . 

RouterOS
^^^^^^^^

The following settings are used in RouterOS. They need to be applied via CLI_ . 
Change ``remote`` and ``remote-port`` to the one where the syslog server is 
listening.

.. code-block:: console

    /system logging action>
    set 3 remote=123.123.123.123 remote-port=12312

Next command just prints out the settings of ``/system logging action`` .

.. code-block:: console

    /system logging action> print
    Flags: * - default 
    0 * name="memory" target=memory memory-lines=1000 memory-stop-on-full=no 

    1 * name="disk" target=disk disk-file-name="flash/log" 
        disk-lines-per-file=1000 disk-file-count=2 disk-stop-on-full=no 

    2 * name="echo" target=echo remember=yes 

    3 * name="remote" target=remote remote=123.123.123.123 remote-port=12312 
        src-address=0.0.0.0 bsd-syslog=no syslog-time-format=bsd-syslog 
        syslog-facility=daemon syslog-severity=auto 

It is also needed to add the remote syslog server as a destination for logs 
on the wanted topics. The ``prefix=`` option is optional but useful to distinguish 
between different devices as it is added in the logs which are sent to the remote 
syslog server.

.. code-block:: console

    /system logging>
    add action=remote prefix=example_prefix topics=info
    add action=remote prefix=example_prefix topics=error
    add action=remote prefix=example_prefix topics=warning
    add action=remote prefix=example_prefix topics=critical

Grafana
^^^^^^^

Grafana_ is used to display the syslog messages. 
In Grafana_ the database has to be added as a datasource_ . Then a table_ 
with following SQL query in the Metrics tab can be added to a dashboard. The 
SQL query has to be adjusted to the used database/table/columns structure, see 
script ``syslogserver.py`` for more details how the database/table/columns are 
created. The ``AND message LIKE '%example_prefix%'`` part of the SQL query is 
used to display only a certain device based on the above used ``prefix=`` 
option.

.. code-block:: sql

    SELECT
    inserted_utc,
    message
    FROM logging.logs
    WHERE $__timeFilter(inserted_utc) AND message LIKE '%example_prefix%'
    ORDER BY inserted_utc DESC

Credits
-------

https://gist.github.com/marcelom/4218010 

References
----------

.. target-notes::

.. _MariaDB: https://mariadb.org/
.. _MySQL: https://www.mysql.com/
.. _socketserver: https://docs.python.org/3/library/socketserver.html
.. _mysql-connector-python: https://pypi.org/project/mysql-connector-python/
.. _venv1: https://docs.python.org/3/tutorial/venv.html
.. _venv2: https://docs.python.org/3/library/venv.html
.. _tmux: https://en.wikipedia.org/wiki/Tmux
.. _`systemd.service`: https://www.raspberrypi.org/documentation/linux/usage/systemd.md
.. _Mikrotik: https://mikrotik.com/
.. _`wAP LTE kit`: https://mikrotik.com/product/wap_lte_kit
.. _CLI: https://wiki.mikrotik.com/wiki/Manual:First_time_startup#CLI
.. _Grafana: https://grafana.com/
.. _datasource: http://docs.grafana.org/features/datasources/mysql/
.. _table: http://docs.grafana.org/features/panels/table_panel/
