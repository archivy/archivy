
The Archivy HTTP API allows you to run small scripts in any language that will interact with your archivy instance through HTTP.

All calls must be first logged in with the [login](/reference/web_api/#archivy.api.login) endpoint.

## Small example in Python

This code uses the `requests` module to interact with the API:

```python
import requests
# we create a new session that will allow us to login once
s = requests.session()

INSTANCE_URL = <your instance url>
s.post(f"{INSTANCE_URL}/api/login", auth=(<username>, <password>))

# once you've logged in - you can make authenticated requests to the api, like:
resp = s.get(f"{INSTANCE_URL}/api/dataobjs").content)
```


## Reference

::: archivy.api
