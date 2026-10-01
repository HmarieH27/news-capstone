# Run the application

Use Python 3.11 or newer. From this folder:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export DJANGO_DEBUG=1
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/. Run `python manage.py test` for automated tests.
Local development uses SQLite and prints email to the console. No email is sent
unless you configure an SMTP backend. Databases and environments are excluded
from submissions. `SQLITE_PATH` can point to a disposable database for testing.

For deployment, set `DJANGO_SECRET_KEY` to your own randomly generated key,
`DJANGO_DEBUG=0`, and `DJANGO_ALLOWED_HOSTS` to your actual host names. Configure
`EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST`,
`EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` and
`DEFAULT_FROM_EMAIL` for invoice, reset and subscription mail. Keep credentials
outside source control. Password reset links expire after one hour and after use.

## MariaDB

Install MariaDB and the mysqlclient build prerequisites (on Debian:
`default-libmysqlclient-dev build-essential pkg-config`). Create a UTF-8 database
and a dedicated database user. Install `pip install -r requirements-mariadb.txt`.
Set `DB_ENGINE=mariadb`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` and
`DB_PORT`, then run `python manage.py migrate` and `python manage.py test`.
The test user needs permission to create and drop the isolated test database.
Do not use a production database for tests.

To transfer existing SQLite data, back it up, export with
`python manage.py dumpdata --natural-foreign --natural-primary --exclude contenttypes --exclude auth.permission > data.json`
before changing the database settings; migrate MariaDB and then run
`python manage.py loaddata data.json`. Keep the export private and compare row
counts and login/content workflows before switching traffic. Configuration alone
is not evidence that a MariaDB migration has been performed.

## News workflows

Register as a reader or journalist. An administrator assigns trusted editors through
`/admin/` and adds editors/journalists to publishers. Readers manage subscriptions
on the home page. Journalists create drafts; editors review and approve drafts in
the editorial workspace. The approved article is emailed to subscribers and POSTed
using `requests` to `/api/approved/`. Set `APPROVED_API_URL` to this application's
trusted internal URL; it receives an editor token, so never point it at a third party.
Use the threaded development server, or multiple production workers, for this
loopback request. Failed delivery remains retryable via the approval button.
Individual emails keep recipient addresses private. Delivery is at-least-once:
a crash after sending an email but before recording success may repeat that mail.

Get a token at `POST /api/token/` with username and password, then send
`Authorization: Token <your-token>`. Article list/detail, subscribed, create,
PUT/PATCH, DELETE and editor approval endpoints live under `/api/articles/`.
The list endpoint returns all approved articles as required by the PDF; only the
`subscribed/` endpoint filters to a reader's subscriptions. Newsletters and
publishers are available at `/api/newsletters/` and `/api/publishers/`.
Authors are assigned by the server. Editing an article clears approval.
Role-inapplicable many-to-many subscriptions are empty, not SQL NULL (Django
many-to-many fields cannot store None); independent authored content is represented
by reverse relations with a null publisher. Reader accounts cannot author content.

## Docker demonstration

```sh
docker build -t news-capstone .
docker run --rm -p 127.0.0.1:8000:8000 -e DJANGO_DEBUG=1 -v news-data:/data news-capstone
```

This coursework container runs Django's development server for a local demonstration.
Use `docker exec -it <container> python manage.py createsuperuser` to create an
administrator. The named volume retains SQLite data. For public deployment use
production WSGI workers, HTTPS, static-file hosting and private runtime secrets.
The internal approval URL defaults to this container's threaded server.

## Documentation and required Git history

Install `pip install Sphinx==8.2.3`, then `DJANGO_DEBUG=1 make -C docs html`.
Built HTML is included at `docs/_build/html/index.html`. The Level 3 publishing
script's explicit `capstone` mode creates the initial code commit, a `docs` branch
with one commit per documented module, a `container` branch, both merge commits,
and a final README commit in a disposable clone. It publishes only when executed.
The older sibling task_manager project is retained for review but is not this
assignment's final-capstone submission.
