# -*- coding: utf-8 -*-

# Copyright (2018) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Python libs
import json
from unittest import mock

# 3rd party libs
from flask import Flask
from flask import Response
from flask_api import status
from hpOneView.exceptions import HPOneViewException

# Module libs
from oneview_redfish_toolkit.api.redfish_error import RedfishError
from oneview_redfish_toolkit.blueprints import resource_block
from oneview_redfish_toolkit.tests.base_test import BaseTest


class TestResourceBlock(BaseTest):
    """Tests for ResourceBlock blueprint"""

    @classmethod
    def setUpClass(self):
        # creates a test client
        self.app = Flask(__name__)

        self.app.register_blueprint(resource_block.resource_block)

        @self.app.errorhandler(status.HTTP_500_INTERNAL_SERVER_ERROR)
        def internal_server_error(error):
            """General InternalServerError handler for the app"""

            redfish_error = RedfishError(
                "InternalError",
                "The request failed due to an internal service error.  "
                "The service is still operational.")
            redfish_error.add_extended_info("InternalError")
            error_str = redfish_error.serialize()
            return Response(
                response=error_str,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                mimetype="application/json")

        @self.app.errorhandler(status.HTTP_404_NOT_FOUND)
        def not_found(error):
            """Creates a Not Found Error response"""
            redfish_error = RedfishError(
                "GeneralError", error.description)
            error_str = redfish_error.serialize()
            return Response(
                response=error_str,
                status=status.HTTP_404_NOT_FOUND,
                mimetype='application/json')

        self.app = self.app.test_client()

        # propagate the exceptions to the test client
        self.app.testing = True

        with open(
            'oneview_redfish_toolkit/mockups/oneview/ServerHardware.json'
        ) as f:
            self.server_hardware = json.load(f)

    @mock.patch.object(resource_block, 'g')
    def test_get_resource_block_not_found(self, g):
        error = HPOneViewException({
            'errorCode': 'RESOURCE_NOT_FOUND',
            'message': 'server-hardware not found'
        })
        g.oneview_client.index_resources.get_all.return_value = [
            {"category": "server-hardware"}
        ]
        g.oneview_client.server_hardware.get.side_effect = error

        response = self.app.get(
            "/redfish/v1/CompositionService/ResourceBlocks"
            "/30303437-3034-4D32-3230-313133364752")

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertEqual("application/json", response.mimetype)

    @mock.patch.object(resource_block, 'g')
    def test_get_resource_block_internal_error(self, g):
        with open('oneview_redfish_toolkit/mockups/errors/Error500.json') as f:
            error_500 = json.load(f)

        g.oneview_client.index_resources.get_all.return_value = [
            {"category": "server-hardware"}
        ]
        g.oneview_client.server_hardware.get.side_effect = Exception()

        response = self.app.get(
            "/redfish/v1/CompositionService/ResourceBlocks"
            "/30303437-3034-4D32-3230-313133364752")

        result = json.loads(response.data.decode("utf-8"))

        self.assertEqual(
            status.HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)
        self.assertEqual("application/json", response.mimetype)
        self.assertEqual(error_500, result)

    @mock.patch.object(resource_block, 'g')
    def test_get_resource_block(self, g):
        with open(
            'oneview_redfish_toolkit/mockups/oneview'
            '/ServerProfileTemplates.json'
        ) as f:
            server_profile_templates = json.load(f)

        with open(
            'oneview_redfish_toolkit/mockups/redfish'
            '/ServerHardwareResourceBlock.json'
        ) as f:
            expected_resource_block = json.load(f)

        g.oneview_client.index_resources.get_all.return_value = [
            {"category": "server-hardware"}
        ]
        g.oneview_client.server_hardware.get.return_value = \
            self.server_hardware
        g.oneview_client.server_profile_templates.get_all.return_value = \
            server_profile_templates

        response = self.app.get(
            "/redfish/v1/CompositionService/ResourceBlocks"
            "/30303437-3034-4D32-3230-313133364752")

        result = json.loads(response.data.decode("utf-8"))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("application/json", response.mimetype)
        self.assertEqual(expected_resource_block, result)

    @mock.patch.object(resource_block, 'g')
    def test_get_resource_block_computer_system_not_found(self, g):
        error = HPOneViewException({
            'errorCode': 'RESOURCE_NOT_FOUND',
            'message': 'server-hardware not found'
        })
        g.oneview_client.server_hardware.get.side_effect = error

        response = self.app.get(
            "/redfish/v1/CompositionService/ResourceBlocks"
            "/30303437-3034-4D32-3230-313133364752/Systems/2M201136GR")

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertEqual("application/json", response.mimetype)

    @mock.patch.object(resource_block, 'g')
    def test_get_computer_system_not_found(self, g):
        error = HPOneViewException({
            'errorCode': 'RESOURCE_NOT_FOUND',
            'message': 'server-hardware not found'
        })
        g.oneview_client.server_hardware.get.side_effect = error

        response = self.app.get(
            "/redfish/v1/CompositionService/ResourceBlocks"
            "/30303437-3034-4D32-3230-313133364752/Systems/2M201136GR")

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertEqual("application/json", response.mimetype)

    @mock.patch.object(resource_block, 'g')
    def test_get_computer_system_invalid_serial(self, g):
        g.oneview_client.server_hardware.get.return_value = \
            self.server_hardware

        response = self.app.get(
            "/redfish/v1/CompositionService/ResourceBlocks"
            "/30303437-3034-4D32-3230-313133364752/Systems/1234567890")

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertEqual("application/json", response.mimetype)

    @mock.patch.object(resource_block, 'g')
    def test_get_computer_system(self, g):
        with open(
            'oneview_redfish_toolkit/mockups/redfish'
            '/ResourceBlockComputerSystem.json'
        ) as f:
            expected_computer_system = json.load(f)

        g.oneview_client.server_hardware.get.return_value = \
            self.server_hardware

        response = self.app.get(
            "/redfish/v1/CompositionService/ResourceBlocks"
            "/30303437-3034-4D32-3230-313133364752/Systems/2M201136GR")

        result = json.loads(response.data.decode("utf-8"))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("application/json", response.mimetype)
        self.assertEqual(expected_computer_system, result)