#!/usr/bin/env python3
"""
Unit tests for bridge_mcp_ghidra.py

Tests cover:
- BSim integration functions
- Pagination parameters
- Error handling
- Request timeout configuration
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the parent directory to the path to import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Mock the mcp module before importing bridge_mcp_ghidra
mock_mcp = MagicMock()
# Make the tool decorator a pass-through
mock_mcp.tool = lambda: lambda f: f
sys.modules['mcp'] = mock_mcp
sys.modules['mcp.server'] = MagicMock()
sys.modules['mcp.server.fastmcp'] = MagicMock()
sys.modules['mcp.server.fastmcp'].FastMCP = lambda x: mock_mcp

import bridge_mcp_ghidra


class TestBridgeMCPGhidra(unittest.TestCase):
    """Test suite for bridge_mcp_ghidra module"""

    def setUp(self):
        """Set up test fixtures"""
        # Reset global variables
        bridge_mcp_ghidra.ghidra_server_url = bridge_mcp_ghidra.DEFAULT_GHIDRA_SERVER
        bridge_mcp_ghidra.ghidra_request_timeout = bridge_mcp_ghidra.DEFAULT_REQUEST_TIMEOUT

    @patch('bridge_mcp_ghidra.requests.get')
    def test_safe_get_success(self, mock_get):
        """Test safe_get with successful response"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.text = "line1\nline2\nline3"
        mock_response.encoding = 'utf-8'
        mock_get.return_value = mock_response

        result = bridge_mcp_ghidra.safe_get("test_endpoint", {"param": "value"})
        
        self.assertEqual(result, ["line1", "line2", "line3"])
        mock_get.assert_called_once()

    @patch('bridge_mcp_ghidra.requests.get')
    def test_safe_get_error_response(self, mock_get):
        """Test safe_get with error response"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        result = bridge_mcp_ghidra.safe_get("test_endpoint")
        
        self.assertEqual(result, ["Error 404: Not Found"])

    @patch('bridge_mcp_ghidra.requests.get')
    def test_safe_get_exception(self, mock_get):
        """Test safe_get with network exception"""
        mock_get.side_effect = Exception("Connection failed")

        result = bridge_mcp_ghidra.safe_get("test_endpoint")
        
        self.assertEqual(result, ["Request failed: Connection failed"])

    @patch('bridge_mcp_ghidra.requests.post')
    def test_safe_post_success_with_dict(self, mock_post):
        """Test safe_post with dict data"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.text = "Success response"
        mock_response.encoding = 'utf-8'
        mock_post.return_value = mock_response

        result = bridge_mcp_ghidra.safe_post("test_endpoint", {"key": "value"})
        
        self.assertEqual(result, "Success response")
        mock_post.assert_called_once()

    @patch('bridge_mcp_ghidra.requests.post')
    def test_safe_post_success_with_string(self, mock_post):
        """Test safe_post with string data"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.text = "Success response"
        mock_response.encoding = 'utf-8'
        mock_post.return_value = mock_response

        result = bridge_mcp_ghidra.safe_post("test_endpoint", "test_string")
        
        self.assertEqual(result, "Success response")
        mock_post.assert_called_once()

    @patch('bridge_mcp_ghidra.requests.post')
    def test_safe_post_error_response(self, mock_post):
        """Test safe_post with error response"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        result = bridge_mcp_ghidra.safe_post("test_endpoint", {})
        
        self.assertEqual(result, "Error 500: Internal Server Error")

    @patch('bridge_mcp_ghidra.requests.post')
    def test_safe_post_exception(self, mock_post):
        """Test safe_post with network exception"""
        mock_post.side_effect = Exception("Connection timeout")

        result = bridge_mcp_ghidra.safe_post("test_endpoint", {})
        
        self.assertEqual(result, "Request failed: Connection timeout")

    def test_default_values(self):
        """Test default configuration values"""
        self.assertEqual(bridge_mcp_ghidra.DEFAULT_GHIDRA_SERVER, "http://127.0.0.1:8080/")
        self.assertEqual(bridge_mcp_ghidra.DEFAULT_REQUEST_TIMEOUT, 5)

    @patch('bridge_mcp_ghidra.safe_get')
    def test_list_methods_pagination(self, mock_safe_get):
        """Test list_methods with pagination parameters"""
        mock_safe_get.return_value = ["method1", "method2"]
        
        bridge_mcp_ghidra.list_methods(offset=10, limit=50)
        
        mock_safe_get.assert_called_once_with("methods", {"offset": 10, "limit": 50})

    @patch('bridge_mcp_ghidra.safe_post')
    def test_bsim_select_database(self, mock_safe_post):
        """Test BSim database selection"""
        mock_safe_post.return_value = "Connected successfully"
        
        result = bridge_mcp_ghidra.bsim_select_database("/path/to/db.bsim")
        
        mock_safe_post.assert_called_once_with("bsim/select_database", {"database_path": "/path/to/db.bsim"})
        self.assertEqual(result, "Connected successfully")

    @patch('bridge_mcp_ghidra.safe_post')
    def test_bsim_query_function_basic(self, mock_safe_post):
        """Test BSim query function with basic parameters"""
        mock_safe_post.return_value = "Query results"
        
        result = bridge_mcp_ghidra.bsim_query_function(
            function_address="0x401000",
            max_matches=10,
            similarity_threshold=0.7,
            confidence_threshold=0.0
        )
        
        expected_data = {
            "function_address": "0x401000",
            "max_matches": "10",
            "similarity_threshold": "0.7",
            "confidence_threshold": "0.0",
            "offset": "0",
            "limit": "100",
        }
        mock_safe_post.assert_called_once_with("bsim/query_function", expected_data)
        self.assertEqual(result, "Query results")

    @patch('bridge_mcp_ghidra.safe_post')
    def test_bsim_query_function_with_max_filters(self, mock_safe_post):
        """Test BSim query function with max similarity/confidence filters"""
        mock_safe_post.return_value = "Filtered results"
        
        result = bridge_mcp_ghidra.bsim_query_function(
            function_address="0x401000",
            max_matches=5,
            similarity_threshold=0.6,
            confidence_threshold=0.1,
            max_similarity=0.95,
            max_confidence=0.9,
            offset=10,
            limit=20
        )
        
        # Verify that max_similarity and max_confidence are included
        call_args = mock_safe_post.call_args[0][1]
        self.assertIn("max_similarity", call_args)
        self.assertIn("max_confidence", call_args)
        self.assertEqual(call_args["max_similarity"], "0.95")
        self.assertEqual(call_args["max_confidence"], "0.9")
        self.assertEqual(result, "Filtered results")

    @patch('bridge_mcp_ghidra.safe_post')
    def test_bsim_query_all_functions(self, mock_safe_post):
        """Test BSim query all functions"""
        mock_safe_post.return_value = "All functions results"
        
        result = bridge_mcp_ghidra.bsim_query_all_functions(
            max_matches_per_function=5,
            similarity_threshold=0.7,
            confidence_threshold=0.0
        )
        
        expected_data = {
            "max_matches_per_function": "5",
            "similarity_threshold": "0.7",
            "confidence_threshold": "0.0",
            "offset": "0",
            "limit": "100",
        }
        mock_safe_post.assert_called_once_with("bsim/query_all_functions", expected_data)
        self.assertEqual(result, "All functions results")

    @patch('bridge_mcp_ghidra.safe_post')
    def test_bsim_get_match_disassembly(self, mock_safe_post):
        """Test getting disassembly for BSim match"""
        mock_safe_post.return_value = "Disassembly output"
        
        result = bridge_mcp_ghidra.bsim_get_match_disassembly(
            executable_path="/path/to/exe",
            function_name="test_func",
            function_address="0x401000"
        )
        
        expected_data = {
            "executable_path": "/path/to/exe",
            "function_name": "test_func",
            "function_address": "0x401000",
        }
        mock_safe_post.assert_called_once_with("bsim/get_match_disassembly", expected_data)
        self.assertEqual(result, "Disassembly output")

    @patch('bridge_mcp_ghidra.safe_post')
    def test_bsim_get_match_decompile(self, mock_safe_post):
        """Test getting decompilation for BSim match"""
        mock_safe_post.return_value = "Decompiled code"
        
        result = bridge_mcp_ghidra.bsim_get_match_decompile(
            executable_path="/path/to/exe",
            function_name="test_func",
            function_address="0x401000"
        )
        
        expected_data = {
            "executable_path": "/path/to/exe",
            "function_name": "test_func",
            "function_address": "0x401000",
        }
        mock_safe_post.assert_called_once_with("bsim/get_match_decompile", expected_data)
        self.assertEqual(result, "Decompiled code")

    @patch('bridge_mcp_ghidra.safe_post')
    def test_bsim_disconnect(self, mock_safe_post):
        """Test BSim disconnect"""
        mock_safe_post.return_value = "Disconnected"
        
        result = bridge_mcp_ghidra.bsim_disconnect()
        
        mock_safe_post.assert_called_once_with("bsim/disconnect", {})
        self.assertEqual(result, "Disconnected")

    @patch('bridge_mcp_ghidra.safe_get')
    def test_bsim_status(self, mock_safe_get):
        """Test BSim status check"""
        mock_safe_get.return_value = ["Status: Connected", "Database: /path/to/db.bsim"]
        
        result = bridge_mcp_ghidra.bsim_status()
        
        mock_safe_get.assert_called_once_with("bsim/status")
        self.assertEqual(result, "Status: Connected\nDatabase: /path/to/db.bsim")

    @patch('bridge_mcp_ghidra.safe_get')
    def test_search_functions_by_name(self, mock_safe_get):
        """Test searching functions by name with pagination"""
        mock_safe_get.return_value = ["func1", "func2"]
        
        result = bridge_mcp_ghidra.search_functions_by_name("test", offset=5, limit=10)
        
        mock_safe_get.assert_called_once_with("searchFunctions", {"query": "test", "offset": 5, "limit": 10})

    def test_search_functions_by_name_empty_query(self):
        """Test searching functions with empty query"""
        result = bridge_mcp_ghidra.search_functions_by_name("")
        
        self.assertEqual(result, ["Error: query string is required"])

    @patch('bridge_mcp_ghidra.safe_get')
    def test_list_strings_with_filter(self, mock_safe_get):
        """Test listing strings with filter parameter"""
        mock_safe_get.return_value = ["string1", "string2"]
        
        bridge_mcp_ghidra.list_strings(offset=0, limit=100, filter="test")
        
        expected_params = {"offset": 0, "limit": 100, "filter": "test"}
        mock_safe_get.assert_called_once_with("strings", expected_params)

    @patch('bridge_mcp_ghidra.safe_get')
    def test_list_strings_without_filter(self, mock_safe_get):
        """Test listing strings without filter parameter"""
        mock_safe_get.return_value = ["string1", "string2"]
        
        bridge_mcp_ghidra.list_strings(offset=10, limit=50)
        
        expected_params = {"offset": 10, "limit": 50}
        mock_safe_get.assert_called_once_with("strings", expected_params)


class TestConfigurableTimeout(unittest.TestCase):
    """Test suite for configurable timeout functionality"""

    def setUp(self):
        """Reset global configuration"""
        bridge_mcp_ghidra.ghidra_server_url = bridge_mcp_ghidra.DEFAULT_GHIDRA_SERVER
        bridge_mcp_ghidra.ghidra_request_timeout = bridge_mcp_ghidra.DEFAULT_REQUEST_TIMEOUT

    @patch('bridge_mcp_ghidra.requests.get')
    def test_timeout_is_used_in_get_request(self, mock_get):
        """Verify that configured timeout is used in GET requests"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.text = "result"
        mock_response.encoding = 'utf-8'
        mock_get.return_value = mock_response

        # Set custom timeout
        bridge_mcp_ghidra.ghidra_request_timeout = 30

        bridge_mcp_ghidra.safe_get("test")

        # Verify timeout parameter was passed
        call_kwargs = mock_get.call_args[1]
        self.assertEqual(call_kwargs['timeout'], 30)

    @patch('bridge_mcp_ghidra.requests.post')
    def test_timeout_is_used_in_post_request(self, mock_post):
        """Verify that configured timeout is used in POST requests"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.text = "result"
        mock_response.encoding = 'utf-8'
        mock_post.return_value = mock_response

        # Set custom timeout
        bridge_mcp_ghidra.ghidra_request_timeout = 45

        bridge_mcp_ghidra.safe_post("test", {})

        # Verify timeout parameter was passed
        call_kwargs = mock_post.call_args[1]
        self.assertEqual(call_kwargs['timeout'], 45)


if __name__ == '__main__':
    unittest.main()
