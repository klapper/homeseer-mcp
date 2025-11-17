# HomeSeer MCP Server

A Model Context Protocol (MCP) server for controlling HomeSeer smart home devices with support for both local and cloud instances.

## Features

- Control HomeSeer devices via MCP protocol
- List and search devices with filtering
- Retrieve and filter HomeSeer events (automation actions)
- Execute HomeSeer events (trigger automations)
- Get available device controls
- Simple local network access (no authentication needed)
- Username/password authentication for remote access
- Configuration via JSON file or environment variables
- Support for both local and cloud HomeSeer instances
- Comprehensive test suite

## Quick Start

### 1. Installation

```bash
# Create and activate virtual environment
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Enable Local Network Access (Recommended)

**For Local Same-Subnet Access (Simplest):**
1. In HomeSeer, go to **Setup > Network**
2. Enable "No Password Required for Local (same subnet) Login"
3. That's it! No credentials needed when accessing from the same network

**For Remote/Cloud Access:**
- You'll need your HomeSeer username and password
- Used for accessing HomeSeer over the internet or from different networks

### 3. Configure Connection

**Option A: JSON Configuration File (Recommended for Development)**

```bash
# Copy example configuration
cp config.json.example config.json
```

Edit `config.json` with your settings:

For local same-subnet access (simplest - no credentials needed):
```json
{
  "url": "http://192.168.1.100/JSON",
  "verify_ssl": false
}
```

For remote/cloud access with username and password:
```json
{
  "url": "https://connected2.homeseer.com/json",
  "username": "your-username",
  "password": "your-password"
}
```

**Option B: Environment Variables (Recommended for Production)**

```powershell
# Windows PowerShell
$env:HOMESEER_URL = "http://192.168.1.100/JSON"
$env:HOMESEER_VERIFY_SSL = "false"
```

```bash
# Linux/macOS
export HOMESEER_URL="http://192.168.1.100/JSON"
export HOMESEER_VERIFY_SSL="false"
```


### 4. Run the Server

```bash
python server.py
```

Or use the VS Code task: "Run MCP Server"

## Configuration

### Configuration Methods

The server supports two configuration methods with the following precedence:
1. Default values (hardcoded)
2. JSON configuration file (`config.json`)
3. Environment variables (highest precedence - overrides file values)

### Configuration Options

| Option | Environment Variable | Description | Default |
|--------|---------------------|-------------|---------|
| `url` | `HOMESEER_URL` | HomeSeer API endpoint | `https://connected2.homeseer.com/json` |
| `username` | `HOMESEER_USERNAME` | Username (for remote access) | None |
| `password` | `HOMESEER_PASSWORD` | Password (for remote access) | None |
| `source` | `HOMESEER_SOURCE` | Request identifier | `homeseer-mcp` |
| `timeout` | `HOMESEER_TIMEOUT` | Request timeout (seconds) | `30` |
| `verify_ssl` | `HOMESEER_VERIFY_SSL` | Enable SSL verification | `true` |

**Note:** For local same-subnet access with "No Password Required" enabled, you don't need username/password.

### Common Configuration Scenarios

**Local HomeSeer Instance (Simplest - No Authentication Required):**

If you have enabled "No Password Required for Local (same subnet) Login" in HomeSeer's **Setup > Network** menu, you only need to specify the IP address:

```json
{
  "url": "http://192.168.1.100/JSON",
  "verify_ssl": false
}
```

No `username` or `password` needed! This is the simplest setup for local access.

**Remote/Cloud HomeSeer with Username/Password:**
```json
{
  "url": "https://connected2.homeseer.com/json",
  "username": "your-username",
  "password": "your-password"
}
```

**Environment Variables Only (No config.json needed):**
```powershell
# Local access
$env:HOMESEER_URL = "http://192.168.1.100/JSON"
$env:HOMESEER_VERIFY_SSL = "false"

# Or for remote access
$env:HOMESEER_URL = "https://connected2.homeseer.com/json"
$env:HOMESEER_USERNAME = "your-username"
$env:HOMESEER_PASSWORD = "your-password"
```

## Available MCP Tools

The server exposes the following MCP tools:

### Device Management
- **`list_all_devices`** - List all HomeSeer devices with optional filtering and room information
  - Parameters:
    - `free_text_search` (optional): Filter devices by name
    - `need_room_information` (optional): Include location details
  - Returns: List of devices with ref, name, and optionally location fields

- **`get_device_info`** - Get detailed information about a specific device by reference ID
  - Parameters:
    - `device_ref`: The device reference ID
  - Returns: Detailed device information including name, location, value, status, and associated devices

- **`get_control`** - Get the list of available controls for a device
  - Parameters:
    - `device_ref`: The device reference ID
  - Returns: List of control options with labels, values, and control types

### Device Control
- **`control_homeseer_device`** - Control a device using device ID and control ID
  - Parameters:
    - `device_id`: The device reference ID
    - `control_id`: The control/value ID to set
  - Returns: True if successful

- **`control_homeseer_device_by_label`** - Control a device using a human-readable label
  - Parameters:
    - `device_ref`: The device reference ID
    - `label`: The control label (e.g., "On", "Off", "Close")
  - Returns: True if successful

### Event Management
- **`get_events`** - Get all HomeSeer events with optional filtering
  - An event is an action to be performed such as controlling a light, a sequence of lights, a thermostat, etc.
  - Events have two properties: a group name and an event name
  - Parameters:
    - `free_text_search` (optional): Filter events by name or group (case-insensitive)
  - Returns: List of events, each containing:
    - `Group`: The event group name (e.g., "Lighting", "Climate")
    - `Name`: The event name (e.g., "Outside Lights Off")
    - `id`: The unique event identifier
    - Additional fields: `voice_command`, `voice_command_enabled`
  - Example usage:
    - `get_events()` - Get all events
    - `get_events(free_text_search="lighting")` - Get all lighting-related events
    - `get_events(free_text_search="kitchen")` - Get events with "kitchen" in name or group

- **`run_event`** - Execute a HomeSeer event by group/name or event ID
  - Triggers an automation action such as controlling lights, thermostats, or running sequences
  - Parameters:
    - `group`: Event group name (required if using name, not case-sensitive)
    - `name`: Event name (required if using group, not case-sensitive)
    - `event_id`: Event ID (alternative to group/name)
  - Returns: True if successful
  - Note: Must provide either `event_id` OR both `group` and `name`
  - Example usage:
    - `run_event(group="Lighting", name="Outside Lights Off")` - Run event by name
    - `run_event(event_id=5)` - Run event by ID
    - `run_event(group="Window Shutters", name="All house window shutters close")` - Execute shutter event

## Testing

### Quick Test: List Your Devices

```python
from config import get_config
import requests

config = get_config()
print(f"Connecting to: {config.base_url}")

params = config.get_request_params(request="getstatus")
response = requests.get(
    config.base_url,
    params=params,
    timeout=config.timeout,
    verify=config.verify_ssl
)

print(f"Status: {response.status_code}")
if response.ok:
    data = response.json()
    print(f"Found {len(data.get('Devices', []))} devices")
```

### Run Test Suite

Use the platform-specific test runner:

```powershell
# Windows PowerShell
.\test.ps1
```

```cmd
# Windows Command Prompt
test.bat
```

```bash
# Linux/macOS
./test.sh
```

Or run pytest directly:
```bash
# Run all tests
pytest tests/

# Verbose output
pytest tests/ -v

# With coverage report
pytest tests/ --cov=. --cov-report=html
```

The test suite includes:
- API client tests
- MCP server tests
- Configuration management tests

## Security Best Practices

1. **Never commit `config.json` with real credentials**
   - The file is already in `.gitignore`
   - Use `config.json.example` as a template

2. **Use local same-subnet access when possible**
   - Simplest setup with no credentials required
   - Enable "No Password Required for Local (same subnet) Login" in HomeSeer > Setup > Network
   - Most secure for home network use

3. **Use environment variables in production**
   - Especially in Docker/Kubernetes environments
   - Easier to manage secrets securely
   - Environment variables override config file values

4. **Enable SSL verification in production**
   - Only disable (`verify_ssl: false`) for testing with self-signed certificates
   - For local instances, consider using proper SSL certificates

## Troubleshooting

### Configuration Issues

**Problem:** Configuration not loading
- **Solution:** Ensure `config.json` is in the project root directory
- **Solution:** Verify JSON syntax is valid (use a JSON validator)
- **Solution:** Check file permissions

**Problem:** Environment variables not working
- **Solution:** Ensure variables are prefixed with `HOMESEER_`
- **Solution:** Check that variables are set in the current shell session
- **Solution:** Variable names are case-sensitive

### Connection Issues

**Problem:** Authentication failed
- **Solution:** For local access, ensure "No Password Required for Local (same subnet) Login" is enabled in HomeSeer > Setup > Network
- **Solution:** For remote access, verify your username/password are correct
- **Solution:** Ensure the URL is accessible from your network
- **Solution:** For cloud HomeSeer, use `https://connected2.homeseer.com/json`
- **Solution:** Test the URL in a browser or with `curl`

**Problem:** SSL certificate verification failed
- **For Development:** Set `"verify_ssl": false` in config.json
- **For Production:** Install proper SSL certificates on your HomeSeer instance

**Problem:** Connection timeout
- **Solution:** Verify HomeSeer is running and accessible
- **Solution:** Increase timeout value (e.g., `"timeout": 60`)
- **Solution:** Check firewall settings

## Development

### Hot Reload Configuration

```python
from config import get_config_manager

# Reload configuration after making changes
manager = get_config_manager()
new_config = manager.reload_config()
```

### Debug Logging

Enable debug logging to see detailed configuration and API calls:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Project Structure

```
homeseer-mcp/
├── server.py              # Main MCP server implementation
├── config.py              # Configuration management
├── config.json.example    # Configuration template
├── requirements.txt       # Python dependencies
├── tests/                 # Test suite
│   ├── test_server.py    # Server and API client tests
│   ├── test_config.py    # Configuration tests
│   └── README.md         # Test documentation
├── test.ps1              # PowerShell test runner
├── test.bat              # Windows batch test runner
└── test.sh               # Unix/Linux test runner
```

## API Documentation

For detailed information about the HomeSeer JSON API, see:
- [HomeSeer JSON API Documentation](https://docs.homeseer.com/hspi/json-api)

## License

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please ensure:
- All tests pass (`pytest tests/`)
- Code follows existing patterns
- New features include tests
- Documentation is updated

## Future Enhancements

**OAuth Token Authentication:** The HomeSeer JSON API supports token-based authentication which could provide additional security benefits. If there is community interest, OAuth token support could be added in a future version. For now, the simplest approach is using local same-subnet access (no credentials) or username/password for remote access.

