import json
import random
import core
import collections
from core.helpers import Comparisons
from core import scheduler


class Config():
    ''' Config
    Config is a simple json object that is loaded into core.CONFIG as a dict

    All sections and subsections must be capitalized. All keys must be lower-case.
    No spaces, underscores, or hyphens.
    Be terse but descriptive.
    '''

    def __init__(self):
        self.file = core.CONF_FILE
        self.base_file = 'core/base_config.cfg'

    def new_config(self):
        ''' Copies base_file to config directory.

        Automatically assigns random values to searchtimehr, searchtimemin,
            installupdatehr, installupdatemin, and apikey.

        Config template is stored as core/base_config.cfg

        When adding keys to the base config:
            Keys will have no spaces, hypens, underscores or other substitutions
                for a space. Simply crush everything into one word.
            Keys that access another dictionary should be capitalized. This can
                be done in the way that makes most sense in context, but should
                try to mimic camel case.
            Keys that access a non-dictionary value should be lowercase.

        Returns str 'Config Saved' on success. Throws execption on failure.
        '''

        with open(self.base_file, 'r') as f:
            config = json.load(f)

        config['Search']['searchtimehr'] = random.randint(0, 23)
        config['Search']['searchtimemin'] = random.randint(0, 59)

        config['Server']['installupdatehr'] = random.randint(0, 23)
        config['Server']['installupdatemin'] = random.randint(0, 59)

        config['Search']['popularmovieshour'] = random.randint(0, 23)
        config['Search']['popularmoviesmin'] = random.randint(0, 59)

        apikey = "%06x" % random.randint(0, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        config['Server']['apikey'] = apikey

        with open(self.file, 'w') as f:
            json.dump(config, f, indent=4, sort_keys=True)
        return 'Config created at {}'.format(self.file)

    def write(self, data):
        ''' Writes a dict to the config file.
        :param data: dict of Section with nested dict of keys and values:

        {'Section': {'key': 'val', 'key2': 'val2'}, 'Section2': {'key': 'val'}}

        MUST contain fully populated sections or data will be lost.

        Only modifies supplied section.

        After updating config file, copies to core.CONFIG via self.stash()

        Does not return.
        '''

        diff = Comparisons.compare_dict(data, core.CONFIG)

        core.CONFIG.update(data)

        with open(self.file, 'w') as f:
            json.dump(core.CONFIG, f, indent=4, sort_keys=True)

        self.stash(config=core.CONFIG)

        if diff:
            scheduler.restart_scheduler(diff)

        return

    def merge_new_options(self):
        ''' Merges new options in base_config with config

        Opens base_config and config, then saves them merged with config taking priority.

        Does not return
        '''

        new_config = {}

        with open(self.base_file, 'r') as f:
            base_config = json.load(f)
        with open(self.file, 'r') as f:
            config = json.load(f)

        new_config = self._merge(base_config, config)

        # Convert imdb str to list
        if type(new_config['Search']['Watchlists']['imdbrss']) == str:
            new_config['Search']['Watchlists']['imdbrss'] = new_config['Search']['Watchlists']['imdbrss'].split(',')

        # Convert from predb-only verifying to multiple choice
        if new_config['Search'].get('predbcheck') is True:
            new_config['Search']['verifyreleases'] = 'predb'
            del new_config['Search']['predbcheck']

        # Convert from hardlink option to multiple choice
        if new_config['Postprocessing'].get('createhardlink') is True:
            new_config['Postprocessing']['movermethod'] = 'hardlink'
            del new_config['Postprocessing']['createhardlink']

        with open(self.file, 'w') as f:
            json.dump(new_config, f, indent=4, sort_keys=True)

        return

    def _merge(self, d, u):
        ''' Deep merge dictionaries
        d: dict base dict to merge into
        u: dict dict to update from

        If any k:v pair in u is not in d, adds k:v pair.

        Will not overwrite any values in d, nor will it remove
            any k:v pairs in d.

        Returns dict
        '''
        for k, v in u.items():
            if isinstance(v, collections.Mapping):
                r = self._merge(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        return d

    def dump(self, config=core.CONFIG):
        ''' Writes config to file
        config: dict of config  <default core.CONFIG>

        Opposite of stash. Writes config to disk

        Returns bool
        '''
        try:
            with open(self.file, 'w') as f:
                json.dump(config, f, indent=4, sort_keys=True)
        except Exception as e:
            return False

        return True

    def stash(self, config=None):
        ''' Stores entire config as dict to core.CONFIG
        config: dict config file contents <optional>

        If 'config' is not supplied, reads config from disk. If calling stash() from
            a method in this class pass the saved config so we don't have to read from
            a file we just wrote to.

        Sanitizes input when neccesary

        Does not return
        '''

        if not config:
            with open(self.file, 'r') as f:
                config = json.load(f)

        repl = config['Postprocessing']['replaceillegal']
        if repl in ('"', '*', '?', '<', '>', '|', ':'):
            config['Postprocessing']['replaceillegal'] = ''

        core.CONFIG = config

        return
