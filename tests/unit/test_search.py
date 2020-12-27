from archivy.data import get_items
import archivy.search

def test_lunr_index_builds_correctly(test_app, note_fixture, bookmark_fixture):
    index = archivy.search.create_lunr_index(documents=get_items(structured=False))
    
    # search for title of note
    results = index.search("Test")
    assert len(results) == 1
    assert int(results[0]["ref"]) == note_fixture.id

    # make sure it matched with the "title"
    assert "title" in results[0]["match_data"].metadata["test"].keys()

    # search bookmark contents
    results = index.search("Lorem Ipsum")
    assert len(results) == 1
    assert int(results[0]["ref"]) == bookmark_fixture.id
    
    # check it correctly matched instances of the body
    assert "body" in results[0]["match_data"].metadata["lorem"].keys()
    assert "body" in results[0]["match_data"].metadata["ipsum"].keys()
