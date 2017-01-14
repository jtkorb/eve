from bravado.client import SwaggerClient

def get_info(token, character_id):
    '''
    Get some EVE Online character information (currently public character data and
    private wallet contents.
    '''
    if not token:
        return None

    client = SwaggerClient.from_url('https://esi.tech.ccp.is/latest/swagger.json')

    # Getting public character data does not require a token; getting the wallet does...
    character = client.Character.get_characters_character_id(character_id=character_id).result()
    wallet = client.Wallet.get_characters_character_id_wallets(character_id=character_id,
        _request_options={"headers" : { "Authorization" : "Bearer " + token}}).result()

    return character, wallet