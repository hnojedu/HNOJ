import hashlib
import hmac
import json


def sign(data, key):
    print(data)
    data_str = json.dumps(data)
    data_bytes = data_str.encode('utf-8')

    signature = hmac.new(key, data_bytes, hashlib.sha256).hexdigest()

    data = {'data': data_str, 'signature': signature}

    return data


def unpack(received_data, key):
    print(received_data)
    data = received_data['data']
    received_signature = received_data['signature']

    submission_bytes = data.encode('utf-8')

    calculated_signature = hmac.new(key, submission_bytes, hashlib.sha256).hexdigest()

    if received_signature != calculated_signature:
        return None

    return data
