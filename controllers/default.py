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
        user = db(db.auth_user.id == auth.user.id).select().first()  # get up-to-date auth data
        if user.cached_until == None or datetime.utcnow() > user.cached_until:
            user, wallet = eveuser.get_info(db, auth)
        else:
            wallet = db(db.wallet.user_id == auth.user.id).select()
        user.birthday = user.birthday.strftime("%b %d, %Y at %H:%M:%S GMT")
        summary = evesum.do_summary(wallet)
    else:
        user, wallet, summary = None, None, None

    return dict(message=T('Welcome to the EVE Transaction Analyzer'), user=user, wallet=wallet, summary=summary)

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


