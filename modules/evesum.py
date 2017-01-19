class Summary(object):
    def __init__(self, name):
        self.name = name
        self.bought = 0
        self.sold = 0
        self.paid = 0
        self.recv = 0

    def representation(self):
        return [
            self.name,
            format(self.bought, ",d") if self.bought > 0 else "-",
            format(self.paid, ",.2f") if self.paid > 0.0 else "-",
            "-" if self.bought == 0 else format(self.paid / self.bought, ",.2f"),
            format(self.sold, ",d") if self.sold > 0 else "-",
            format(self.recv, ",.2f") if self.recv > 0.0 else "-",
            "-" if self.sold == 0 else format(self.recv / self.sold, ",.2f")
        ]

def do_summary(wallet):
    '''For each 'type_name', accumulate data from transactions.'''
    summary = {}
    for row in wallet:
        if row['type_name'] not in summary:
            summary[row['type_name']] = Summary(row['type_name'])
        item = summary[row['type_name']]
        if row['transaction_type'] == "sell":
            item.sold += row['quantity']
            item.recv += row['quantity'] * row['price']
        else:
            item.bought += row['quantity']
            item.paid += row['quantity'] * row['price']

    a = []
    for key in sorted(summary.iterkeys()):
        s = summary[key]
        a.append(s.representation())
    return a