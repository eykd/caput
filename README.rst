Caput
=====

Easy file metadata.

Store metadata in a special YAML configuration header for text files, or a
sidecar "shadow" configuration file for binary files.

*Caput:* **n.** Latin for "head" or "top". Root of many English words, such as
"captain", "capital", and "decapitate".

Install
-------

Caput is available from PyPI::

    pip install caput

Usage
-----

Say that you're building a static site generator. You can add a metadata header
to any textfile. The first three bytes *must* be ``---\n``. In ``index.md``::

    ---
    title: My Site
    author: Me
    featured_image: /images/my-header.jpg
    ---
    # Welcome to my site!

Read the metadata header::

    >>> import caput

    >>> caput.read_config('./index.md', defaults={'markup': 'markdown'})
    {'markup': 'markdown',
     'title': 'My Site',
     'author': 'Me',
     'featured_image': '/images/my-header.jpg'}

Read the file contents::

    >>> caput.read_contents('./index.md')
    '# Welcome to my site!\n'

You can add metadata to binary files with a "shadow" header. For your featured
image, add a ``.yml`` file with the same base name, e.g. for
``./images/my-header.jpg`` you would add ``./images/my-header.yml``::

    title: My Site Header
    credit: Me

Read the metadata header::

    >>> caput.read_config('./images/my-header.jpg')
    {'title': 'My Site Header', 'credit': 'Me')

Read the file contents::

    >>> caput.read_contents('./images/my-header.jpg', encoding=None)
    b'...binary data...'
