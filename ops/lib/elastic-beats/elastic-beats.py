# Copyright 2020 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Implements the requires side handling of the 'elastic-beats' interface."""

import json
import logging

from ops.model import ModelError, BlockedStatus, WaitingStatus
from ops.framework import Object, EventBase, EventSetBase, EventSource, StoredState

logger = logging.getLogger(__name__)


class BeatsError(ModelError):
    """A base class for all errors raised by interface"""

    def __init__(self, kind, message, relation_name):
        super().__init__()
        self.status = kind('{}: {}'.format(message, relation_name))


class BeatsClientError(BeatsError):
    """An error specific to the BeatsClient class"""


class BeatsAvailable(EventBase):

    """Event emitted by BeatsClient.on.available."""
    pass


class BeatsClientEvents(EventSetBase):

    """Events emitted by the BeatsClient class."""

    beats_available = EventSource(BeatsAvailable)


class BeatsClient(Object):
    """Provides a client type that handles the interaction with charms."""

    on = BeatsClientEvents()
    _stored = StoredState()

    def __init__(self, charm, relation_name):
        """
        :param charm: the charm object to be used as a parent object.
        :type charm: :class: `ops.charm.CharmBase`
        """
        super().__init__(charm, relation_name)
        self._relation_name = relation_name
        #self._stored.set_default(ca_certificate=None, key=None, certificate=None)

        self.framework.observe(charm.on[relation_name].relation_joined, self._on_relation_joined)
        self.framework.observe(charm.on[relation_name].relation_changed, self._on_relation_changed)

    @property
    def socket_addresses(self):
        sock_addrs = []
        for unit in self._relation.units:
            unit_data = self._relation.data[unit]
            port = unit_data.get('port')
            if port is not None:
                sock_addrs.append(unit_data['ingress-address'], port)
        return sock_addrs

    @property
    def is_joined(self):
        return self.framework.model.get_relation(self._relation_name) is not None

    @property
    def _on_relation_changed(self, event):
        if event.unit is not None:
            if event.relation.data[event.unit].get('port') is not None:
                self.on.emit.server_ready()
