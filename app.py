#!/usr/bin/python

import base64
import logging
from cable.client import JsonRequest as Req
from cable.request_controller import Action
from config import ALLOWED_ACCOUNTS, STORAGE, PAGE_SIZE
from flask import Flask, jsonify, abort, send_from_directory, request
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS
from os import makedirs
from os.path import dirname, join

app = Flask(__name__)
auth = HTTPBasicAuth()
CORS(app)


@auth.verify_password
def check_allowed(username: str, password: str) -> dict:
    account = ALLOWED_ACCOUNTS.get(username)
    if account is None:
        logging.info(f"Attempt to use {username} FAILED. not allowed")
        return False

    account['email'] = username
    account['pwd'] = password
    return account


@auth.error_handler
def unauthorized():
    return jsonify(error='Invalid credentials'), 403


def get_account() -> dict:
    return dict(auth.current_user())


@app.route('/')
@auth.login_required
def get_folders():
    account: dict = get_account()

    data, status = Req(account, Action.FOLDERS).send()
    if status == 401:
        logging.info(
            f"Attempt to use {account['email']} FAILED. {data['error']}")

    return jsonify(data), status


@app.route('/<folder>')
@auth.login_required
def get_headers(folder):
    data: dict = get_account()
    data['folder'] = folder

    try:
        # must be integers
        data['page_size'] = int(request.args.get('page_size', PAGE_SIZE))
        data['page'] = int(request.args.get('page', 0))
    except:
        abort(400)

    data, status = Req(data, Action.MAILS).send()
    if status == 401:
        logging.info(f"Attempt to use {data['email']} FAILED. {data['error']}")

    return jsonify(data), status


@app.route('/<folder>/<uid>', methods=['GET'])
@auth.login_required
def get_mail(folder, uid):
    data: dict = get_account()
    data['folder'] = folder
    data['uid'] = uid
    email = data['email']

    response, status = Req(data, Action.DOWNLOAD).send()
    if status == 401:
        logging.info(f"Attempt to use {email} FAILED. {response['error']}")
        abort(401)

    def store_att(email: str, uid: str, att: dict) -> str:
        filename = att['filename']
        path = join(STORAGE, email, uid, filename)

        makedirs(dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            payload = att['payload']
            content = base64.b64decode(payload.encode())
            f.write(content)

        return join('/att', uid, filename)

    if not 'attachments' in response:
        return jsonify(response), status

    for i, att in enumerate(response['attachments']):
        if 'av' in att:
            logging.critical(
                f"AV scan for {att['filename']} FAILED. {att['av']}")
            continue
        else:
            logging.info(f"AV scan for {att['filename']} PASSED")

        url = store_att(email, uid, att)
        del att['payload']
        att['link'] = url
        response['attachments'][i] = att

    return jsonify(response), status


@app.route('/att/<uid>/<filename>', methods=['GET'])
@auth.login_required()
def download_att(uid, filename):
    account: dict = get_account()

    # do a folder request to force an authentication
    # data is useless, we only have to check for 200
    # to know if the user can access the <email> folder
    # inside the storage (or happened some error)
    #
    response, status = Req(account, Action.FOLDERS).send()
    if status == 401:
        logging.info(
            f"Attempt to use {account['email']} FAILED. {response['error']}")
    if status != 200:
        return jsonify(response), status

    return send_from_directory(join(STORAGE, account['email'], uid), filename)


@app.route('/<folder>/<uid>', methods=['DELETE'])
@auth.login_required()
def delete_mail(folder, uid):
    data: dict = get_account()
    data['folder'] = folder
    data['uid'] = uid

    response, status = Req(data, Action.DELETE).send()
    if status == 401:
        logging.info(
            f"Attempt to use {data['email']} FAILED. {response['error']}")
    return jsonify(response), status


@app.route('/<folder>/<uid>', methods=['PUT'])
@auth.login_required()
def unsee(folder, uid):
    data: dict = get_account()
    data['folder'] = folder
    data['uid'] = uid

    arg = request.args.get('unsee', False)
    unsee = str(arg).lower() in ['true', '1', 'yes']

    if not unsee:
        return jsonify({"msg", "Nothing to do"}), 304

    response, status = Req(data, Action.UNSEEN).send()
    if status == 401:
        logging.info(
            f"Attempt to use {data['email']} FAILED. {response['error']}")

    return jsonify(response), status


@app.route('/ping')
def ping():
    return jsonify(msg='pong')


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        # ssl_context=('cert/cert.pem', 'cert/key.pem')
    )
