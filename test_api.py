import requests
import json
import time
import base64
from PIL import Image
from io import BytesIO
import os

# API base URL
BASE_URL = "http://localhost:5000/api"

def show_image(base64_image):
    """Display an image from base64 string"""
    try:
        image_data = base64.b64decode(base64_image)
        image = Image.open(BytesIO(image_data))
        image.show()
    except Exception as e:
        print(f"Error displaying image: {e}")

def test_create_session():
    """Test creating a new Scrapybara session"""
    print("\n=== Testing Scrapybara Session Creation ===")
    
    # Choose which Scrapybara environment to test
    print("Available Scrapybara environments:")
    print("1. scrapybara-browser (Web browser environment)")
    print("2. scrapybara-ubuntu (Ubuntu environment)")
    choice = input("Choose environment (1/2) [default: 1]: ") or "1"
    
    computer_type = "scrapybara-browser" if choice == "1" else "scrapybara-ubuntu"
    
    # For browser environment, ask for start URL
    start_url = "https://www.google.com"
    if computer_type == "scrapybara-browser":
        start_url = input(f"Enter start URL [default: {start_url}]: ") or start_url
    
    # Create a session with the selected Scrapybara environment
    response = requests.post(
        f"{BASE_URL}/sessions",
        json={
            "computer": computer_type,
            "debug": True,
            "show": False,
            "start_url": start_url
        }
    )
    
    if response.status_code != 200:
        print(f"Error creating session: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    session_id = data.get("session_id")
    
    print(f"Session created with ID: {session_id}")
    print(f"Computer type: {data.get('computer_type')}")
    
    # Optionally display the screenshot
    if "screenshot" in data:
        print("Received screenshot. Display? (y/n)")
        if input().lower() == 'y':
            show_image(data["screenshot"])
    
    return session_id

def test_interact(session_id):
    """Test interacting with the agent"""
    print("\n=== Testing Agent Interaction ===")
    
    # Send a message to the agent
    user_input = input("Enter a message to send to the agent: ")
    
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/interact",
        json={"input": user_input}
    )
    
    if response.status_code != 200:
        print(f"Error interacting with agent: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    
    # Print the agent's response
    print("\nAgent Response:")
    for item in data.get("items", []):
        if item.get("role") == "assistant":
            print(f"Assistant: {item.get('content')}")
        elif item.get("type") == "message":
            print(f"Message: {item.get('content')}")
        elif item.get("type") == "computer_call":
            action = item.get("action", {})
            print(f"Action: {action.get('type')} with params {action}")
    
    # Optionally display the screenshot
    if "screenshot" in data:
        print("Received screenshot. Display? (y/n)")
        if input().lower() == 'y':
            show_image(data["screenshot"])
    
    # If it's a browser environment, show the current URL
    if "current_url" in data:
        print(f"Current URL: {data['current_url']}")

def test_execute_action(session_id):
    """Test executing a specific action"""
    print("\n=== Testing Action Execution ===")
    
    # Get the session type to show appropriate actions
    response = requests.get(f"{BASE_URL}/sessions")
    if response.status_code != 200:
        print("Error getting session information")
        return
    
    sessions = response.json().get("sessions", {})
    session_info = sessions.get(session_id, {})
    computer_type = session_info.get("computer_type", "unknown")
    
    # Define an action to execute
    if computer_type == "scrapybara-browser":
        print("Available browser actions: click, type, wait, scroll, move, keypress, goto, etc.")
    else:  # scrapybara-ubuntu
        print("Available Ubuntu actions: click, type, wait, scroll, move, keypress, etc.")
    
    action_type = input("Enter action type: ")
    
    # Build action parameters based on the action type
    action_params = {"type": action_type}
    
    if action_type == "click":
        action_params["x"] = int(input("Enter x coordinate: "))
        action_params["y"] = int(input("Enter y coordinate: "))
        action_params["button"] = input("Enter button (left/right/middle) [default: left]: ") or "left"
    
    elif action_type == "type":
        action_params["text"] = input("Enter text to type: ")
    
    elif action_type == "wait":
        action_params["ms"] = int(input("Enter wait time in milliseconds [default: 1000]: ") or "1000")
    
    elif action_type == "scroll":
        action_params["x"] = int(input("Enter x coordinate: "))
        action_params["y"] = int(input("Enter y coordinate: "))
        action_params["scroll_x"] = int(input("Enter horizontal scroll amount: "))
        action_params["scroll_y"] = int(input("Enter vertical scroll amount: "))
    
    elif action_type == "move":
        action_params["x"] = int(input("Enter x coordinate: "))
        action_params["y"] = int(input("Enter y coordinate: "))
    
    elif action_type == "keypress":
        keys = input("Enter keys to press (comma-separated): ").split(",")
        action_params["keys"] = [k.strip() for k in keys]
    
    elif action_type == "goto" and computer_type == "scrapybara-browser":
        action_params["url"] = input("Enter URL to navigate to: ")
    
    # Execute the action
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/action",
        json=action_params
    )
    
    if response.status_code != 200:
        print(f"Error executing action: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    print(f"Action executed: {data.get('message')}")
    
    # Optionally display the screenshot
    if "screenshot" in data:
        print("Received screenshot. Display? (y/n)")
        if input().lower() == 'y':
            show_image(data["screenshot"])
    
    # If it's a browser environment, show the current URL
    if "current_url" in data:
        print(f"Current URL: {data['current_url']}")

def test_get_screenshot(session_id):
    """Test getting a screenshot"""
    print("\n=== Testing Screenshot Retrieval ===")
    
    response = requests.get(f"{BASE_URL}/sessions/{session_id}/screenshot")
    
    if response.status_code != 200:
        print(f"Error getting screenshot: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    
    if "screenshot" in data:
        print("Received screenshot. Display? (y/n)")
        if input().lower() == 'y':
            show_image(data["screenshot"])

def test_delete_session(session_id):
    """Test deleting a session"""
    print("\n=== Testing Session Deletion ===")
    
    response = requests.delete(f"{BASE_URL}/sessions/{session_id}")
    
    if response.status_code != 200:
        print(f"Error deleting session: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    print(f"Session deleted: {data.get('message')}")

def test_list_sessions():
    """Test listing all sessions"""
    print("\n=== Testing Session Listing ===")
    
    response = requests.get(f"{BASE_URL}/sessions")
    
    if response.status_code != 200:
        print(f"Error listing sessions: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    sessions = data.get("sessions", {})
    
    if not sessions:
        print("No active Scrapybara sessions found.")
    else:
        print("Active Scrapybara sessions:")
        for session_id, session_info in sessions.items():
            print(f"  - {session_id}: {session_info}")

def main():
    """Main test function"""
    print("=== Scrapybara API Test Script ===")
    print("Make sure the API server is running on http://localhost:5000")
    print("This test script will only test Scrapybara functionality.")
    print("Ensure you have set SCRAPYBARA_API_KEY in your .env file.")
    
    # Test listing sessions (should be empty initially)
    test_list_sessions()
    
    # Create a session
    session_id = test_create_session()
    if not session_id:
        print("Failed to create Scrapybara session. Exiting.")
        return
    
    try:
        while True:
            print("\n=== Test Menu ===")
            print("1. Interact with agent")
            print("2. Execute specific action")
            print("3. Get screenshot")
            print("4. List all sessions")
            print("5. Delete session and exit")
            print("6. Exit without deleting session")
            
            choice = input("Enter your choice (1-6): ")
            
            if choice == "1":
                test_interact(session_id)
            elif choice == "2":
                test_execute_action(session_id)
            elif choice == "3":
                test_get_screenshot(session_id)
            elif choice == "4":
                test_list_sessions()
            elif choice == "5":
                test_delete_session(session_id)
                break
            elif choice == "6":
                print("Exiting without deleting session.")
                break
            else:
                print("Invalid choice. Please try again.")
    
    except KeyboardInterrupt:
        print("\nTest interrupted.")
        if input("Delete session before exiting? (y/n): ").lower() == 'y':
            test_delete_session(session_id)

if __name__ == "__main__":
    main() 