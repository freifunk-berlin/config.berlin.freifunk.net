# -*- coding: utf-8 -*-

import pynipap

class Api:
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
    def __init__(self, app_name):
        pynipap.AuthOptions({'authoritative_source': app_name})

    def connect(self, uri, vrf='default'):
        """Connects to nipap instance. Vrf parameter is optional."""
        pynipap.xmlrpc_uri = uri
        
        self.vrf = self.get_vrf_by_name(vrf)
        if self.vrf is None:
            raise Exception("VRF '%s' could not be found" % vrf)

    def _get_by_name(self, cls, name):
        query = {
            'operator': 'equals',
            'val1': 'name',
            'val2': name
        }
        request = cls.search(query)['result']

        return request[0] if len(request) > 0 else None

    def get_pool_by_name(self, name):
        """Searches for a pool by name."""
        return self._get_by_name(pynipap.Pool, name)

    def get_vrf_by_name(self, name):
        """Searches for a vrf by name."""
        return self._get_by_name(pynipap.VRF, name)

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

    def _create_prefix(self, pool, prefix_len = None, data = {}):
        prefix = pynipap.Prefix()
        prefix.vrf = self.vrf
        prefix.type = 'assignment'
        for k,v in data.items():
            setattr(prefix, k, v)

        args = {'from-pool': pool, 'family': 4}
        if prefix_len is not None:
            args['prefix_length'] = prefix_len

        prefix.save(args)

    def create_prefix_from_pool(self, pool_name, prefix_len = None, data = {}):
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

        self._create_prefix(pool, prefix_len, data)
