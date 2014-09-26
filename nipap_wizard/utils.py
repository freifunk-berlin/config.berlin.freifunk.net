# -*- coding: utf-8 -*-

from functools import wraps
from flask import session, redirect, url_for
from nipap import Api

def session_key_needed(key, endpoint):
    def session_key_needed_(f):
        @wraps(f)
        def session_key_needed__(*args, **kwargs):
            if key not in session:
                return redirect(url_for(endpoint))
            return f(*args, **kwargs)
        return session_key_needed__
    return session_key_needed_


def send_email(api_params, email, router):
    (app_id, api_user, api_pass, api_host, pool_mesh, pool_hna) = api_params
    api = Api(app_id)
    api.connect('http://%s:%s@%s' % (api_user, api_pass, api_host))

    data = {'customer_id': 1, 'description': email}

    # create mesh ips
    mesh_ips_num = 2 if router['data']['dualband'] else 1
    mesh_ips = []
    for i in range(mesh_ips_num):
        mesh_ips.append(api.create_prefix_from_pool(pool_mesh, data = data))

    # create hna ips
    hna = api.create_prefix_from_pool(pool_hna, data = data)
