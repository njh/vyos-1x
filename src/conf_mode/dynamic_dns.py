#!/usr/bin/env python3
#
# Copyright (C) 2018 VyOS maintainers and contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 or later as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

import os
import sys
import jinja2

from vyos.config import Config
from vyos import ConfigError

config_dir  = r'/etc/ddclient/'
config_file = config_dir + 'ddclient_{0}.conf'

config_tmpl = """
### Autogenerated by dynamic_dns.py ###
daemon=1m
syslog=yes
ssl=yes
pid=/var/run/ddclient/ddclient_{{ interface }}.pid
cache=/var/cache/ddclient/ddclient_{{ interface }}.cache
{% if web_url and web_skip -%}
use=web, web={{ web_url}}, web-skip={{ web_skip }}
{% else -%}
use=if, if={{ interface }}
{% endif -%}

{% for rfc in rfc2136 -%}
{% for record in rfc.record %}
# RFC2136 dynamic DNS configuration for {{ record }}.{{ rfc.zone }}
server={{ rfc.server }}
protocol=nsupdate
password={{ rfc.keyfile }}
ttl={{ rfc.ttl }}
zone={{ rfc.zone }}
{{ record }}
{% endfor %}
{% endfor -%}

{% for srv in service %}
{% for host in srv.host %}
# DynDNS provider configuration for {{ host }}
protocol={{ srv.protocol }}
max-interval=28d
login={{ srv.login }}
password='{{ srv.password }}'
{{ host }}
{% endfor %}
{% endfor %}
"""

# Mapping of service name to service protocol
default_service_protocol = {
    'afraid': 'freedns',
    'changeip': 'changeip',
    'cloudflare': 'cloudflare',
    'dnspark': 'dnspark',
    'dslreports': 'dslreports1',
    'dyndns': 'dyndns2',
    'easydns': 'easydns',
    'namecheap': 'namecheap',
    'noip': 'noip',
    'sitelutions': 'sitelutions',
    'zoneedit': 'zoneedit1'
}

default_config_data = {
    'interfaces': [],
}

def get_config():
    dyndns = default_config_data
    conf = Config()
    if not conf.exists('service dns dynamic'):
        return None
    else:
        conf.set_level('service dns dynamic')

    for interface in conf.list_nodes('interface'):
        node = {
            'interface': interface,
            'rfc2136': [],
            'service': [],
            'web_skip': '',
            'web_url': ''
        }

        # set config level to e.g. "service dns dynamic interface eth0"
        conf.set_level('service dns dynamic interface {0}'.format(interface))

        # Handle RFC2136 - Dynamic Updates in the Domain Name System
        for rfc2136 in conf.list_nodes('rfc2136'):
            rfc = {
                'name': rfc2136,
                'keyfile': '',
                'record': [],
                'server': '',
                'ttl': '600',
                'zone': ''
            }

            if conf.exists('rfc2136 {0} key'.format(rfc2136)):
                rfc['keyfile'] = conf.return_value('rfc2136 {0} key'.format(rfc2136))

            if conf.exists('rfc2136 {0} record'.format(rfc2136)):
                rfc['record'] = conf.return_values('rfc2136 {0} record'.format(rfc2136))

            if conf.exists('rfc2136 {0} server'.format(rfc2136)):
                rfc['server'] = conf.return_value('rfc2136 {0} server'.format(rfc2136))

            if conf.exists('rfc2136 {0} ttl'.format(rfc2136)):
                rfc['ttl'] = conf.return_value('rfc2136 {0} ttl'.format(rfc2136))

            if conf.exists('rfc2136 {0} zone'.format(rfc2136)):
                rfc['zone'] = conf.return_value('rfc2136 {0} zone'.format(rfc2136))

            node['rfc2136'].append(rfc)

        # Handle DynDNS service providers
        for service in conf.list_nodes('service'):
            srv = {
                'provider': service,
                'host': [],
                'login': '',
                'password': '',
                'protocol': '',
                'server': ''
            }
            
            # preload protocol from default service mapping
            if service in default_service_protocol.keys():
                srv['protocol'] = default_service_protocol[service]

            if conf.exists('service {0} login'.format(service)):
                srv['login'] = conf.return_value('service {0} login'.format(service))

            if conf.exists('service {0} host-name'.format(service)):
                srv['host'] = conf.return_values('service {0} host-name'.format(service))

            if conf.exists('service {0} protocol'.format(service)):
                srv['protocol'] = conf.return_value('service {0} protocol'.format(service))

            if conf.exists('service {0} password'.format(service)):
                srv['password'] = conf.return_value('service {0} password'.format(service))

            if conf.exists('service {0} server'.format(service)):
                srv['server'] = conf.return_value('service {0} server'.format(service))

            node['service'].append(srv)

        # Additional settings in CLI
        if conf.exists('use-web skip'):
            node['web_skip'] = conf.return_value('use-web skip')

        if conf.exists('use-web url'):
            node['web_url'] = conf.return_value('use-web url')

        dyndns['interfaces'].append(node)

    return dyndns

def verify(dyndns):
    # bail out early - looks like removal from running config
    if dyndns is None:
        return None

    return None

def generate(dyndns):
    # bail out early - looks like removal from running config
    if dyndns is None:
        return None

    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    for node in dyndns['interfaces']:
        tmpl = jinja2.Template(config_tmpl)

        config_text = tmpl.render(node)
        with open(config_file.format(node['interface']), 'w') as f:
            f.write(config_text)

    return None

def apply(dns):
    raise ConfigError("error")
    return None

if __name__ == '__main__':
    try:
        c = get_config()
        verify(c)
        generate(c)
        apply(c)
    except ConfigError as e:
        print(e)
        sys.exit(1)
