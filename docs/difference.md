
There are many great tools out there to create your knowledge base. 


So why should you use Archivy? 

Here are the ingredients that make Archivy stand out (of course many tools have other interesting components / focuses, and you should pick the one that resonates with what you want):

- **Focus on scripting and extensibility**: When I began developing archivy, I had plans for developing **in the app's core** additional features that would allow you to sync up to your digital presence, for exemple a Reddit extension that would download your upvoted posts, etc... I quickly realised that this would be a bad way to go, as many people often want maybe **one** feature, but not a ton of useless included extensions. That's when I decided to instead build a flexible framework for people to build installable [**plugins**](plugins.md), as this allows a) users only download what they want and b) Archivy can focus on its core and users can build their own extensions for themselves and others.
- **Importance of Digital Preservation**: ^ I mentioned above the idea of a plugin for saving all your upvoted reddit posts. This is just an example of how Archivy is intended to be used not only as a knowledge base, but also a resilient stronghold for the data that used to be solely held by third-party services. This idea of automatically syncing and saving content you've found valuable could be expanded to HN upvoted posts, browser bookmarks, etc... [^1]
- **deployable OR you can just run it on your computer**: The way archivy was engineered makes it possible for you to just run it on your laptop or pc, and still use it without problems. On the other hand, it is also very much a possibility to self-host it and expose it publicly for use from anywhere, which is why archivy has auth.
- **Powerful Search**: Elasticsearch might be considered overkill for one's knowledge base, but as your knowledge base grows also with content from other data sources and automation, it can become a large amount of data. Elasticsearch provides very high quality search on this information at a swift speed. We still plan on adding an alternative search system that users can choose to use if they don't want to run ES. [^2]



[^1]: https://beepb00p.xyz/hpi.html is an intriguing tool on this topic.

[^2]: See [this thread](https://github.com/archivy/archivy/issues/13) if you have any tools in mind for this.
