from datetime import datetime
import pytz
import eveuser
from gluon.html import *

def main(auth, db, args):
    if auth.is_logged_in():
        char_row = db(db.auth_user.id == auth.user.id).select().first()  # get up-to-date auth data

        if char_row.cached_until == None or datetime.utcnow() > char_row.cached_until:
            eveuser.update_tables(db, char_row, auth.settings.login_form.accessToken())
            char_row = db(db.auth_user.id == auth.user.id).select().first()  # reload data (cached_until changed)

        summary = create_summary(db, auth.user.id, args)
        character = format_character(char_row)
    else:
        character, summary = None, None

    return dict(character=character, summary=summary)

def format_character(char_row):
    # Convert cached_until and birthday in UTC to ET for display...
    eastern = pytz.timezone('US/Eastern')
    cached_until = char_row.cached_until.replace(tzinfo=pytz.utc).astimezone(eastern).strftime("%H:%M:%S %Z")
    birthday = char_row.birthday.replace(tzinfo=pytz.utc).astimezone(eastern).strftime("%b %d, %Y at %H:%M:%S %Z")

    return DIV(
        TABLE(THEAD(TR(
            TD(IMG(_src=char_row.portrait, _alt="Character Portrait"), _style="padding: 0px 15px 5px 0px;"),
            TD(char_row.first_name, " ", char_row.last_name, BR(),
                char_row.registration_id, BR(), char_row.race, " ", char_row.bloodline, " ",
                char_row.ancestry, BR(), "Born ", birthday, _style="padding: 0px 15px 5px 0px;"),
            TD(IMG(_src=char_row.corp_logo, _alt="Corporate Logo"), _style="padding: 0px 15px 5px 0px;"),
            TD("Member ", I(char_row.corp_name))))),
        P("Data refreshes at ", cached_until))

class Summary(object):
    rows = []

    def __init__(self, name, group_name, quantity=0):
        self.name = name
        self.group = group_name
        self.quantity = quantity
        self.bought = 0
        self.sold = 0
        self.paid = 0
        self.recv = 0
        Summary.rows.append(self)

    @classmethod
    def make_table(cls, args):
        group = args[0] if len(args) == 1 else None
        row = TR()
        row.append(TH("Name"))
        if not group:
            row.append(TH("Group"))
        row.append(CAT(TH("Currently Own", _class="num"),
            TH("Quantity Bought", _class="num"), TH("Total Paid", _class="num"), TH("Average Cost", _class="num"),
            TH("Quantity Sold", _class="num"), TH("Total Received", _class="num"), TH("Average Price", _class="num")))
        head = THEAD(row)
        body = TBODY()
        for row in Summary.rows:
            if group:
                if row.group == group:
                    body.append(row.make_row(group))
            else:
                body.append(row.make_row())
        t = TABLE(head, body, _id="summaryTable", _class="display compact cell-border", _cell_spacing="0")
        if group:
            t = DIV(H3("Group by: ", group), t)
        else:
            t = DIV(H3("Current Assets and Summary of Transactions"), t)

        return t

    def make_row(self, group=None):
        row = TR()
        row.append(TD(self.name))
        if not group:
            row.append(TD(self.group))
        row.append(CAT(
            TD(format(self.quantity, ",d")),
            TD(format(self.bought, ",d") if self.bought > 0 else "-"),
            TD(format(self.paid, ",.2f") if self.paid > 0.0 else "-"),
            TD("-" if self.bought == 0 else format(self.paid / self.bought, ",.2f")),
            TD(format(self.sold, ",d") if self.sold > 0 else "-"),
            TD(format(self.recv, ",.2f") if self.recv > 0.0 else "-"),
            TD("-" if self.sold == 0 else format(self.recv / self.sold, ",.2f"))))
        return row

def create_summary(db, id, args):
    '''For each 'type_name', accumulate data from transactions.'''

    transactions = db((db.wallet.user_id == id) &
                      (db.wallet.type_id == db.types.type_id) &
                      (db.types.group_id == db.groups.group_id)).select()

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

    # Initialize tables to empty...
    Summary.rows = []
    by_type_name = {}
    by_type_id = {}

    # Build a Summary entry per type_name in the Wallet...
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

    # Add Asset quantities to Summary objects (adding new Summary objects as necessary)...
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

    return Summary.make_table(args)
