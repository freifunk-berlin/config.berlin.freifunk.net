# -*- coding: utf-8 -*-

import pynipap

class NipapApi:
    """This class wraps pynipap into an useable API for creating prefixes.
       Before you can use API functions you have to connect to a valid 
       nipap instance like the following:

           api_user = 'foo'
           api_pass = 'bar'
           api_host = 'localhost:1337'
           
           api = Api('nipap-wizard')
           api.connect('http://%s:%s@%s' % (api_user, api_pass, api_host))


       * List all pools
           for p in api.list_all_pools():
               print(p.name)

       * List all prefixes
           for p in api.list_all_prefixes():
               print(p.prefix)

       * Search for free prefixes in a pool:
           api.find_free_prefix('Mesh')
           api.find_free_prefix('Mesh', 26)

       * create prefix from a pool named Mesh
           data = {'customer_id':'foo@bar.de', 'description':'foobar'}
           api.create_prefix_from_pool('Mesh', data = data)

       * create prefix with a specific prefix length from a pool named Mesh
           api.create_prefix_from_pool('Mesh', 26)
    """
    def __init__(self, app_id):
        self.app_id = app_id
        pynipap.AuthOptions({'authoritative_source': app_id})

    def connect(self, uri, vrf='default'):
        """Connects to nipap instance. Vrf parameter is optional."""
        pynipap.xmlrpc_uri = uri
        
        self.vrf = self.get_vrf_by_name(vrf)
        if self.vrf is None:
            raise Exception("VRF '%s' could not be found" % vrf)

    def _get_by(self, cls, val1, val2, search_options = None):
        query = {
            'operator': 'equals',
            'val1': str(val1),
            'val2': str(val2)
        }
        return cls.search(query, search_options)['result']

    def _get_one_by(self, cls, val1, val2):
        req = self._get_by(cls, val1, val2)
        return req[0] if len(req) > 0 else None

    def get_prefix_by_cidr(self, prefix):
        """Searches for a Prefix by cidr."""
        return self._get_one_by(pynipap.Prefix, 'prefix', prefix)

    def get_pool_by_name(self, name):
        """Searches for a pool by name."""
        return self._get_one_by(pynipap.Pool, 'name', name)

    def get_vrf_by_name(self, name):
        """Searches for a vrf by name."""
        return self._get_one_by(pynipap.VRF, 'name', name)

    def get_prefixes_by_external_key(self, external_key):
        """Searches for prefixes by external_key."""
        return self._get_by(pynipap.Prefix, 'external_key', '%d' % external_key)

    def get_prefixes_by_pool_name(self, pool_name):
        # 2^31-1 is max value XML-RPC supports
        opts = { 'include_all_children': True, 'max_result': (2**31)-1 }
        return self._get_by(pynipap.Prefix, 'pool_name', pool_name, opts)

    def find_free_prefix(self, pool_name, prefix_len = None):
        """Searches for a valid free prefix in a given pool."""
        args = {'from-pool': { 'name':  pool_name}, 'family': 4 }
        if prefix_len is not None:
            args['prefix_length'] = prefix_len

        return pynipap.Prefix.find_free(self.vrf, args)[0]

    def list_all_pools(self):
        return pynipap.Pool.list()

    def list_all_prefixes(self):
        return pynipap.Prefix.list()

    def _create_prefix(self, pool, prefix_type, family = 4, prefix_len = None, data = {}):
        prefix = pynipap.Prefix()
        prefix.vrf = self.vrf
        prefix.type = prefix_type
        for k,v in data.items():
            setattr(prefix, k, v)

        args = {'from-pool': pool, 'family': family}
        if prefix_len is not None:
            args['prefix_length'] = prefix_len

        prefix.save(args)

        return prefix

    def create_prefix_from_pool(self, pool_name, prefix_type = 'assignment', prefix_len = None, family = 4, data = {}):
        """Creates a prefix from a given pool. You can specify prefix_len if
           you do not want to us default prefix_len of that pool. Additional
           data can be added with data (as a dict). Only the following
           attributes are valid: description, comment, tags, node, type,
           country, order_id, customer_id, external_key, alarm_priority,
           monitor and vlan.
        """
        pool = self.get_pool_by_name(pool_name)
        if pool is None:
            raise Exception("Pool '%s' does not exist" % pool_name)

        prefix = self._create_prefix(pool, prefix_type, family, prefix_len, data=data)

        return prefix.prefix

    def allocate_ips(self, pool, request_id, email, hostname, prefix_len = None, family = 4, prefix_type='reservation'):
        data = {
            'tags': [self.app_id],
            'description' : hostname,
            'customer_id' : email,
            'external_key' : request_id
        }
        return self.create_prefix_from_pool(pool, prefix_type, prefix_len,
                family, data=data)

    def activate_ips(self, request_id):
        for p in self.get_prefixes_by_external_key(request_id):
            p.type = 'assignment'
            p.save()

    def get_prefixes_for_id(self, prefix_id):
        prefixes = self.get_prefixes_by_external_key(prefix_id)
        return [p.prefix for p in prefixes]

    def delete_prefixes_by_id(self, external_key):
        for p in self.get_prefixes_by_external_key(external_key):
            p.remove()

    def create_prefix_by_cidr(self, cidr, email, pool = None, data = {}):
        p = pynipap.Prefix()
        p.type = 'assignment'
        p.prefix = cidr
        p.customer_id = email
        for k,v in data.items():
            setattr(p, k, v)

        if pool is not None:
            p.pool_id = self.get_pool_by_name(pool).id

        p.save()
