# Scrapybara Agent API

This API provides HTTP endpoints to interact with the Scrapybara-powered Computer Use Agent (CUA) system. It allows you to create sessions with different Scrapybara environments, interact with the agent, and execute specific actions.

## What is Scrapybara?

[Scrapybara](https://scrapybara.com) provides virtual desktops and browsers in the cloud. It offers two main environments:

1. **scrapybara-browser**: A browser environment for web automation
2. **scrapybara-ubuntu**: A full Ubuntu environment for more complex automation tasks

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure you have the necessary API keys in your `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key
   SCRAPYBARA_API_KEY=your_scrapybara_api_key
   ```

3. Start the API server:
   ```bash
   python api.py
   ```

## API Endpoints

### Sessions

#### Create a Session
- **URL**: `/api/sessions`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "computer": "scrapybara-browser",  // Options: scrapybara-browser, scrapybara-ubuntu
    "debug": false,
    "show": false,
    "start_url": "https://bing.com"  // For browser environment
  }
  ```
- **Response**:
  ```json
  {
    "session_id": "uuid",
    "computer_type": "scrapybara-browser",
    "screenshot": "base64-encoded-image",
    "message": "Session created with scrapybara-browser"
  }
  ```

#### List Sessions
- **URL**: `/api/sessions`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "sessions": {
      "session-id-1": {
        "computer_type": "scrapybara-browser",
        "created_at": "timestamp"
      },
      "session-id-2": {
        "computer_type": "scrapybara-ubuntu",
        "created_at": "timestamp"
      }
    }
  }
  ```

#### Delete a Session
- **URL**: `/api/sessions/{session_id}`
- **Method**: `DELETE`
- **Response**:
  ```json
  {
    "message": "Session {session_id} deleted"
  }
  ```

### Interaction

#### Interact with Agent
- **URL**: `/api/sessions/{session_id}/interact`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "input": "Your message to the agent"
  }
  ```
- **Response**:
  ```json
  {
    "items": [
      {
        "role": "assistant",
        "content": "Agent's response"
      },
      {
        "type": "computer_call",
        "action": {
          "type": "click",
          "x": 100,
          "y": 200
        }
      },
      // Other items...
    ],
    "screenshot": "base64-encoded-image",
    "current_url": "https://example.com"  // For browser environment
  }
  ```

#### Execute Action
- **URL**: `/api/sessions/{session_id}/action`
- **Method**: `POST`
- **Body**:
  ```json
  {
    "type": "click",  // Action type
    "x": 100,         // Action-specific parameters
    "y": 200,
    "button": "left"
  }
  ```
- **Response**:
  ```json
  {
    "message": "Action click executed",
    "screenshot": "base64-encoded-image",
    "current_url": "https://example.com"  // For browser environment
  }
  ```

#### Get Screenshot
- **URL**: `/api/sessions/{session_id}/screenshot`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "screenshot": "base64-encoded-image"
  }
  ```

## Testing

You can test the API using the provided test script:

```bash
python test_api.py
```

The test script provides an interactive menu to test different API endpoints with Scrapybara environments.

## Available Actions

Depending on the Scrapybara environment, the following actions are available:

### Common Actions (Both Environments)

- **click**: Click at a specific position
  ```json
  {
    "type": "click",
    "x": 100,
    "y": 200,
    "button": "left"  // left, right, middle
  }
  ```

- **double_click**: Double-click at a specific position
  ```json
  {
    "type": "double_click",
    "x": 100,
    "y": 200
  }
  ```

- **scroll**: Scroll at a specific position
  ```json
  {
    "type": "scroll",
    "x": 100,
    "y": 200,
    "scroll_x": 0,
    "scroll_y": 100
  }
  ```

- **type**: Type text
  ```json
  {
    "type": "type",
    "text": "Hello, world!"
  }
  ```

- **wait**: Wait for a specified time
  ```json
  {
    "type": "wait",
    "ms": 1000
  }
  ```

- **move**: Move the cursor to a specific position
  ```json
  {
    "type": "move",
    "x": 100,
    "y": 200
  }
  ```

- **keypress**: Press specific keys
  ```json
  {
    "type": "keypress",
    "keys": ["ctrl", "a"]
  }
  ```

### Browser-Specific Actions (scrapybara-browser only)

- **goto**: Navigate to a URL
  ```json
  {
    "type": "goto",
    "url": "https://example.com"
  }
  ```

## Integration with Next.js

To integrate this API with a Next.js application:

1. Start the API server as described above.

2. In your Next.js application, make HTTP requests to the API endpoints to create sessions, interact with the agent, and execute actions.

3. You can display the screenshots returned by the API in your Next.js UI.

4. For a more seamless integration, you can create a Next.js API route that proxies requests to this API.

Example Next.js API route:

```javascript
// pages/api/agent/[...path].js
export default async function handler(req, res) {
  const { path } = req.query;
  const apiUrl = `http://localhost:5000/api/${path.join('/')}`;
  
  const response = await fetch(apiUrl, {
    method: req.method,
    headers: {
      'Content-Type': 'application/json',
    },
    body: req.method !== 'GET' ? JSON.stringify(req.body) : undefined,
  });
  
  const data = await response.json();
  res.status(response.status).json(data);
}
```

This allows your Next.js frontend to interact with the Scrapybara agent through your Next.js API routes.

## Example Next.js Integration

Here's a simple example of how you might use this API in a Next.js component:

```jsx
// components/ScrapybaraController.js
import { useState, useEffect } from 'react';
import Image from 'next/image';

export default function ScrapybaraController() {
  const [sessionId, setSessionId] = useState(null);
  const [screenshot, setScreenshot] = useState(null);
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState(null);
  
  // Create a session when the component mounts
  useEffect(() => {
    async function createSession() {
      const res = await fetch('/api/agent/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          computer: 'scrapybara-browser',
          start_url: 'https://www.google.com'
        })
      });
      
      const data = await res.json();
      setSessionId(data.session_id);
      setScreenshot(data.screenshot);
    }
    
    createSession();
    
    // Clean up the session when the component unmounts
    return () => {
      if (sessionId) {
        fetch(`/api/agent/sessions/${sessionId}`, { method: 'DELETE' });
      }
    };
  }, []);
  
  // Send a message to the agent
  async function sendMessage() {
    if (!sessionId || !message) return;
    
    const res = await fetch(`/api/agent/sessions/${sessionId}/interact`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input: message })
    });
    
    const data = await res.json();
    setResponse(data);
    setScreenshot(data.screenshot);
    setMessage('');
  }
  
  if (!sessionId) return <div>Loading Scrapybara session...</div>;
  
  return (
    <div className="scrapybara-controller">
      <div className="screenshot-container">
        {screenshot && (
          <Image 
            src={`data:image/png;base64,${screenshot}`}
            alt="Scrapybara screenshot"
            width={800}
            height={600}
          />
        )}
      </div>
      
      <div className="input-container">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Tell the agent what to do..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
      
      {response && (
        <div className="response-container">
          {response.items.map((item, index) => (
            <div key={index} className="response-item">
              {item.role === 'assistant' && (
                <div className="assistant-message">{item.content}</div>
              )}
              {item.type === 'computer_call' && (
                <div className="action">
                  Action: {item.action.type}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
``` 