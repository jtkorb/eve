from bravado.client import SwaggerClient
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

USER_AGENT = "EVE Transaction Analyzer 0.1, Tim Korb <jtkorb@bikmort.com>"
SWAGGER_URL = "https://esi.tech.ccp.is/latest/swagger.json"
CREST_ROOT_URL = "https://crest-tq.eveonline.com/"
CHARACTER_INFO_URL = "https://api.eveonline.com/eve/CharacterInfo.xml.aspx?characterID=%s"
WALLET_TRANSACTIONS_URL = "https://api.eveonline.com/char/WalletTransactions.xml.aspx?" + \
                          "characterID=%s&accessType=character&accessToken=%s"

DT_FORMAT = '%Y-%m-%d %H:%M:%S'

def extractURL(r, name):
    return r.json()[name]["href"]

def set_swagger_data(user, token, character_id):
    client = SwaggerClient.from_url(SWAGGER_URL)
    r = client.Character.get_characters_character_id(character_id=character_id).result()
    user.gender = r['gender']
    user.security_status = r['security_status']
    user.birthday = r['birthday']
    user.description = r['description']
    user.update_record()

    # wallet = client.Wallet.get_characters_character_id_wallets(character_id=character_id,
    #     _request_options={"headers" : { "Authorization" : "Bearer " + token}}).result()

    return

def set_crest_data(user, token, character_id):

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

def set_xmlapi_data(db, user, token, character_id):
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
        d['type_id'] = int(row.attrib['typeID'])
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
    return

def get_info(db, auth):
    '''
    Get some EVE Online character information (currently public character data and
    private wallet contents.
    '''
    token = auth.settings.login_form.accessToken()
    character_id = auth.user.registration_id

    if not token:
        return None

    user = db(db.auth_user.registration_id == character_id).select().first()

    set_swagger_data(user, token, character_id)
    set_crest_data(user, token, character_id)
    set_xmlapi_data(db, user, token, character_id)

    wallet = db(db.wallet.user_id == user.id).select()

    return user, wallet
