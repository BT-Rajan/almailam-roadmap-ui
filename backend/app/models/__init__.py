# Importing any single model (e.g. `from app.models.user import User`) only
# registers that module's tables with SQLAlchemy's shared metadata -- it does
# NOT pull in the other model modules. That's fine when the full app has
# already been imported (app.main imports every router, which imports every
# model), but it breaks any script that imports just one model directly
# (e.g. scripts/create_admin.py importing only app.models.user): SQLAlchemy
# then can't resolve foreign keys pointing at tables it never saw, e.g.
#
#   sqlalchemy.exc.NoReferencedTableError: Foreign key associated with
#   column 'users.client_id' could not find table 'clients' ...
#
# Importing this package (which happens automatically for every
# `app.models.<something>` import, since Python runs a package's
# __init__.py before its submodules) now imports every model module up
# front, so the metadata is always complete regardless of which single
# model a caller asked for.

from app.models import (  # noqa: F401
    ai_config,
    client,
    company,
    contract,
    document,
    document_template,
    government,
    knowledge,
    message,
    notification,
    payment,
    permit_catalog,
    project,
    quotation,
    refresh_token,
    role,
    service_catalog,
    status_report,
    task,
    timeline,
    type_activity_catalog,
    user,
)
