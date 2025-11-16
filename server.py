"""
HomeSeer MCP Server - Object-oriented implementation.

This module provides a FastMCP server for controlling HomeSeer smart home devices.
"""

from typing import Optional, List, Dict, Any
from fastmcp.server import FastMCP
import requests
import logging
from config import HomeSeerConfig, get_config


class HomeSeerAPIClient:
    """
    Client for interacting with the HomeSeer JSON API.
    
    This class encapsulates all HTTP communication with the HomeSeer system,
    providing a clean interface for device operations.
    """
    
    # Device relationship types
    RELATIONSHIP_ROOT = 2  # Root device (other devices may be part of this physical device)
    RELATIONSHIP_STANDALONE = 3  # Standalone device (only device representing this physical device)
    RELATIONSHIP_CHILD = 4  # Child device (part of a group of devices representing this physical device)
    
    def __init__(self, config: HomeSeerConfig):
        """
        Initialize the HomeSeer API client.
        
        Args:
            config: HomeSeerConfig object with API connection details
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"HomeSeer API Client initialized for: {config.url}")
    
    def _make_request(self, **params) -> Dict[str, Any]:
        """
        Make an HTTP request to the HomeSeer API.
        
        Args:
            **params: Additional parameters for the API request
            
        Returns:
            JSON response as a dictionary
            
        Raises:
            requests.HTTPError: If the HTTP request fails
            requests.RequestException: For other request-related errors
        """
        request_params = self.config.get_request_params(**params)
        
        self.logger.debug(f"Making request to {self.config.base_url} with params: {list(params.keys())}")
        
        response = requests.get(
            self.config.base_url,
            params=request_params,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl
        )
        
        response.raise_for_status()
        self.logger.info(f"Response status: {response.status_code}")
        self.logger.debug(f"Response: {response.text[:200]}...")  # Log first 200 chars
        
        return response.json()
    
    def get_all_devices(self) -> List[Dict[str, Any]]:
        """
        Retrieve all devices from HomeSeer.
        
        Returns:
            List of device dictionaries
        """
        data = self._make_request(request="getstatus")
        return data.get("Devices", [])
    
    def get_device_by_ref(self, device_ref: str) -> Dict[str, Any]:
        """
        Get a specific device by its reference ID.
        
        Args:
            device_ref: The device reference ID
            
        Returns:
            Device information dictionary
            
        Raises:
            IndexError: If device not found
        """
        data = self._make_request(request="getstatus", ref=device_ref)
        devices = data.get("Devices", [])
        
        if not devices:
            raise ValueError(f"Device with ref {device_ref} not found")
        
        return devices[0]
    
    def set_device_status(self, device_ref: int, value: int) -> bool:
        """
        Set the status/value of a device.
        
        Args:
            device_ref: The device reference ID
            value: The value/control ID to set
            
        Returns:
            True if successful
        """
        self._make_request(
            request="setdevicestatus",
            ref=device_ref,
            value=value
        )
        return True
    
    def control_device_by_label(self, device_ref: int, label: str) -> bool:
        """
        Control a device using a label/command string.
        
        Args:
            device_ref: The device reference ID
            label: The control label (e.g., "On", "Off", "Dim 50%")
            
        Returns:
            True if successful
        """
        self._make_request(
            request="controldevicebylabel",
            ref=device_ref,
            label=label
        )
        return True


class HomeSeerMCPServer:
    """
    MCP Server for HomeSeer device control.
    
    This class wraps the FastMCP server and provides MCP tools for
    interacting with HomeSeer devices.
    """
    
    def __init__(self, config: Optional[HomeSeerConfig] = None):
        """
        Initialize the HomeSeer MCP server.
        
        Args:
            config: Optional HomeSeerConfig. If None, loads from default sources.
        """
        self.config = config or get_config()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.client = HomeSeerAPIClient(self.config)
        self.mcp = FastMCP(name="homeseer-mcp")
        
        # Register MCP tools using bound methods (recommended FastMCP pattern)
        self._register_tools()
        
        self.logger.info(f"HomeSeer MCP Server initialized with URL: {self.config.url}")
    
    def _register_tools(self) -> None:
        """
        Register all MCP tools with the FastMCP server.
        
        Uses the recommended FastMCP pattern of registering bound instance methods.
        This automatically binds 'self' so it doesn't appear as a parameter to the LLM.
        """
        # Register bound methods directly - FastMCP will use the method's docstring
        self.mcp.tool(self.list_all_devices)
        self.mcp.tool(self.get_device_info)
        self.mcp.tool(self.control_homeseer_device)
        self.mcp.tool(self.control_homeseer_device_by_label)
    
    def list_all_devices(
        self,
        free_text_search: Optional[str] = None,
        need_room_information: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List all HomeSeer devices with optional filtering.
        
        Args:
            free_text_search: Optional text to filter device names
            need_room_information: Include location information
            
        Returns:
            List of device dictionaries
        """
        devices = self.client.get_all_devices()
        
        # Apply text filter if provided
        if free_text_search:
            search_lower = free_text_search.lower()
            devices = [
                device for device in devices
                if search_lower in device.get("name", "").lower()
            ]
        
        # Format output based on requirements
        if need_room_information:
            result = [
                {
                    "ref": device["ref"],
                    "name": device["name"],
                    "location": device.get("location", ""),
                    "location2": device.get("location2", ""),
                }
                for device in devices
            ]
        else:
            result = [
                {
                    "ref": device["ref"],
                    "name": device["name"]
                }
                for device in devices
            ]
        
        self.logger.info(f"Listed {len(result)} devices (filtered from {len(devices)})")
        return result
    
    def get_device_info(self, device_ref: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific HomeSeer device.
        
        Args:
            device_ref: The device reference ID
            
        Returns:
            Dictionary with device details
        """
        device = self.client.get_device_by_ref(device_ref)
        
        return {
            "name": device.get("name"),
            "location": device.get("location"),
            "location2": device.get("location2"),
            "value": device.get("value"),
            "status": device.get("status"),
            "associated_devices": device.get("associated_devices"),
        }
    
    def control_homeseer_device(self, device_id: int, control_id: int) -> bool:
        """
        Control a HomeSeer device by device ID and control ID.
        
        Args:
            device_id: The device reference ID
            control_id: The control/value ID to set
            
        Returns:
            True if successful
        """
        result = self.client.set_device_status(device_id, control_id)
        self.logger.info(f"Controlled device {device_id} with value {control_id}")
        return result
    
    def control_homeseer_device_by_label(self, device_ref: int, label: str) -> bool:
        """
        Control a device using a label string.
        
        Args:
            device_ref: The device reference ID
            label: The control label
            
        Returns:
            True if successful
        """
        result = self.client.control_device_by_label(device_ref, label)
        self.logger.info(f"Controlled device {device_ref} with label '{label}'")
        return result
    
    def run(self) -> None:
        """Start the MCP server."""
        self.logger.info("Starting HomeSeer MCP Server...")
        self.mcp.run()


def main() -> None:
    """Main entry point for the HomeSeer MCP server."""
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run server
    server = HomeSeerMCPServer()
    server.run()


if __name__ == "__main__":
    main()
