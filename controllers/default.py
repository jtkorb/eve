# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

# -------------------------------------------------------------------------
# This is a sample controller
# - index is the default action of any application
# - user is required for authentication and authorization
# - download is for downloading files uploaded in the db (does streaming)
# -------------------------------------------------------------------------

from datetime import datetime
import eveuser
import evesum

def index():
    """
    Landing page for EVE Online users.
    """
    if auth.is_logged_in():
        character = db(db.auth_user.id == auth.user.id).select().first()  # get up-to-date auth data

        if character.cached_until == None or datetime.utcnow() > character.cached_until:
            eveuser.update_tables(db, character, auth.settings.login_form.accessToken())
            character = db(db.auth_user.id == auth.user.id).select().first()  # reload data (cached_until changed)

        delta = datetime.now() - datetime.utcnow()  # for ad hoc timezone conversions
        cached_until = (character.cached_until+delta).strftime("%H:%M:%S")
        birthday = (character.birthday+delta).strftime("%b %d, %Y at %H:%M:%S")
        summary, transactions = evesum.analyze(db, auth.user.id)
    else:
        character, summary, transactions, birthday, cached_until = None, None, None, None, None

    return dict(character=character, summary=summary, transactions=transactions, birthday=birthday, cached_until=cached_until)

@auth.requires_login()
def raw():
    user = db(db.auth_user.id == auth.user.id).select().first()  # get up-to-date auth data
    dbw = db.wallet
    wallet = SQLFORM.grid(dbw.user_id == auth.user.id, deletable=False, editable=False, create=False,
                          fields=[dbw.transaction_date_time,
                                  dbw.transaction_type, dbw.type_id, dbw.type_name,
                                  dbw.station_name, dbw.quantity, dbw.price])
    return dict(user=user, wallet=wallet)

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


