import urllib.request
import urllib.parse
import datetime
import hashlib
import hmac
import json

""" Simple function to send/receive message with Lex
    message: a string of message you want to send to Lex
    bot_credentials: a dictionary of the following items:
    {
        access-key: <your-access-key, given by AWS>
        secret-key: <your-secret-key, given by AWS>
        user-id: <a random string representing a user chatting with Lex>
        bot-name: <your bot name, set in AWS>
        bot-alias: <your bot alias, set in AWS>
        region: <the region your Lex service is hosted, e.g. us-east-1>
    }
    returns:
        (success, message) tuple
        success = True on success, False otherwise
        message = Lex's reply, or the error message
    
"""
def ask_lex(message, bot_credentials):
    aws_access_key = bot_credentials['access-key']
    aws_secret_key = bot_credentials['secret-key']
    user_id = bot_credentials['user-id']
    bot_name = bot_credentials['bot-name']
    bot_alias = bot_credentials['bot-alias']
    region = bot_credentials['region']
    host = 'runtime.lex.{}.amazonaws.com'.format(region)

    payload = json.dumps({'inputText': message}).encode('utf-8')
    hashed_payload = hashlib.sha256(payload).hexdigest()

    req_time = datetime.datetime.utcnow()
    amz_time = req_time.strftime('%Y%m%dT%H%M%SZ')
    short_time = req_time.strftime('%Y%m%d')
    algorithm = 'AWS4-HMAC-SHA256'
    canonical_uri = '/bot/{}/alias/{}/user/{}/text'.format(bot_name, bot_alias, user_id)
    canonical_query = ''
    canonical_headers = 'content-type:application/json\n' + 'host:' + host + '\n' + 'x-amz-content-sha256:' + hashed_payload + '\n' + 'x-amz-date:' + amz_time + '\n'
    method = 'POST'
    signed_headers = 'content-type;host;x-amz-content-sha256;x-amz-date'
    canonical = '{}\n{}\n{}\n{}\n{}\n{}'.format(method, canonical_uri, canonical_query, canonical_headers, signed_headers, hashed_payload)

    canonical_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    scope = '{}/{}/lex/aws4_request'.format(short_time, region)

    str_to_sign = '{}\n{}\n{}\n{}'.format(algorithm, amz_time, scope, canonical_hash)

    k_date = hmac.new(('AWS4' + aws_secret_key).encode('utf-8'), short_time.encode('utf-8'), hashlib.sha256).digest()
    k_region = hmac.new(k_date, region.encode('utf-8'), hashlib.sha256).digest()
    k_service = hmac.new(k_region, 'lex'.encode('utf-8'), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, 'aws4_request'.encode('utf-8'), hashlib.sha256).digest()
    signature = hmac.new(k_signing, str_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    headers = {
        'Host': host,
        'Authorization': algorithm + ' Credential=' + aws_access_key + '/' + scope + ',SignedHeaders=' + signed_headers + ',Signature=' + signature,
        'Content-Type': 'application/json',
        'X-Amz-Content-Sha256': hashed_payload,
        'X-Amz-Date': amz_time
    }

    req = urllib.request.Request(
        'https://runtime.lex.us-east-1.amazonaws.com/bot/{}/alias/{}/user/{}/text'.format(bot_name, bot_alias, user_id),
        payload,
        headers=headers,
        method='POST'
    )
        
    try:
        with urllib.request.urlopen(req) as f:
            response = json.load(f)
            return True, response['message']

    except urllib.error.HTTPError as http_error:
        response = json.load(http_error)
        return False, response['message']
