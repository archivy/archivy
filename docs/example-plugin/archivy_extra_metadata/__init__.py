import click
from tinydb import Query
from archivy.helpers import get_db
from archivy import app

@click.group()
def extra_metadata():
    """`archivy_extra_metadata` plugin to add metadata to your notes."""
    pass

@extra_metadata.command()
@click.option("--author", required=True)
@click.option("--location", required=True)
def setup(author, location):
    """Save metadata values."""    
    with app.app_context():
        # save data in db
        get_db().insert({"type": "metadata", "author": author, "location": location})
    click.echo("Metadata saved!")


def add_metadata(dataobj):
	with app.app_context():
		metadata = get_db().search(Query().type == "metadata")[0]
		dataobj.content += f"Made by {metadata['author']} in {metadata['location']}."
