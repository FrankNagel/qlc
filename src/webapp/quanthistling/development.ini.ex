#
# quanthistling - Pylons development environment configuration
#
# The %(here)s variable will be replaced with the parent directory of this file
#
[DEFAULT]
debug = true
# Uncomment and replace with the address which should receive any error reports
#email_to = pbouda@cidles.eu
smtp_server = cidles.eu
error_email_from = paste@localhost

mail.on = true
mail.manager = immediate
mail.transport = smtp
mail.provider = smtp
mail.message.encoding = utf-8
mail.utf8qp.on = true

mail.smtp.server = cidles.eu
mail.smtp.username = pbouda
mail.smtp.password = password
mail.smtp.tls=false
mail.smtp.debug=true

[server:main]
use = egg:Paste#http
host = 127.0.0.1
port = 5000

[app:main]
use = egg:quanthistling
full_stack = true
static_files = true

cache_dir = %(here)s/data
beaker.session.key = quanthistling
beaker.session.secret = somesecret

# If you'd like to fine-tune the individual locations of the cache data dirs
# for the Cache data, or the Session saves, un-comment the desired settings
# here:
#beaker.cache.data_dir = %(here)s/data/cache
#beaker.session.data_dir = %(here)s/data/sessions

# SQLAlchemy database URL
sqlalchemy.url = postgresql://postgres:password@localhost/quanthistling
#sqlalchemy.url = postgresql+pg8000://postgres:password@localhost/quanthistling
#sqlalchemy.url = sqlite:///d:/development.db

# WARNING: *THE LINE BELOW MUST BE UNCOMMENTED ON A PRODUCTION ENVIRONMENT*
# Debug mode will enable the interactive debugging tool, allowing ANYONE to
# execute malicious code after an exception is raised.
#set debug = false

# Logging configuration
[loggers]
keys = root, routes, quanthistling, sqlalchemy

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = INFO
handlers = console

[logger_routes]
level = INFO
handlers =
qualname = routes.middleware
# "level = DEBUG" logs the route matched and routing variables.

[logger_quanthistling]
level = DEBUG
handlers =
qualname = quanthistling

[logger_sqlalchemy]
level = INFO
handlers =
qualname = sqlalchemy.engine
# "level = INFO" logs SQL queries.
# "level = DEBUG" logs SQL queries and results.
# "level = WARN" logs neither.  (Recommended for production systems.)

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(asctime)s,%(msecs)03d %(levelname)-5.5s [%(name)s] [%(threadName)s] %(message)s
datefmt = %H:%M:%S
