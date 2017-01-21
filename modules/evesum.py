class Summary(object):
    def __init__(self, name, group_name, quantity=0):
        self.name = name
        self.group = group_name
        self.quantity = quantity
        self.bought = 0
        self.sold = 0
        self.paid = 0
        self.recv = 0

    def representation(self):
        return [
            self.name, self.group, format(self.quantity, ",d"),
            format(self.bought, ",d") if self.bought > 0 else "-",
            format(self.paid, ",.2f") if self.paid > 0.0 else "-",
            "-" if self.bought == 0 else format(self.paid / self.bought, ",.2f"),
            format(self.sold, ",d") if self.sold > 0 else "-",
            format(self.recv, ",.2f") if self.recv > 0.0 else "-",
            "-" if self.sold == 0 else format(self.recv / self.sold, ",.2f")
        ]

def analyze(db, id):
    '''For each 'type_name', accumulate data from transactions.'''

    # Each transaction looks like this:
    # < Row
    # {'wallet': {'user_id': 1L, 'type_id': 10246L, 'price': 15000.0, 'type_name': 'Mining Drone I',
    #             'client_type_id': '1383', 'transaction_type': 'buy',
    #             'transaction_date_time': datetime.datetime(2016, 12, 23, 0, 26, 21),
    #             'journal_transaction_id': '13447505687', 'client_id': '96838043', 'id': 442L,
    #             'station_name': 'Jouvulen III - Science and Trade Institute School', 'transaction_for': 'personal',
    #             'client_name': 'Pax Mendol', 'transaction_id': '4484368141', 'quantity': 1L},
    #  'groups': {'group_id': 101L, 'id': 96L, 'name': 'Mining Drone'},
    #  'types': {'name': 'Mining Drone I', 'type_id': 10246L, 'icon_id': None, 'volume': 5.0, 'group_id': 101L,
    #            'id': 226L, 'description': 'Mining Drone'}} >

    transactions = db((db.wallet.user_id == id) &
                      (db.wallet.type_id == db.types.type_id) &
                      (db.types.group_id == db.groups.group_id)).select()

    by_type_name = {}
    by_type_id = {}
    for row in transactions:
        if row.wallet.type_name not in by_type_name:
            by_type_name[row.wallet.type_name] = Summary(row.wallet.type_name, row.groups.name)
            by_type_id[row.wallet.type_id] = by_type_name[row.wallet.type_name]
        item = by_type_name[row.wallet.type_name]
        if row.wallet.transaction_type == "sell":
            item.sold += row.wallet.quantity
            item.recv += row.wallet.quantity * row.wallet.price
        else:
            item.bought += row.wallet.quantity
            item.paid += row.wallet.quantity * row.wallet.price

    r = db(db.assets.user_id == id).select(db.assets.type_id, db.assets.quantity.sum(), groupby=db.assets.type_id)
    for row in r:
        type_id = row.assets.type_id
        quantity = row._extra['SUM("assets"."quantity")'] or 1
        if type_id in by_type_id:
            by_type_id[type_id].quantity += quantity
        else:
            t = db(db.types.type_id == type_id).select().first()
            g = db(db.groups.group_id == t.group_id).select().first() if t else None
            if g:
                by_type_id[type_id] = by_type_name[t.name] = Summary(t.name, g.name, quantity=quantity)
            else:
                print "types or group entry missing for type_id %d)" % type_id
                type_name = "(missing entry for type_id = %d)" % type_id
                by_type_id[type_id] = by_type_name[type_name] = Summary(type_name, "---unknown---", quantity=quantity)

    summary = []
    for key in sorted(by_type_name.iterkeys()):
        summary.append(by_type_name[key].representation())
    return summary, transactions
