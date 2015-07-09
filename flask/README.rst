===============================
UA Server
===============================

This is the front-facing user advocacy server


Quickstart
----------

First, set your app's secret key as an environment variable. For example, example add the following to ``.bashrc`` or ``.bash_profile``.

.. code-block:: bash

    export USERADVOCACY_SECRET = 'something-really-secret'

Then set some other environment variables.

.. code-block:: bash

    export UPLOAD_PATH=''
    export SQLALCHEMY_DATABASE_URI='mysql://ua:test@localhost/useradvocacy'



Then run the following commands to bootstrap your environment.


::

    git clone https://github.com/mozilla/user-advocacy
    cd user-advocacy/flask
    . bin/activate
    pip install -r requirements/dev.txt
    bower install


Database
--------

Install MySQL.

run ```mysql -uroot`` and enter the following.

::

    CREATE USER 'ua'@'localhost' IDENTIFIED BY 'test';
    CREATE DATABASE telemetry CHARACTER SET utf8;
    GRANT ALL ON telemetry.* TO 'ua'@'localhost' IDENTIFIED BY 'test';
    CREATE DATABASE sentiment CHARACTER SET utf8;
    GRANT ALL ON sentiment.* TO 'ua'@'localhost' IDENTIFIED BY 'test';


Exit with ``^D`` and then load the data.

 ::

    mysql -u ua -p telemetry < test_data/telemetry.sql
    mysql -u ua -p sentiment < test_data/sentiment.sql

Finally, to bootstrap the database and run the server, type the following.

::

    python manage.py db init
    python manage.py db migrate
    python manage.py db upgrade
    python manage.py server


Deployment
----------

In your production environment, make sure the ``USERADVOCACY_ENV`` environment variable is set to ``"prod"``.


Shell
-----

To open the interactive shell, run ::

    python manage.py shell

By default, you will have access to ``app``, ``db``, and the ``User`` model.


Running Tests
-------------

To run all tests, run ::

    python manage.py test


Migrations
----------

Whenever a database migration needs to be made. Run the following commmands:
::

    python manage.py db migrate

This will generate a new migration script. Then run:
::

    python manage.py db upgrade

To apply the migration.

For a full migration command reference, run ``python manage.py db --help``.
