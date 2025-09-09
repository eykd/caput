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

Write metadata headers to files::

    >>> metadata = {
    ...     'title': 'My New Post',
    ...     'author': 'Me',
    ...     'date': '2024-01-15'
    ... }

    >>> content = '# This is my new post\n\nLorem ipsum...'

    >>> caput.write_config('./new-post.md', metadata, content)

    >>> # Verify the file was written correctly
    >>> caput.read_config('./new-post.md')
    {'title': 'My New Post', 'author': 'Me', 'date': '2024-01-15'}

    >>> caput.read_contents('./new-post.md')
    '# This is my new post\n\nLorem ipsum...'

Update existing metadata::

    >>> # Read existing metadata
    >>> config = caput.read_config('./index.md')
    >>> config['updated'] = '2024-01-15'
    >>> config['tags'] = ['blog', 'personal']

    >>> # Write back with updated metadata
    >>> caput.write_config('./index.md', config)

Read & write contents::

    >>> content = caput.read_contents('./index.md')
    >>> config = caput.read_config('./index.md')
    >>> config['updated'] = '2025-09-09'
    >>> content += '\n\nUpdated on 2025-09-09'
    >>> caput.write_contents('./index.md', content, config)


Shadow Files for Binary Content
--------------------------------

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

Write metadata for binary files::

    >>> # Create metadata for a binary file using a shadow YAML file
    >>> binary_metadata = {
    ...     'title': 'Site Logo',
    ...     'credit': 'Design Team',
    ...     'license': 'CC BY 4.0'
    ... }

    >>> caput.write_shadow_config('./images/logo.png', binary_metadata)

    >>> # This creates ./images/logo.yml with the metadata
    >>> caput.read_config('./images/logo.png')
    {'title': 'Site Logo', 'credit': 'Design Team', 'license': 'CC BY 4.0'}
