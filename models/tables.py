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

# From https://esi.tech.ccp.is/latest/#!/Assets/get_characters_character_id_assets...
#
# {
#   "application/json": [
#     {
#       "is_singleton": true,
#       "item_id": 1000000016835,
#       "location_flag": "Hangar",
#       "location_id": 60002959,
#       "location_type": "station",
#       "type_id": 3516
#     }
#   ]
# }

db.define_table('assets',
                Field('user_id', 'reference auth_user'),
                Field('type_id', 'integer'),    # TODO Change to "reference types"?
                Field('item_id', 'integer'),
                Field('is_singleton', 'boolean'),
                Field('location_flag'),
                Field('location_id', 'integer'),
                Field('location_type'),
                Field('quantity', 'integer'))

db.define_table('types',
                Field('type_id', 'integer'),
                Field('name'),
                Field('description'),
                Field('group_id', 'integer'),  # TODO Change to "reference groups"?
                Field('icon_id', 'integer'),
                Field('volume', 'float'))

db.define_table('groups',
                Field('group_id', 'integer'),
                Field('name'))