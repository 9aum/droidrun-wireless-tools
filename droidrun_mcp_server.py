from mcp.server.fastmcp import FastMCP
import requests
import base64
import json
import time
import wifi_config

# --- CONFIGURATION ---
# Initialize FastMCP Server
mcp = FastMCP("DroidRun Control")

# Connection Details from wifi_config.py
BASE_URL = f"http://{wifi_config.TARGET_IP}:{wifi_config.TARGET_PORT}"
HEADERS = {
    "Authorization": f"Bearer {wifi_config.AUTH_TOKEN}",
    "Content-Type": "application/json"
}

# --- TOOLS ---

@mcp.tool()
def get_screen_content(mode: str = "fast") -> str:
    """
    Get the current screen content / UI State.
    Args:
        mode: 'fast' for /a11y_tree (Recommended) or 'full' for /state_full.
    """
    endpoint = "/a11y_tree" if mode == "fast" else "/state_full"
    url = f"{BASE_URL}{endpoint}"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return json.dumps(resp.json(), ensure_ascii=False)
    except Exception as e:
        return f"Error getting screen: {e}"

@mcp.tool()
def tap_coordinate(x: int, y: int) -> str:
    """
    Tap at specific (x, y) coordinates on the screen.
    """
    url = f"{BASE_URL}/action/tap"
    payload = {"x": int(x), "y": int(y)}
    
    try:
        requests.post(url, json=payload, headers=HEADERS, timeout=5)
        return f"Tapped at ({x}, {y})"
    except Exception as e:
        return f"Error tapping: {e}"

@mcp.tool()
def type_text(text: str) -> str:
    """
    Type text into the focused input field. 
    Supports Unicode/Thai via Base64.
    """
    url = f"{BASE_URL}/keyboard/input"
    b64_text = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    payload = {"base64_text": b64_text}
    
    try:
        requests.post(url, json=payload, headers=HEADERS, timeout=5)
        return f"Typed: '{text}'"
    except Exception as e:
        return f"Error typing: {e}"

@mcp.tool()
def press_home() -> str:
    """Press the generic Android HOME button."""
    return _send_global_action(2, "HOME")

@mcp.tool()
def press_back() -> str:
    """Press the generic Android BACK button."""
    return _send_global_action(1, "BACK")

@mcp.tool()
def press_key(key_code_or_name: str) -> str:
    """
    Press a specific key by Code or Name.
    Valid Names: enter, backspace, tab, escape, home, back, up, down, left, right.
    """
    KEY_MAP = {
        "enter": 66, "backspace": 67, "tab": 61, "escape": 111,
        "back": 4, "home": 3, 
        "up": 19, "down": 20, "left": 21, "right": 22
    }
    k = str(key_code_or_name).lower()
    code = KEY_MAP.get(k, k)
    
    try:
        url = f"{BASE_URL}/keyboard/key"
        requests.post(url, json={"key_code": int(code)}, headers=HEADERS, timeout=5)
        return f"Pressed Key: {code}"
    except Exception as e:
        return f"Error pressing key: {e}"

@mcp.tool()
def long_press(x: int, y: int, duration_ms: int = 1000) -> str:
    """Long press at coordinates (simulated via Swipe)."""
    return swipe(x, y, x, y, duration_ms)

@mcp.tool()
def swipe(sx: int, sy: int, ex: int, ey: int, duration_ms: int = 500) -> str:
    """Swipe from (sx,sy) to (ex,ey)."""
    url = f"{BASE_URL}/action/swipe"
    payload = {"startX": int(sx), "startY": int(sy), "endX": int(ex), "endY": int(ey), "duration": int(duration_ms)}
    try:
        requests.post(url, json=payload, headers=HEADERS, timeout=5)
        return f"Swiped {sx},{sy} -> {ex},{ey}"
    except Exception as e:
        return f"Error swiping: {e}"

@mcp.tool()
def clear_text() -> str:
    """Clear text in the focused input field."""
    url = f"{BASE_URL}/keyboard/clear"
    try:
        requests.post(url, json={}, headers=HEADERS, timeout=5)
        return "Text Cleared"
    except Exception as e:
        return f"Error clearing text: {e}"

@mcp.tool()
def get_device_info() -> str:
    """Get device status (Current App, Keyboard, etc)."""
    url = f"{BASE_URL}/phone_state"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=5)
        return json.dumps(resp.json(), indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error getting device info: {e}"

@mcp.tool()
def list_apps() -> str:
    """List all installed applications (Label & Package Name)."""
    url = f"{BASE_URL}/packages"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        apps = resp.json().get("result", [])
        # Simplify output for LLM
        simple_list = [f"{app['label']} ({app['packageName']})" for app in apps]
        return "\n".join(simple_list)
    except Exception as e:
        return f"Error listing apps: {e}"

@mcp.tool()
def get_screenshot() -> str:
    """Get the current screen as a Base64 PNG string."""
    url = f"{BASE_URL}/screenshot"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        # Verify it's valid base64 or binary
        if resp.headers.get("Content-Type") == "image/png":
            return base64.b64encode(resp.content).decode('utf-8')
        return resp.text # Likely already base64 string from API
    except Exception as e:
        return f"Error getting screenshot: {e}"

def _send_global_action(action_id: int, name: str) -> str:
    url = f"{BASE_URL}/action/global"
    payload = {"action": action_id}
    try:
        requests.post(url, json=payload, headers=HEADERS, timeout=5)
        return f"Pressed {name}"
    except Exception as e:
        return f"Error pressing {name}: {e}"

if __name__ == "__main__":
    # Run the MCP Server
    print("DroidRun MCP Server Running...")
    mcp.run()
