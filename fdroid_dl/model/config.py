"""Package exposing fdroid_dl.Config."""
# -*- coding: utf-8 -*-

import logging
import collections
import copy
import json
import os
import os.path
import shutil
from tempfile import NamedTemporaryFile
from .repoconfig import RepoConfig
from .metadata import Metadata
from .index import Index
from ..json import GenericJSONEncoder


LOGGER = logging.getLogger('model.Config')


class Config(collections.MutableMapping):
    """
    Main Class responsible for handling the f-droid.json config file.

    This Class represents the config file used by fdroid-dl and will default to
    https://f-droid.org/repo/ as bas repo and add at least the
    **org.fdroid.fdroid** app for download into the queue.
    """

    DEFAULTS = {
        "f-droid": {
            'https://f-droid.org/repo/': {
                "apps": ["org.fdroid.fdroid"]
            }
        },
        "metadata": {}
    }

    def __init__(self, filename='fdroid-dl.json', repo_dir='./repo',
                 metadata_dir='./metadata', cache_dir='.cache', apk_versions=1):
        """
        Parameters
        ----------
        filename : str
            filename including path where to store the generated config file
        repo_dir : str
            path to f-droid repo, apk files will be downloded here
        metadata_dir : str
            path to f-droid metadata directory, images and descriptions will
            be stored here
        cache_dir : str
            directory to store extracted and parsed index.json files from
            f-droid repo
        apk_versions: int
            how many versions of apk files should be downloaded
        """
        self.__filename = filename
        self.__repo = repo_dir
        self.__metadata_dir = metadata_dir
        self.__cache_dir = cache_dir
        self.__store = {}
        self.__indices = {}
        self.__metadata = None
        self.__apk_versions = apk_versions
        self.__init_defaults()
        self.__prepare_fs()

    @property
    def filename(self):
        return str(self.__filename)

    @property
    def repo_dir(self):
        return str(self.__repo)

    @property
    def metadata_dir(self):
        return str(self.__metadata_dir)

    @property
    def cache_dir(self):
        return str(self.__cache_dir)

    @property
    def store(self):
        return str(self.__store)

    @property
    def metadata(self):
        return self.__metadata

    @property
    def size(self):
        return len(self.__store.keys())

    @property
    def apk_versions(self):
        return int(self.__apk_versions)

    def __init_defaults(self):
        self.__store = copy.deepcopy(Config.DEFAULTS)
        for key in Config.DEFAULTS['f-droid'].keys():
            cfg = RepoConfig(key, self.__store['f-droid'][key], self)
            self.__store['f-droid'][cfg.url] = cfg
        self.__metadata = Metadata(self, Config.DEFAULTS.get('metadata', {}))

    def __prepare_fs(self):
        os.makedirs(self.__repo, exist_ok=True)
        os.makedirs(self.__metadata_dir, exist_ok=True)
        os.makedirs(self.__cache_dir, exist_ok=True)

    def load(self, file=None):
        """
        Loads given file handler or filename into Config object and resolves.

        """
        if file is None:
            file = self.__filename
        if not hasattr(file, 'read'):
            file = open(file, 'r')

        if os.path.isfile(self.__filename):
            with open(self.__filename) as config_file:
                try:
                    file_data = json.load(config_file)
                    if 'f-droid' in file_data:
                        for key in file_data['f-droid'].keys():
                            cfg = RepoConfig(
                                key, file_data['f-droid'][key], self)
                            self.__store['f-droid'][cfg.url] = cfg
                    if 'metadata' in file_data:
                        self.__metadata = Metadata(self, file_data['metadata'])
                        self.__store['metadata'] = self.__metadata
                except Exception:
                    LOGGER.exception("Fatal error reading %s", config_file)

    def save(self):
        with NamedTemporaryFile(mode='w') as tmp:
            json.dump(self.__store, tmp, sort_keys=True,
                      indent=4, cls=GenericJSONEncoder)
            tmp.flush()
            shutil.copy(tmp.name, self.__filename)
        return self

    @property
    def repos(self):
        for key in self.__store['f-droid'].keys():
            cfg = self.__store['f-droid'][key]
            if not isinstance(cfg, RepoConfig):
                self.__store['f-droid'][key] = RepoConfig(key, cfg, self)
            yield cfg

    @property
    def indices(self):
        for repo in self.repos:
            if repo.url in self.__indices:
                yield self.__indices[repo.url]
            elif os.path.exists(repo.filename):
                with Index.fromJSON(repo.filename, key=repo.url) as idx:
                    self.__indices[repo.url] = idx
                    yield idx

    def repo(self, url):
        """
        Return RepoConfig based on url.

        Searches in config file for given url and returns the corresponding
        RepoConfig Class representation of it. if the repo is marked as
        having errors it will not be found. A KeyError is being raised if
        given url is not found or has an error node in the json file.

        Parameters
        ----------
        key : str
            url of repo in config file

        Returns
        -------
        fdroid_dl.model.Index
            index found for given key

        Raises
        ------
        KeyError
            raised if given url is not found or is in error state

        """
        if url in self.__store['f-droid']:
            cfg = self.__store['f-droid'][url]
            if not isinstance(cfg, RepoConfig):
                self.__store['f-droid'][url] = RepoConfig(url, cfg, self)
            if 'error' not in cfg:
                return cfg
        raise KeyError("repo with url: %s not found" % url)

    def index(self, url):
        """
        Return Index based on url.

        Searches for downloaded index file based on repository url as
        configured in config file.

        Parameters
        ----------
        url : str
            url of repo in config file

        Returns
        -------
        fdroid_dl.model.Index
            index found for given url

        """
        repo = self.repo(url)
        if repo.url in self.__indices:
            return self.__indices[repo.url]
        if os.path.exists(repo.filename):
            with Index.fromJSON(repo.filename, key=repo.url) as idx:
                self.__indices[repo.url] = idx
            return self.__indices[repo.url]
        raise KeyError(
            "index with url: %s not found on filesystem file: %s" %
            (url, repo.filename))

    def __repr__(self):
        """."""
        return "<Config: %s>" % str(self.__store)
    #######################
    # implement "dict"
    #######################

    def __getitem__(self, key):
        """."""
        return self.__store[key]

    def __setitem__(self, key, value):
        """."""
        self.__store[key] = value

    def __delitem__(self, key):
        """."""
        del self.__store[key]

    def __iter__(self):
        """."""
        return iter(self.__store)

    def __len__(self):
        """."""
        return len(self.__store)
    #######################
    # implement "with"
    #######################

    def __enter__(self):
        """."""
        self.load()
        return self

    def __exit__(self, type, value, traceback):
        """."""
        self.save()
