# -------------------------------------------------------------------------
# Define your tables below (or better in another model file) for example
#
# >>> db.define_table('mytable', Field('myfield', 'string'))
#
# Fields can be 'string','text','password','integer','double','boolean'
#       'date','time','datetime','blob','upload', 'reference TABLENAME'
# There is an implicit 'id integer autoincrement' field
# Consult manual for more options, validators, etc.
#
# More API examples for controllers:
#
# >>> db.mytable.insert(myfield='value')
# >>> rows = db(db.mytable.myfield == 'value').select(db.mytable.ALL)
# >>> for row in rows: print row.id, row.myfield
# -------------------------------------------------------------------------

db.define_table('wallet',
                Field('user_id', 'reference auth_user'),
                Field('type_id', 'integer'),
                Field('client_type_id'),
                Field('transaction_for'),
                Field('price', 'float'),
                Field('client_id'),
                Field('journal_transaction_id'),
                Field('type_name'),
                Field('station_name'),
                Field('transaction_id'),
                Field('quantity', 'integer'),
                Field('transaction_date_time', 'datetime'),
                Field('client_name'),
                Field('transaction_type'))
