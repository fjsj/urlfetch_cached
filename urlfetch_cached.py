'''
Memcached version of Google App Engine asynchronous urlfetch.
Just get the returned rpc object and use it as it was the original one.

Author: fjsj - flaviojuvenal@gmail.com
'''
from google.appengine.api import urlfetch, memcache
from google.appengine.api.urlfetch import GET
import simplejson as json
import logging
import copy

cache_client = memcache.Client()

class CachedRPC(object):
    '''In accordance to:
    http://code.google.com/intl/en/appengine/docs/python/urlfetch/asynchronousrequests.html#The_RPC_Object'''
    def __init__(self, rpc, cache_key, cached_result, expire_time):
        self.rpc = rpc
        self.cache_key = cache_key
        self.cached_result = cached_result
        if cached_result:
            logging.debug('cache hit for key: %s' % cache_key)
        self.expire_time = expire_time
        self.wait_called = False
        
    def get_callback(self):
        return self.rpc.callback
    
    def set_callback(self, callback):
        self.rpc.callback = callback
    
    callback = property(get_callback, set_callback)
                
    def deadline(self):
        return self.rpc.deadline
            
    def wait(self):
        if not self.wait_called:
            if self.cached_result:
                self.callback() 
            else:
                self.rpc.wait()
            self.wait_called = True

    def check_success(self):
        if self.cached_result:
            return self.cached_result
        else:
            result = self.rpc.get_result()
            cache_client.set(self.cache_key, result, self.expire_time)
            logging.debug('caching key: %s' % self.cache_key)
            return result
            
    def get_result(self):
        return self.check_success()

def make_fetch_call(rpc, url, payload=None, method=GET, headers={},
                    allow_truncated=False, follow_redirects=True,
                    validate_certificate=None, _expire_time=0):
    #key is made with json.dumps because it is better than pickle.dumps, see:
    #http://kovshenin.com/archives/app-engine-python-objects-in-the-google-datastore/
    args_dict = copy.copy(locals())
    del args_dict['rpc']
    cache_key = make_fetch_call.__name__ + '(' + json.dumps(args_dict) + ')'
    cached_result = cache_client.get(cache_key)
    if not cached_result:
        urlfetch.make_fetch_call(rpc, url, payload, method, headers,
                                 allow_truncated, follow_redirects,
                                 validate_certificate)
    return CachedRPC(rpc, cache_key, cached_result, _expire_time)
    
