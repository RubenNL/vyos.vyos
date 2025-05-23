# (c) 2016 Red Hat Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function


__metaclass__ = type

from unittest.mock import patch

from ansible_collections.vyos.vyos.plugins.modules import vyos_user
from ansible_collections.vyos.vyos.tests.unit.modules.utils import set_module_args

from .vyos_module import TestVyosModule, load_fixture


class TestVyosUserModule(TestVyosModule):
    module = vyos_user

    def setUp(self):
        super(TestVyosUserModule, self).setUp()

        self.mock_get_config = patch(
            "ansible_collections.vyos.vyos.plugins.modules.vyos_user.get_config",
        )
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            "ansible_collections.vyos.vyos.plugins.modules.vyos_user.load_config",
        )
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestVyosUserModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, filename=None):
        self.get_config.return_value = load_fixture("vyos_user_config.cfg")
        self.load_config.return_value = dict(diff=None, session="session")

    def test_vyos_user_password(self):
        set_module_args(dict(name="ansible", configured_password="test"))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["set system login user ansible authentication plaintext-password test"],
        )

    def test_vyos_user_delete(self):
        set_module_args(dict(name="ansible", state="absent"))
        result = self.execute_module(changed=True)
        self.assertEqual(result["commands"], ["delete system login user ansible"])

    def test_vyos_user_purge(self):
        set_module_args(dict(purge=True))
        result = self.execute_module(changed=True)
        self.assertEqual(
            sorted(result["commands"]),
            sorted(
                [
                    "delete system login user ansible",
                    "delete system login user admin",
                    "delete system login user ssh",
                ],
            ),
        )

    def test_vyos_user_update_password_changed(self):
        set_module_args(
            dict(
                name="test",
                configured_password="test",
                update_password="on_create",
            ),
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["set system login user test authentication plaintext-password test"],
        )

    def test_vyos_user_update_password_on_create_ok(self):
        set_module_args(
            dict(
                name="ansible",
                configured_password="test",
                update_password="on_create",
            ),
        )
        self.execute_module()

    def test_vyos_user_update_password_always(self):
        set_module_args(
            dict(
                name="ansible",
                configured_password="test",
                update_password="always",
            ),
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            ["set system login user ansible authentication plaintext-password test"],
        )

    def test_vyos_user_set_ssh_key(self):
        set_module_args(
            dict(
                name="ansible",
                public_keys=[
                    dict(
                        name="user@host",
                        key="AAAAC3NzaC1lZDI1NTE5AAAAIFIR0jrMvBdmvTJNY5EDhOD+eixvbOinhY1eBU2uyuhu",
                        type="ssh-ed25519",
                    ),
                ],
            ),
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "set system login user ansible authentication public-keys user@host key 'AAAAC3NzaC1lZDI1NTE5AAAAIFIR0jrMvBdmvTJNY5EDhOD+eixvbOinhY1eBU2uyuhu'",
                "set system login user ansible authentication public-keys user@host type 'ssh-ed25519'",
            ],
        )

    def test_vyos_user_set_ssh_key_idempotent(self):
        set_module_args(
            dict(
                name="ssh",
                public_keys=[
                    dict(
                        name="user@host",
                        key="AAAAB3NzaC1yc2EAAAADAQABAAABAQD",
                        type="ssh-rsa",
                    ),
                ],
            ),
        )
        self.load_fixtures()
        result = self.execute_module(changed=False)
        self.assertEqual(result["commands"], [])

    def test_vyos_user_set_ssh_key_change(self):
        set_module_args(
            dict(
                name="ssh",
                public_keys=[
                    dict(
                        name="user@host",
                        key="AAAAC3NzaC1lZDI1NTE5AAAAIFIR0jrMvBdmvTJNY5EDhOD+eixvbOinhY1eBU2uyuhu",
                        type="ssh-ed25519",
                    ),
                ],
            ),
        )
        self.load_fixtures()
        result = self.execute_module(
            changed=True,
            commands=[
                "set system login user ssh authentication public-keys user@host key 'AAAAC3NzaC1lZDI1NTE5AAAAIFIR0jrMvBdmvTJNY5EDhOD+eixvbOinhY1eBU2uyuhu'",
                "set system login user ssh authentication public-keys user@host type 'ssh-ed25519'",
            ],
        )

    def test_vyos_user_set_ssh_key_add_and_remove(self):
        set_module_args(
            dict(
                name="ssh",
                public_keys=[
                    dict(
                        name="noone@nowhere",
                        key="AAAAC3NzaC1lZDI1NTE5AAAAIFIR0jrMvBdmvTJNY5EDhOD+eixvbOinhY1eBU2uyuhu",
                        type="ssh-ed25519",
                    ),
                ],
            ),
        )
        self.load_fixtures()
        result = self.execute_module(
            changed=True,
            commands=[
                "delete system login user ssh authentication public-keys user@host",
                "set system login user ssh authentication public-keys noone@nowhere key 'AAAAC3NzaC1lZDI1NTE5AAAAIFIR0jrMvBdmvTJNY5EDhOD+eixvbOinhY1eBU2uyuhu'",
                "set system login user ssh authentication public-keys noone@nowhere type 'ssh-ed25519'",
            ],
        )

    def test_vyos_user_set_ssh_key_empty(self):
        # empty public_keys has no effect (for setting passwords, user names, etc.)
        set_module_args(
            dict(
                name="ssh",
                public_keys=[],
            ),
        )
        self.load_fixtures()
        result = self.execute_module(changed=False)

    def test_vyos_user_set_encrypted_password(self):
        set_module_args(
            dict(
                name="ansible",
                encrypted_password="$6$rounds=656000$SALT$HASH",
            ),
        )
        result = self.execute_module(changed=True)
        self.assertEqual(
            result["commands"],
            [
                "set system login user ansible authentication encrypted-password '$6$rounds=656000$SALT$HASH'",
            ],
        )

    def test_vyos_user_set_encrypted_password_idem(self):
        set_module_args(
            dict(
                name="ansible",
                encrypted_password="$6$ZfvSv6A50W6yNPYX$4HP5eg2sywcXYxTqhApQ7zvUvx0HsQHrI9xuJoFLy2gM/",
            ),
        )
        result = self.execute_module(changed=False)
