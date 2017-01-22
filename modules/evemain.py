from datetime import datetime
import pytz
import eveuser
from gluon.html import *

def main(auth, db, args, response):
    if auth.is_logged_in():
        char_row = db(db.auth_user.id == auth.user.id).select().first()  # get up-to-date auth data

        if char_row.cached_until == None or datetime.utcnow() > char_row.cached_until:
            eveuser.update_tables(db, char_row, auth.settings.login_form.accessToken())
            char_row = db(db.auth_user.id == auth.user.id).select().first()  # reload data (cached_until changed)

        summary = analyze(db, auth.user.id, args)
        character = Character(char_row).xml()
    else:
        character, summary = None, None

    return dict(character=character, summary=summary)

class Character(object):
    def __init__(self, character):
        self.character = character
        # Convert cached_until and birthday in UTC to ET for display...
        eastern = pytz.timezone('US/Eastern')
        self.cached_until = character.cached_until.replace(tzinfo=pytz.utc).astimezone(eastern).strftime("%H:%M:%S %Z")
        self.birthday = character.birthday.replace(tzinfo=pytz.utc).astimezone(eastern).strftime("%b %d, %Y at %H:%M:%S %Z")

    def xml(self):
        return DIV(TABLE(THEAD(TR(
            TD(IMG(_src=self.character.portrait, _alt="Character Portrait"), _class="char"),
            TD(self.character.first_name, " ", self.character.last_name, BR(),
               self.character.registration_id, BR(), self.character.race, " ", self.character.bloodline, " ",
               self.character.ancestry, BR(), "Born ", self.birthday, _class="char"),
            TD(IMG(_src=self.character.corp_logo, _alt="Corporate Logo"), _class="char"),
            TD("Member ", I(self.character.corp_name))))),
            P("Data refreshes at ", self.cached_until))

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
        row.append(CAT(TH("Currently Own"),
            TH("Quantity Bought"), TH("Total Paid"), TH("Average Cost"),
            TH("Quantity Sold"), TH("Total Received"), TH("Average Price")))
        head = THEAD(row)
        body = TBODY()
        for row in Summary.rows:
            if group:
                if row.group == group:
                    body.append(row.make_row(group))
            else:
                body.append(row.make_row())
        t = TABLE(head, body, _id="summaryTable", _class="tablesorter smry")
        if group:
            t = DIV(H3("Group by: ", group), t)
        else:
            t = DIV(H3("Current Assets and Summary of Transactions"), t)

        return t

    def make_row(self, group=None):
        row = TR()
        row.append(TD(self.name, _class="smry"))
        if not group:
            row.append(TD(self.group, _class="smry"))
        row.append(CAT(
            TD(format(self.quantity, ",d"), _class="smry num"),
            TD(format(self.bought, ",d") if self.bought > 0 else "-", _class="smry num"),
            TD(format(self.paid, ",.2f") if self.paid > 0.0 else "-", _class="smry num"),
            TD("-" if self.bought == 0 else format(self.paid / self.bought, ",.2f"), _class="smry num"),
            TD(format(self.sold, ",d") if self.sold > 0 else "-", _class="smry num"),
            TD(format(self.recv, ",.2f") if self.recv > 0.0 else "-", _class="smry num"),
            TD("-" if self.sold == 0 else format(self.recv / self.sold, ",.2f"), _class="smry num")))
        return row

def analyze(db, id, args):
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

    # Build a Summary entry per type_name in the Assets...
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
