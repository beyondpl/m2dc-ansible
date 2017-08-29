#!/usr/bin/python

#Beyond.pl DC under M2DC project (H2020)
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.


import json
import logging
import os
import six
from six.moves import configparser

import requests
from requests.adapters import HTTPAdapter

from urlparse import urljoin, urlunsplit
from urllib import urlencode

import xml.etree.ElementTree as ET

RESOURCE_NAME = "node"
DEFAULT_BASE_URL = "http://129.70.144.122/REST/"
LOG = logging.getLogger(__name__)

class Client(object):
    """
    REST API client class
    """
    def __init__(self, base_url, username, password, **kwargs):
        """Initialize a client session"""
        self.session = requests.Session()
        self.session.mount("http://", HTTPAdapter(max_retries=kwargs.get("max_retries", 5)))
        self.session.mount("https://", HTTPAdapter(max_retries=kwargs.get("max_retries", 5)))
        self.session.auth = ("admin", "admin")
        self.session.verify = kwargs.get("ssl_cert_file", True)
        self.base_url = base_url
        self.session.headers.update({"User-Agent": "Ansible Inventory"})

    @staticmethod
    def construct_url(base_url, resource, **kwargs):
        url_parts = (None, None, urljoin(base_url, resource), urlencode(kwargs), None)
        return urlunsplit(url_parts)

    def _handle_response(self, response, resource):
        try:
            response.raise_for_status()
        except requests.HTTPError:
            try:
                result = response.json() if response.json() else response.text
            except ValueError:
                result = response.text
            raise requests.HTTPError(response, result, resource)

    REQUEST_TIMEOUT = 90

    def get(self, resource, **kwargs):
        """Send a GET request"""
        url = self.construct_url(self.base_url, resource, **kwargs)
        LOG.debug("%s", url)
        response = self.session.get(url, auth=('admin','admin'), timeout=Client.REQUEST_TIMEOUT)
        LOG.debug("result: [%s]", response)
        self._handle_response(response, resource)

        return response.text

    def close(self):
        """Close the client session"""
        self.session.close()
        return True

class recsInventory(object):


    @property
    def empty_inventory(self):
        return self._empty_inventory

    @property
    def recs_inventory_template(self):
        return self._inventory_template

    @property
    def inventory(self):
        return self._inventory

    @property
    def recs_vars(self):
        return self._recs_vars


    def __init__(self, configuration_id=None, username=None, api_password=None, override_config_file=None, base_url=DEFAULT_BASE_URL):
        """ Excecution path """
        self._recs_vars         =     {u"base_url":base_url,
                                            u"username":username,
                                            u"api_password":api_password}
        self._empty_inventory     =     {u"_meta":{u"hostvars": {}}}
        self._inventory_template  =     {u"recs_environment"  : {u"hosts": [], u"vars": {}},
                                            u"_meta": {u"hostvars":{}}}
        self._clientData = {}
        self._inventory = self._inventory_template

        self._client = Client(self.recs_vars[u"base_url"], self.recs_vars[u"username"], self.skytap_vars[u"api_password"])


        self.recs_vars[u"username"] = "admin"
        self.recs_vars[u"api_password"] = "admin"

    def get_data(self):
        #query_string = RESOURCE_NAME + "/" + str(self.recs_env_vars[u"configuration_id"]) + ".json"
        query_string = RESOURCE_NAME
        url = Client.construct_url(self.recs_vars[u"base_url"], query_string)
        self._clientData = self._client.get(url)
        #print("%s", self._clientData )
        return self._clientData


    def parse_xml_to_inventory(self, client_data, inventory):
        """parses xml and builds inventory structure"""
        root = ET.fromstring(client_data)
        for child in root:
            print(child.tag, child.attrib)
        #for node in root.findall('baseBoardId'):
        #    name = node.get('health')
        #    print(node, name)
        return inventory

    def get_inventory(self):
        """get the API data, parse it into an inventory"""
        api_data = self.get_data()
        #print("%s", api_data)
#        network_type = self.recs_env_vars[u"network_type"]
        parse_method = self.parse_xml_to_inventory
        parse_method(api_data, self.inventory)

        return self.inventory

    def run_as_script(self):
        """get the invenotry data, dump it into json string"""
        return json.dumps(self.get_inventory())

def main():
    print(recsInventory().run_as_script())
if __name__ == "__main__":
    main()
