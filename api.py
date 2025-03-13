from flask import Flask, request, jsonify
import json
import base64
import traceback
import time
from agent.agent import Agent
from computers import (
    ScrapybaraBrowser,
    ScrapybaraUbuntu,
)

app = Flask(__name__)

# Store active computer and agent instances
active_sessions = {}

def acknowledge_safety_check_callback(message: str) -> bool:
    # In API mode, we'll auto-acknowledge safety checks
    print(f"Auto-acknowledging safety check: {message}")
    return True

def extract_stream_url(computer):
    """Extract the stream URL from a Scrapybara computer instance using multiple methods"""
    try:
        # Method 1: Try to access through the instance attribute
        if hasattr(computer, 'instance') and computer.instance:
            if hasattr(computer.instance, 'get_stream_url'):
                stream_info = computer.instance.get_stream_url()
                if hasattr(stream_info, 'stream_url'):
                    return stream_info.stream_url
                return str(stream_info)
        
        # Method 2: Try to access through the client attribute
        if hasattr(computer, 'client') and computer.client:
            if hasattr(computer.client, 'get_stream_url'):
                stream_info = computer.client.get_stream_url()
                if hasattr(stream_info, 'stream_url'):
                    return stream_info.stream_url
                return str(stream_info)
        
        # Method 3: Try to access directly from the computer
        if hasattr(computer, 'get_stream_url'):
            stream_info = computer.get_stream_url()
            if hasattr(stream_info, 'stream_url'):
                return stream_info.stream_url
            return str(stream_info)
        
        # Method 4: Try to access through browser attribute
        if hasattr(computer, 'browser') and computer.browser:
            if hasattr(computer.browser, 'get_stream_url'):
                stream_info = computer.browser.get_stream_url()
                if hasattr(stream_info, 'stream_url'):
                    return stream_info.stream_url
                return str(stream_info)
        
        # Method 5: Look for any attribute containing 'stream_url'
        for attr_name in dir(computer):
            if 'stream' in attr_name.lower() and not attr_name.startswith('__'):
                try:
                    attr_value = getattr(computer, attr_name)
                    if isinstance(attr_value, str) and ('http' in attr_value or 'www' in attr_value):
                        return attr_value
                except:
                    pass
        
        # If we get here, we couldn't find the stream URL
        return None
    except Exception as e:
        print(f"Error extracting stream URL: {str(e)}")
        return None

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Create a new session with a specified Scrapybara environment"""
    data = request.json
    
    computer_type = data.get('computer', 'scrapybara-browser')
    debug = data.get('debug', False)
    show = data.get('show', False)
    start_url = data.get('start_url', 'https://bing.com')
    
    computer_mapping = {
        "scrapybara-browser": ScrapybaraBrowser,
        "scrapybara-ubuntu": ScrapybaraUbuntu,
    }
    
    if computer_type not in computer_mapping:
        return jsonify({"error": f"Unknown computer type: {computer_type}. Only scrapybara-browser and scrapybara-ubuntu are supported."}), 400
    
    ComputerClass = computer_mapping[computer_type]
    
    try:
        # Create computer instance
        print(f"Creating {computer_type} instance...")
        computer = ComputerClass()
        print("Entering computer context...")
        computer.__enter__()
        print("Computer context entered successfully")
        
        # Wait a moment for the instance to fully initialize
        time.sleep(2)
        
        # Try to get the stream URL
        print("Attempting to get stream URL...")
        stream_url = extract_stream_url(computer)
        print(f"Stream URL: {stream_url}")
        
        # Create agent instance
        agent = Agent(
            computer=computer,
            acknowledge_safety_check_callback=acknowledge_safety_check_callback,
        )
        
        # Generate a session ID
        import uuid
        session_id = str(uuid.uuid4())
        
        # Store the session with creation timestamp
        import datetime
        active_sessions[session_id] = {
            "computer": computer,
            "agent": agent,
            "items": [],
            "debug": debug,
            "show": show,
            "computer_type": computer_type,
            "stream_url": stream_url,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        # If it's a browser environment, navigate to the start URL
        if computer_type == "scrapybara-browser" and hasattr(computer, 'goto') and callable(computer.goto):
            print(f"Navigating to {start_url}")
            computer.goto(start_url)
        
        # Take a screenshot to return to the client
        print("Taking screenshot...")
        screenshot = computer.screenshot()
        
        response_data = {
            "session_id": session_id,
            "computer_type": computer_type,
            "screenshot": screenshot,
            "message": f"Session created with {computer_type}"
        }
        
        # Include stream URL in the response if available
        if stream_url:
            response_data["stream_url"] = stream_url
        
        return jsonify(response_data)
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error creating session: {str(e)}")
        print(f"Error details: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a session and clean up resources"""
    if session_id not in active_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    try:
        # Clean up resources
        session = active_sessions[session_id]
        session["computer"].__exit__(None, None, None)
        
        # Remove the session
        del active_sessions[session_id]
        
        return jsonify({"message": f"Session {session_id} deleted"})
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error deleting session: {str(e)}")
        print(f"Error details: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

@app.route('/api/sessions/<session_id>/interact', methods=['POST'])
def interact(session_id):
    """Send a message to the agent and get a response"""
    if session_id not in active_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    data = request.json
    user_input = data.get('input')
    
    if not user_input:
        return jsonify({"error": "Input is required"}), 400
    
    try:
        session = active_sessions[session_id]
        agent = session["agent"]
        items = session["items"]
        
        # Add user input to items
        items.append({"role": "user", "content": user_input})
        
        # Run the agent
        output_items = agent.run_full_turn(
            items,
            print_steps=True,
            show_images=session["show"],
            debug=session["debug"],
        )
        
        # Add output items to the session
        items.extend(output_items)
        
        # Take a screenshot to return to the client
        screenshot = session["computer"].screenshot()
        
        # Format the response
        response = {
            "items": output_items,
            "screenshot": screenshot
        }
        
        # Include stream URL in the response
        if session.get("stream_url"):
            response["stream_url"] = session["stream_url"]
        
        # If it's a browser environment, include the current URL
        if session["computer_type"] == "scrapybara-browser":
            try:
                response["current_url"] = session["computer"].get_current_url()
            except:
                pass
        
        return jsonify(response)
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error in interaction: {str(e)}")
        print(f"Error details: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

@app.route('/api/sessions/<session_id>/screenshot', methods=['GET'])
def get_screenshot(session_id):
    """Get a screenshot from the current session"""
    if session_id not in active_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    try:
        session = active_sessions[session_id]
        screenshot = session["computer"].screenshot()
        
        response = {"screenshot": screenshot}
        
        # Include stream URL in the response
        if session.get("stream_url"):
            response["stream_url"] = session["stream_url"]
        
        return jsonify(response)
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error getting screenshot: {str(e)}")
        print(f"Error details: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

@app.route('/api/sessions/<session_id>/action', methods=['POST'])
def execute_action(session_id):
    """Execute a specific action on the computer"""
    if session_id not in active_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    data = request.json
    action_type = data.get('type')
    
    if not action_type:
        return jsonify({"error": "Action type is required"}), 400
    
    try:
        session = active_sessions[session_id]
        computer = session["computer"]
        
        # Extract action parameters (excluding type)
        action_params = {k: v for k, v in data.items() if k != 'type'}
        
        # Check if the action method exists
        if not hasattr(computer, action_type) or not callable(getattr(computer, action_type)):
            return jsonify({"error": f"Unknown action: {action_type}"}), 400
        
        # Execute the action
        method = getattr(computer, action_type)
        method(**action_params)
        
        # Take a screenshot to return to the client
        screenshot = computer.screenshot()
        
        response = {
            "message": f"Action {action_type} executed",
            "screenshot": screenshot
        }
        
        # Include stream URL in the response
        if session.get("stream_url"):
            response["stream_url"] = session["stream_url"]
        
        # If it's a browser environment, include the current URL
        if session["computer_type"] == "scrapybara-browser":
            try:
                response["current_url"] = computer.get_current_url()
            except:
                pass
        
        return jsonify(response)
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error executing action: {str(e)}")
        print(f"Error details: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    """List all active sessions"""
    sessions = {}
    for session_id, session in active_sessions.items():
        sessions[session_id] = {
            "computer_type": session["computer_type"],
            "created_at": session.get("created_at", "unknown"),
            "stream_url": session.get("stream_url")
        }
    
    return jsonify({"sessions": sessions})

@app.route('/api/debug/session/<session_id>', methods=['GET'])
def debug_session(session_id):
    """Debug endpoint to inspect a session's structure"""
    if session_id not in active_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    try:
        session = active_sessions[session_id]
        computer = session["computer"]
        
        # Collect information about the computer object
        computer_info = {
            "type": type(computer).__name__,
            "attributes": [],
            "methods": []
        }
        
        # List attributes and methods
        for attr_name in dir(computer):
            if attr_name.startswith('__'):
                continue
                
            try:
                attr = getattr(computer, attr_name)
                if callable(attr):
                    computer_info["methods"].append(attr_name)
                else:
                    # Only include simple attributes that can be serialized
                    if isinstance(attr, (str, int, float, bool, type(None))):
                        computer_info["attributes"].append({
                            "name": attr_name,
                            "type": type(attr).__name__,
                            "value": attr
                        })
                    else:
                        computer_info["attributes"].append({
                            "name": attr_name,
                            "type": type(attr).__name__
                        })
            except:
                pass
        
        # Try to find stream URL again
        stream_url = extract_stream_url(computer)
        
        return jsonify({
            "session_id": session_id,
            "computer_type": session["computer_type"],
            "created_at": session.get("created_at", "unknown"),
            "stream_url": session.get("stream_url"),
            "newly_found_stream_url": stream_url,
            "computer_info": computer_info
        })
    
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error debugging session: {str(e)}")
        print(f"Error details: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 