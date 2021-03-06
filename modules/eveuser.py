from bravado.client import SwaggerClient
import requests
import xml.etree.ElementTree as ET

USER_AGENT = "EVE Transaction Analyzer 0.1, Tim Korb <jtkorb@bikmort.com>"
SWAGGER_URL = "https://esi.tech.ccp.is/latest/swagger.json"
CREST_ROOT_URL = "https://crest-tq.eveonline.com/"
CHARACTER_INFO_URL = "https://api.eveonline.com/eve/CharacterInfo.xml.aspx?characterID=%s"
WALLET_TRANSACTIONS_URL = "https://api.eveonline.com/char/WalletTransactions.xml.aspx?" + \
                          "characterID=%s&accessType=character&accessToken=%s"

DT_FORMAT = '%Y-%m-%d %H:%M:%S'

def extractURL(r, name):
    return r.json()[name]["href"]

def update_swagger_data(esi, db, user, token, character_id):
    r = esi.Character.get_characters_character_id(character_id=character_id).result()
    user.gender = r['gender']
    user.security_status = r['security_status']
    user.birthday = r['birthday']
    user.description = r['description']
    user.update_record()

    r = esi.Assets.get_characters_character_id_assets(
        character_id=character_id,
        _request_options={"headers" : { "Authorization" : "Bearer " + token}}).result()
    db(db.assets.user_id == user.id).delete()
    for item in r:
        d = {}
        d['user_id'] = user.id
        d['type_id'] = type_id = item['type_id']
        d['item_id'] = item['item_id']
        d['is_singleton'] = item['is_singleton']
        d['location_flag'] = item['location_flag']
        d['location_id'] = item['location_id']
        d['location_type'] = item['location_type']
        d['quantity'] = max(1, item['quantity'])  # None or < 0 indicates a singleton item, but still 1
        db.assets.insert(**d)
        check_update_type_group_ids(esi, db, type_id)
    return

def update_crest_data(user, token, character_id):
    # TODO Pull this from the esi data instead

    # Walk down the tree to find the character information...
    r = requests.get(CREST_ROOT_URL)
    decodeURL = extractURL(r, "decode")
    r = requests.get(decodeURL, headers={'User-Agent': USER_AGENT, "Authorization" : "Bearer " + token})
    characterURL = extractURL(r, "character")
    r = requests.get(characterURL, headers={'User-Agent': USER_AGENT, "Authorization" : "Bearer " + token})
    d = r.json()

    # Extract and record the data...
    user.corp_name = d['corporation']['name']
    user.corp_logo = d['corporation']['logo']['64x64']['href']
    user.portrait = d['portrait']['128x128']['href']
    user.ship = d['ship']['href']
    user.loc = d['location']['href']
    user.update_record()

    # marketPricesURL = extractURL(r, "marketPrices")  # for future use
    return

def check_update_type_group_ids(esi, db, type_id):
    t = db(db.types.type_id == type_id).select().first()
    if t:
        group_id = t['group_id']
    else:
        r = esi.Universe.get_universe_types_type_id(type_id=type_id).result()
        db.types.insert(type_id=type_id, name=r['name'], description=r['description'], group_id=r['group_id'], icon_id=r['icon_id'], volume=r['volume'])
        group_id = r['group_id']

    g = db(db.groups.group_id == group_id).select().first()
    if g:
        group_name = g['name']
    else:
        r = esi.Universe.get_universe_groups_group_id(group_id=group_id).result()
        db.groups.insert(group_id=group_id, name=r['name'])
        group_name = r['name']
    return group_name

def update_xmlapi_data(esi, db, user, token, character_id):
    r = requests.get(CHARACTER_INFO_URL % character_id)
    root = ET.fromstring(r.text)

    user.race = root.find('./result/race').text
    user.bloodline = root.find('./result/bloodline').text
    user.ancestry = root.find('./result/ancestry').text
    user.cached_until = root.find('./cachedUntil').text
    user.update_record()

    # Get wallet transactions...
    r = requests.get(WALLET_TRANSACTIONS_URL % (character_id, token), headers={'User-Agent': USER_AGENT})
    root = ET.fromstring(r.text)

    for row in root.findall("./result/rowset/row"):
        d = {}
        d['user_id'] = user.id
        d['type_id'] = type_id = int(row.attrib['typeID'])
        d['client_type_id'] = row.attrib['clientTypeID']
        d['transaction_for'] = row.attrib['transactionFor']
        d['price'] = float(row.attrib['price'])
        d['client_id'] = row.attrib['clientID']
        d['journal_transaction_id'] = row.attrib['journalTransactionID']
        d['type_name'] = row.attrib['typeName']
        d['station_name'] = row.attrib['stationName']
        d['transaction_id'] = row.attrib['transactionID']
        d['quantity'] = int(row.attrib['quantity'])
        d['transaction_date_time'] = row.attrib['transactionDateTime']
        d['client_name'] = row.attrib['clientName']
        d['transaction_type'] = row.attrib['transactionType']
        db.wallet.update_or_insert(db.wallet.transaction_id == d['transaction_id'], **d)
        check_update_type_group_ids(esi, db, type_id)
    return

def update_tables(db, character, token):
    '''
    Get some EVE Online character information (currently public character data and
    private wallet contents).  Must have been authenticated to EVE Online.
    '''
    esi = SwaggerClient.from_url(SWAGGER_URL)

    character_id = character.registration_id
    update_swagger_data(esi, db, character, token, character_id)
    update_crest_data(character, token, character_id)
    update_xmlapi_data(esi, db, character, token, character_id)
    return
