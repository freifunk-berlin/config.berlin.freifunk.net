from api import Api

api_user = 'foo'
api_pass = 'bar'
api_host = 'localhost:1337'

api = Api('nipap-wizard')
api.connect('http://%s:%s@%s' % (api_user, api_pass, api_host))

# List all pools
print("Registered pools:")
for p in api.list_all_pools():
    print("\t* %s" % p.name)

# List all prefixes
print("\nRegistered prefixes:")
for p in api.list_all_prefixes():
    print("\t* %s" % p.prefix)

# create prefix from a pool named Mesh
data = {'customer_id':'foo@bar.de', 'description':'foobar'}
api.create_prefix_from_pool('Mesh', data = data)

# create prefix with a specific prefix length from a pool named Mesh
api.create_prefix_from_pool('Mesh', 26)

# Search for free prefixes in a pool:
print("\nFree prefixes:")
print("\t* %s" % api.find_free_prefix('Mesh'))
print("\t* %s" % api.find_free_prefix('Mesh', 26))

