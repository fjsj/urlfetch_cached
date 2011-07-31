# urlfetch_cached

Memcached version of Google App Engine asynchronous urlfetch. Just get the returned rpc object and use it as if it was the original one.

Author: fjsj - flaviojuvenal@gmail.com

Example (making an async request to Facebook Graph API):

    _1_HOUR = 3600
    def async_request(self, callback, path, args=None, post_args=None):
        if not args: args = {}
        if self.access_token:
            if post_args is not None:
                post_args["access_token"] = self.access_token
            else:
                args["access_token"] = self.access_token
        post_data = None if post_args is None else urllib.urlencode(post_args)
        
        rpc = urlfetch.create_rpc(deadline=10)
        def handle_result():
            result = rpc.get_result()
            response = simplejson.loads(result.content)
            if response.get("error"):
                raise GraphAPIError(response["error"]["type"],
                                    response["error"]["message"])
            callback(response)
        rpc.callback = handle_result
        rpc = urlfetch_cached.make_fetch_call(
                rpc     = rpc,
                url     = "https://graph.facebook.com/" + path + "?" + urllib.urlencode(args),
                payload = post_data,
                method  = 'POST' if post_data else 'GET',
                _expire_time = _1_HOUR
              )
        return rpc

