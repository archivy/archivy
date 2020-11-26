When developing plugins, you may want to use custom HTML input types on the frontend, like `email` or `password`.

Archivy currently allows you use these two types in your click options.

For example:

```python

from archivy.click_web.web_click_types import EMAIL_TYPE, PASSWORD_TYPE
@cli.command()
@click.option("--the_email", type=EMAIL_TYPE) # this will validate the email format on the frontend and backend
@click.option("--password", type=PASSWORD_TYPE) # type='password' on the HTML frontend.
def login(the_email, password):
	...
```
