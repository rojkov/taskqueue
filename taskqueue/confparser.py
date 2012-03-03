
import logging

from ConfigParser import SafeConfigParser, NoSectionError

LOG = logging.getLogger(__name__)

SECTION_WORKERS = 'workers'

PREFIX_GROUP = 'worker'

OPT_RESULTS_ROUTING_KEY = "results_routing_key"
OPT_SUBGROUPS           = 'subgroups'
OPT_INSTANCES           = 'instances'
OPT_PLUGINS             = 'enabled_plugins'


class ConfigParser(SafeConfigParser):
    """Config parser extended to ignore DEFAULT section."""

    def items(self, section, raw=False, vars=None, defaults=None):
        """Return a list of (name, value) pairs for each option in the section.

        The options are looked up in `vars`, `section`, `defaults` and in the
        section `DEFAULT` in that order.

        :param section: section name
        :type section: string
        :param raw: if set to True then all the '%' interpolations are expanded
                    in the return values
        :type raw: boolean
        :param vars: overrides values in the given config section
        :type vars: dictionary
        :param defaults: overrides values in the DEFAULT section
        :type defaults: dictionary
        :returns: list of (name, value) pairs for each option in the section
        :rtype: list
        """

        LOG.debug("Fetching options from section '%s'" % section)

        if vars is None:
            vars = {}

        if defaults is None:
            return SafeConfigParser.items(self, section, raw, vars)

        output = defaults.copy()
        if not self.has_section(section):
            return list(output.items())

        # preserve config defaults and delete them from config
        conf_defaults = self.defaults().copy()
        for key in conf_defaults.keys():
            self.remove_option('DEFAULT', key)

        output.update(SafeConfigParser.items(self, section, raw, vars))

        # restore default options in config
        for key, value in conf_defaults.items():
            self.set('DEFAULT', key, value)
        return list(output.items())

