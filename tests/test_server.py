"""
Unit tests for HomeSeer MCP Server and API Client.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import requests
from server import HomeSeerAPIClient, HomeSeerMCPServer
from config import HomeSeerConfig


class TestHomeSeerAPIClient:
    def test_get_control(self, client):
        """Test getting ControlPairs for a device."""
        mock_controls = [
            {"label": "On", "value": 255},
            {"label": "Off", "value": 0}
        ]
        mock_response = {"ControlPairs": mock_controls}
        with patch.object(client, '_make_request', return_value=mock_response):
            result = client.get_control(123)
            assert result == mock_controls
            client._make_request.assert_called_once_with(request="getcontrol", ref=123)

    def test_get_control_empty(self, client):
        """Test getting ControlPairs when none exist."""
        mock_response = {"ControlPairs": []}
        with patch.object(client, '_make_request', return_value=mock_response):
            result = client.get_control(123)
            assert result == []
    
    def test_get_events_success(self, client):
        """Test getting all events."""
        mock_events = [
            {"Group": "Lighting", "Name": "Outside Lights Off", "id": 1, "voice_command": "", "voice_command_enabled": False},
            {"Group": "Lighting", "Name": "Kitchen Lights On", "id": 2, "voice_command": "", "voice_command_enabled": False},
            {"Group": "Climate", "Name": "Set Thermostat", "id": 3, "voice_command": "", "voice_command_enabled": False}
        ]
        mock_response = {"Name": "HomeSeer Events", "Version": "1.0", "Events": mock_events}
        
        with patch.object(client, '_make_request', return_value=mock_response):
            result = client.get_events()
            
            assert result == mock_response
            assert result["Events"] == mock_events
            assert result["Name"] == "HomeSeer Events"
            assert result["Version"] == "1.0"
            client._make_request.assert_called_once_with(request="getevents")
    
    def test_get_events_empty(self, client):
        """Test getting events when none exist."""
        mock_response = {"Name": "HomeSeer Events", "Version": "1.0", "Events": []}
        
        with patch.object(client, '_make_request', return_value=mock_response):
            result = client.get_events()
            assert result["Events"] == []
            assert result["Name"] == "HomeSeer Events"
    
    def test_run_event_by_id(self, client):
        """Test running an event by ID."""
        mock_response = {"status": "ok"}
        
        with patch.object(client, '_make_request', return_value=mock_response):
            result = client.run_event(event_id=5)
            
            assert result is True
            client._make_request.assert_called_once_with(request="runevent", id=5)
    
    def test_run_event_by_group_and_name(self, client):
        """Test running an event by group and name."""
        mock_response = {"status": "ok"}
        
        with patch.object(client, '_make_request', return_value=mock_response):
            result = client.run_event(group="Lighting", name="Outside Lights Off")
            
            assert result is True
            client._make_request.assert_called_once_with(
                request="runevent", 
                group="Lighting", 
                name="Outside Lights Off"
            )
    
    def test_run_event_missing_parameters(self, client):
        """Test running an event without required parameters."""
        with pytest.raises(ValueError, match="Must provide either event_id OR both group and name"):
            client.run_event()
    
    def test_run_event_partial_parameters(self, client):
        """Test running an event with only group or only name."""
        with pytest.raises(ValueError, match="Must provide either event_id OR both group and name"):
            client.run_event(group="Lighting")
        
        with pytest.raises(ValueError, match="Must provide either event_id OR both group and name"):
            client.run_event(name="Outside Lights Off")
    """Tests for HomeSeerAPIClient class."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return HomeSeerConfig(
            url="https://test.homeseer.com/json",
            username="testuser",
            password="testpass",
            source="test-mcp",
            timeout=10,
            verify_ssl=True
        )
    
    @pytest.fixture
    def client(self, config):
        """Create a test client."""
        return HomeSeerAPIClient(config)
    
    def test_initialization(self, client, config):
        """Test client initialization."""
        assert client.config == config
        assert client.logger is not None
    
    def test_make_request_success(self, client):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"status": "ok", "data": "test"}'
        mock_response.json.return_value = {"status": "ok", "data": "test"}
        
        with patch('requests.get', return_value=mock_response) as mock_get:
            result = client._make_request(request="getstatus")
            
            # Verify request was made correctly
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args[1]
            assert call_kwargs['timeout'] == 10
            assert call_kwargs['verify'] is True
            assert 'params' in call_kwargs
            
            # Verify result
            assert result == {"status": "ok", "data": "test"}
    
    def test_make_request_with_params(self, client):
        """Test API request with additional parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"result": "success"}'
        mock_response.json.return_value = {"result": "success"}
        
        with patch('requests.get', return_value=mock_response) as mock_get:
            client._make_request(request="getstatus", ref=123)
            
            # Check that params include authentication and custom params
            call_kwargs = mock_get.call_args[1]
            params = call_kwargs['params']
            assert params['request'] == "getstatus"
            assert params['ref'] == 123
            assert params['user'] == "testuser"
            assert params['pass'] == "testpass"
            assert params['source'] == "test-mcp"
    
    def test_make_request_http_error(self, client):
        """Test API request with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("Server Error")
        
        with patch('requests.get', return_value=mock_response):
            with pytest.raises(requests.HTTPError):
                client._make_request(request="getstatus")
    
    def test_make_request_timeout(self, client):
        """Test API request timeout."""
        with patch('requests.get', side_effect=requests.Timeout("Request timed out")):
            with pytest.raises(requests.Timeout):
                client._make_request(request="getstatus")
    
    def test_get_all_devices(self, client):
        """Test getting all devices."""
        mock_devices = [
            {"ref": 1, "name": "Device 1"},
            {"ref": 2, "name": "Device 2"}
        ]
        mock_response = {"Devices": mock_devices}
        
        with patch.object(client, '_make_request', return_value=mock_response):
            result = client.get_all_devices()
            
            assert result == mock_devices
            client._make_request.assert_called_once_with(request="getstatus")
    
    def test_get_all_devices_empty(self, client):
        """Test getting all devices when none exist."""
        mock_response = {"Devices": []}
        
        with patch.object(client, '_make_request', return_value=mock_response):
            result = client.get_all_devices()
            assert result == []
    
    def test_get_device_by_ref_success(self, client):
        """Test getting a specific device by reference."""
        mock_device = {
            "ref": 123,
            "name": "Test Device",
            "location": "Living Room",
            "value": 100,
            "status": "On"
        }
        mock_response = {"Devices": [mock_device]}
        
        with patch.object(client, '_make_request', return_value=mock_response):
            result = client.get_device_by_ref("123")
            
            assert result == mock_device
            client._make_request.assert_called_once_with(request="getstatus", ref="123")
    
    def test_get_device_by_ref_not_found(self, client):
        """Test getting a device that doesn't exist."""
        mock_response = {"Devices": []}
        
        with patch.object(client, '_make_request', return_value=mock_response):
            with pytest.raises(ValueError, match="Device with ref 999 not found"):
                client.get_device_by_ref("999")
    
    def test_set_device_status(self, client):
        """Test setting device status."""
        mock_response = {"status": "ok"}
        
        with patch.object(client, '_make_request', return_value=mock_response):
            result = client.set_device_status(device_ref=123, value=50)
            
            assert result is True
            client._make_request.assert_called_once_with(
                request="setdevicestatus",
                ref=123,
                value=50
            )
    
    def test_control_device_by_label(self, client):
        """Test controlling device by label."""
        mock_response = {"status": "ok"}
        
        with patch.object(client, '_make_request', return_value=mock_response):
            result = client.control_device_by_label(device_ref=123, label="On")
            
            assert result is True
            client._make_request.assert_called_once_with(
                request="controldevicebylabel",
                ref=123,
                label="On"
            )
    
    def test_relationship_constants(self):
        """Test device relationship constants."""
        assert HomeSeerAPIClient.RELATIONSHIP_ROOT == 2
        assert HomeSeerAPIClient.RELATIONSHIP_STANDALONE == 3
        assert HomeSeerAPIClient.RELATIONSHIP_CHILD == 4


class TestHomeSeerMCPServer:
    def test_get_control(self, server, mock_client):
        """Test MCPServer get_control tool."""
        mock_controls = [
            {"label": "On", "value": 255},
            {"label": "Off", "value": 0}
        ]
        mock_client.get_control.return_value = mock_controls
        result = server.get_control(123)
        assert result == mock_controls
        mock_client.get_control.assert_called_once_with(123)

    def test_get_control_empty(self, server, mock_client):
        """Test MCPServer get_control tool with no controls."""
        mock_client.get_control.return_value = []
        result = server.get_control(123)
        assert result == []
        mock_client.get_control.assert_called_once_with(123)
    
    def test_get_events_no_filter(self, server, mock_client):
        """Test MCPServer get_events tool without filter."""
        mock_events_data = {
            "Name": "HomeSeer Events",
            "Version": "1.0",
            "Events": [
                {"Group": "Lighting", "Name": "Outside Lights Off", "id": 10, "voice_command": "", "voice_command_enabled": False},
                {"Group": "Lighting", "Name": "Kitchen Lights On", "id": 20, "voice_command": "", "voice_command_enabled": False},
                {"Group": "Climate", "Name": "Set Thermostat", "id": 30, "voice_command": "", "voice_command_enabled": False}
            ]
        }
        mock_client.get_events.return_value = mock_events_data
        
        result = server.get_events()
        
        assert len(result) == 3
        assert result[0]["Group"] == "Lighting"
        assert result[0]["Name"] == "Outside Lights Off"
        assert result[1]["Group"] == "Lighting"
        assert result[2]["Group"] == "Climate"
        mock_client.get_events.assert_called_once()
    
    def test_get_events_with_name_filter(self, server, mock_client):
        """Test MCPServer get_events tool with name filter."""
        mock_events_data = {
            "Name": "HomeSeer Events",
            "Version": "1.0",
            "Events": [
                {"Group": "Lighting", "Name": "Outside Lights Off", "id": 10, "voice_command": "", "voice_command_enabled": False},
                {"Group": "Lighting", "Name": "Kitchen Lights On", "id": 20, "voice_command": "", "voice_command_enabled": False},
                {"Group": "Climate", "Name": "Set Thermostat", "id": 30, "voice_command": "", "voice_command_enabled": False}
            ]
        }
        mock_client.get_events.return_value = mock_events_data
        
        result = server.get_events(free_text_search="kitchen")
        
        assert len(result) == 1
        assert result[0]["Name"] == "Kitchen Lights On"
        mock_client.get_events.assert_called_once()
    
    def test_get_events_with_group_filter(self, server, mock_client):
        """Test MCPServer get_events tool with group filter."""
        mock_events_data = {
            "Name": "HomeSeer Events",
            "Version": "1.0",
            "Events": [
                {"Group": "Lighting", "Name": "Outside Lights Off", "id": 10, "voice_command": "", "voice_command_enabled": False},
                {"Group": "Lighting", "Name": "Kitchen Lights On", "id": 20, "voice_command": "", "voice_command_enabled": False},
                {"Group": "Climate", "Name": "Set Thermostat", "id": 30, "voice_command": "", "voice_command_enabled": False}
            ]
        }
        mock_client.get_events.return_value = mock_events_data
        
        result = server.get_events(free_text_search="lighting")
        
        assert len(result) == 2
        assert all(event["Group"] == "Lighting" for event in result)
        mock_client.get_events.assert_called_once()
    
    def test_get_events_case_insensitive_filter(self, server, mock_client):
        """Test MCPServer get_events tool with case-insensitive filter."""
        mock_events_data = {
            "Name": "HomeSeer Events",
            "Version": "1.0",
            "Events": [
                {"Group": "Lighting", "Name": "Outside Lights Off", "id": 10, "voice_command": "", "voice_command_enabled": False},
                {"Group": "Climate", "Name": "Set Thermostat", "id": 30, "voice_command": "", "voice_command_enabled": False}
            ]
        }
        mock_client.get_events.return_value = mock_events_data
        
        result = server.get_events(free_text_search="LIGHTS")
        
        assert len(result) == 1
        assert result[0]["Name"] == "Outside Lights Off"
    
    def test_get_events_no_matches(self, server, mock_client):
        """Test MCPServer get_events tool with filter that matches nothing."""
        mock_events_data = {
            "Name": "HomeSeer Events",
            "Version": "1.0",
            "Events": [
                {"Group": "Lighting", "Name": "Outside Lights Off", "id": 10, "voice_command": "", "voice_command_enabled": False}
            ]
        }
        mock_client.get_events.return_value = mock_events_data
        
        result = server.get_events(free_text_search="nonexistent")
        
        assert len(result) == 0
        mock_client.get_events.assert_called_once()
    
    def test_get_events_empty(self, server, mock_client):
        """Test MCPServer get_events tool when no events exist."""
        mock_events_data = {
            "Name": "HomeSeer Events",
            "Version": "1.0",
            "Events": []
        }
        mock_client.get_events.return_value = mock_events_data
        
        result = server.get_events()
        
        assert len(result) == 0
        mock_client.get_events.assert_called_once()
    
    def test_run_event_by_id(self, server, mock_client):
        """Test MCPServer run_event tool with event ID."""
        mock_client.run_event.return_value = True
        
        result = server.run_event(event_id=10)
        
        assert result is True
        mock_client.run_event.assert_called_once_with(group=None, name=None, event_id=10)
    
    def test_run_event_by_group_and_name(self, server, mock_client):
        """Test MCPServer run_event tool with group and name."""
        mock_client.run_event.return_value = True
        
        result = server.run_event(group="Lighting", name="Kitchen Lights On")
        
        assert result is True
        mock_client.run_event.assert_called_once_with(
            group="Lighting", 
            name="Kitchen Lights On", 
            event_id=None
        )
    
    def test_run_event_case_insensitive(self, server, mock_client):
        """Test that run_event passes through case-insensitive parameters."""
        mock_client.run_event.return_value = True
        
        result = server.run_event(group="LIGHTING", name="outside lights off")
        
        assert result is True
        # Verify the parameters are passed as-is (HomeSeer API handles case-insensitivity)
        mock_client.run_event.assert_called_once_with(
            group="LIGHTING",
            name="outside lights off",
            event_id=None
        )
    """Tests for HomeSeerMCPServer class."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return HomeSeerConfig(
            url="https://test.homeseer.com/json",
            token="test-token-123",
            source="test-mcp"
        )
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock API client."""
        return Mock(spec=HomeSeerAPIClient)
    
    @pytest.fixture
    def server(self, config, mock_client):
        """Create a test server with mocked client."""
        with patch('server.HomeSeerAPIClient', return_value=mock_client):
            with patch('server.FastMCP'):
                server = HomeSeerMCPServer(config)
                server.client = mock_client
                return server
    
    def test_initialization(self, config):
        """Test server initialization."""
        with patch('server.HomeSeerAPIClient') as mock_api_client:
            with patch('server.FastMCP') as mock_fastmcp:
                server = HomeSeerMCPServer(config)
                
                assert server.config == config
                assert server.logger is not None
                mock_api_client.assert_called_once_with(config)
                mock_fastmcp.assert_called_once_with(name="homeseer-mcp")
    
    def test_initialization_with_default_config(self):
        """Test server initialization with default config."""
        with patch('server.get_config') as mock_get_config:
            with patch('server.HomeSeerAPIClient'):
                with patch('server.FastMCP'):
                    mock_config = HomeSeerConfig()
                    mock_get_config.return_value = mock_config
                    
                    server = HomeSeerMCPServer()
                    
                    mock_get_config.assert_called_once()
                    assert server.config == mock_config
    
    def test_list_devices_no_filter(self, server, mock_client):
        """Test listing all devices without filter."""
        mock_devices = [
            {"ref": 1, "name": "Device 1", "location": "Room 1"},
            {"ref": 2, "name": "Device 2", "location": "Room 2"}
        ]
        mock_client.get_all_devices.return_value = mock_devices
        
        result = server.list_all_devices()
        
        assert len(result) == 2
        assert result[0] == {"ref": 1, "name": "Device 1"}
        assert result[1] == {"ref": 2, "name": "Device 2"}
        mock_client.get_all_devices.assert_called_once()
    
    def test_list_devices_with_text_filter(self, server, mock_client):
        """Test listing devices with text filter."""
        mock_devices = [
            {"ref": 1, "name": "Living Room Light", "location": "Living Room"},
            {"ref": 2, "name": "Bedroom Light", "location": "Bedroom"},
            {"ref": 3, "name": "Living Room Shutter", "location": "Living Room"}
        ]
        mock_client.get_all_devices.return_value = mock_devices
        
        result = server.list_all_devices(free_text_search="living")
        
        assert len(result) == 2
        assert result[0]["name"] == "Living Room Light"
        assert result[1]["name"] == "Living Room Shutter"
    
    def test_list_devices_with_room_information(self, server, mock_client):
        """Test listing devices with room information."""
        mock_devices = [
            {"ref": 1, "name": "Device 1", "location": "Room 1", "location2": "Floor 1"},
            {"ref": 2, "name": "Device 2", "location": "Room 2", "location2": "Floor 2"}
        ]
        mock_client.get_all_devices.return_value = mock_devices
        
        result = server.list_all_devices(need_room_information=True)
        
        assert len(result) == 2
        assert result[0] == {
            "ref": 1,
            "name": "Device 1",
            "location": "Room 1",
            "location2": "Floor 1"
        }
        assert result[1] == {
            "ref": 2,
            "name": "Device 2",
            "location": "Room 2",
            "location2": "Floor 2"
        }
    
    def test_list_devices_case_insensitive_filter(self, server, mock_client):
        """Test that text filter is case-insensitive."""
        mock_devices = [
            {"ref": 1, "name": "BEDROOM Light"},
            {"ref": 2, "name": "bedroom Fan"},
            {"ref": 3, "name": "BedRoom Shutter"}
        ]
        mock_client.get_all_devices.return_value = mock_devices
        
        result = server.list_all_devices(free_text_search="bedroom")
        
        assert len(result) == 3
    
    def test_get_device_details(self, server, mock_client):
        """Test getting device details."""
        mock_device = {
            "ref": 123,
            "name": "Test Device",
            "location": "Living Room",
            "location2": "First Floor",
            "value": 100,
            "status": "On",
            "associated_devices": [124, 125]
        }
        mock_client.get_device_by_ref.return_value = mock_device
        
        result = server.get_device_info("123")
        
        assert result == {
            "name": "Test Device",
            "location": "Living Room",
            "location2": "First Floor",
            "value": 100,
            "status": "On",
            "associated_devices": [124, 125]
        }
        mock_client.get_device_by_ref.assert_called_once_with("123")
    
    def test_get_device_details_missing_fields(self, server, mock_client):
        """Test getting device details with missing optional fields."""
        mock_device = {
            "ref": 123,
            "name": "Test Device"
        }
        mock_client.get_device_by_ref.return_value = mock_device
        
        result = server.get_device_info("123")
        
        assert result["name"] == "Test Device"
        assert result["location"] is None
        assert result["value"] is None
    
    def test_control_device(self, server, mock_client):
        """Test controlling a device."""
        mock_client.set_device_status.return_value = True
        
        result = server.control_homeseer_device(device_id=123, control_id=50)
        
        assert result is True
        mock_client.set_device_status.assert_called_once_with(123, 50)
    
    def test_control_device_by_label(self, server, mock_client):
        """Test controlling a device by label."""
        mock_client.control_device_by_label.return_value = True
        
        result = server.control_homeseer_device_by_label(device_ref=123, label="Off")
        
        assert result is True
        mock_client.control_device_by_label.assert_called_once_with(123, "Off")
    
    def test_control_device_with_various_labels(self, server, mock_client):
        """Test controlling devices with various labels."""
        mock_client.control_device_by_label.return_value = True
        
        labels = ["On", "Off", "Close", "Open"]
        for label in labels:
            result = server.control_homeseer_device_by_label(device_ref=100, label=label)
            assert result is True
        
        assert mock_client.control_device_by_label.call_count == len(labels)
    
    def test_register_tools_called(self, config):
        """Test that tools are registered during initialization."""
        with patch('server.HomeSeerAPIClient'):
            with patch('server.FastMCP') as mock_fastmcp:
                mock_mcp_instance = MagicMock()
                mock_fastmcp.return_value = mock_mcp_instance
                
                server = HomeSeerMCPServer(config)
                
                # Verify that tool decorator was called multiple times
                assert mock_mcp_instance.tool.call_count >= 4
    
    def test_run_calls_mcp_run(self, server):
        """Test that run method calls mcp.run()."""
        server.mcp = Mock()
        server.run()
        server.mcp.run.assert_called_once()
    
    def test_server_get_control(self, config):
        """Test for get_control API call."""
        mock_controls = [
            {"label": "On", "value": 255},
            {"label": "Off", "value": 0}
        ]
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"ControlPairs": []}'
            mock_response.json.return_value = {"ControlPairs": mock_controls}
            mock_get.return_value = mock_response
            with patch('server.FastMCP'):
                server = HomeSeerMCPServer(config)
                result = server.get_control(123)
                assert result == mock_controls
                call_kwargs = mock_get.call_args[1]
                params = call_kwargs['params']
                assert params['request'] == 'getcontrol'
                assert params['ref'] == 123
    
    def test_server_uses_client_for_device_operations(self, config):
        """Test that server properly uses client for device operations."""
        mock_devices_response = [
            {"ref": 1, "name": "Test Device 1"},
            {"ref": 2, "name": "Test Device 2"}
        ]
        
        with patch('requests.get') as mock_get:
            # Setup mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"Devices": []}'
            mock_response.json.return_value = {"Devices": mock_devices_response}
            mock_get.return_value = mock_response
            
            with patch('server.FastMCP'):
                # Create server (which creates client internally)
                server = HomeSeerMCPServer(config)
                
                # Use server to list devices
                result = server.list_all_devices()
                
                # Verify result
                assert len(result) == 2
                assert result[0]["ref"] == 1
                
                # Verify HTTP request was made
                mock_get.assert_called()
    
    def test_end_to_end_device_control(self, config):
        """Test end-to-end device control flow."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"status": "ok"}'
            mock_response.json.return_value = {"status": "ok"}
            mock_get.return_value = mock_response
            
            with patch('server.FastMCP'):
                server = HomeSeerMCPServer(config)
                
                # Control device by label
                result = server.control_homeseer_device_by_label(device_ref=100, label="Close")
                
                assert result is True
                
                # Verify the request was made with correct parameters
                call_kwargs = mock_get.call_args[1]
                params = call_kwargs['params']
                assert params['request'] == 'controldevicebylabel'
                assert params['ref'] == 100
                assert params['label'] == 'Close'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
