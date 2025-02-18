from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.web import WebClient
import os
from dotenv import load_dotenv
from openai import OpenAI
import logging


# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get environment variables
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")  # You'll need this new token
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# Initialize clients
slack_client = WebClient(token=SLACK_BOT_TOKEN)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def on_connect(client: SocketModeClient, response):
    """Called when the client connects successfully"""
    logger.info("Connected to Slack Socket Mode!")
    
def on_disconnect(client: SocketModeClient):
    """Called when the client disconnects"""
    logger.info("Disconnected from Slack Socket Mode!")
    
def on_error(client: SocketModeClient, error):
    """Called when the client encounters an error"""
    logger.error(f"Error in Socket Mode: {error}")

def handle_slack_event(client: SocketModeClient, req: SocketModeRequest):
    """Handle incoming Slack events."""
    logger.info(f"Received event type: {req.type}")
    logger.info(f"Full event payload: {req.payload}")
    
    # ... rest of your handle_slack_event function ...

def process_message_with_openai(message, thread_messages):
    """Send messages to OpenAI Assistant for parsing."""
    combined_text = message + " " + " ".join(thread_messages)
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": combined_text}],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error processing message with OpenAI: {str(e)}")
        return None

def handle_slack_event(client: SocketModeClient, req: SocketModeRequest):
    """Handle incoming Slack events."""
    logger.info(f"Received event type: {req.type}")
    logger.info(f"Full event payload: {req.payload}")
    if req.type == "events_api":
        # Acknowledge the request
        client.send_socket_mode_response(SocketModeResponse(envelope_id=req.envelope_id))
        
        event = req.payload["event"]
        logger.info(f"Event received: {event}")
        
        # Only process messages from the specified channel
        if event["type"] == "message" and event.get("channel") == CHANNEL_ID:
            logger.info(f"🔹 Received Message: {event.get('text')} from {event.get('user')} in {event.get('channel')}")
            # Ignore bot messages and message updates
            if "bot_id" not in event and "subtype" not in event:
                message_text = event.get("text", "")
                thread_ts = event.get("thread_ts")
                
                # Get thread messages if it's in a thread
                thread_messages = []
                if thread_ts:
                    try:
                        replies = slack_client.conversations_replies(
                            channel=CHANNEL_ID,
                            ts=thread_ts
                        )
                        thread_messages = [msg["text"] for msg in replies.get("messages", [])[1:]]
                    except Exception as e:
                        print(f"Error fetching thread messages: {e}")

                # Process message with OpenAI
                if message_text:
                    ai_response = process_message_with_openai(message_text, thread_messages)
                    if ai_response:
                        # Reply in thread if it's a thread message, otherwise send as new message
                        thread_ts = event.get("thread_ts", event.get("ts"))
                        try:
                            slack_client.chat_postMessage(
                                channel=CHANNEL_ID,
                                text=ai_response,
                                thread_ts=thread_ts
                            )
                        except Exception as e:
                            print(f"Error sending response to Slack: {e}")

def main():
    """Main function to run the Slack event listener."""
    logger.info("=== Starting Slack Bot ===")
    
    # Print all environment variables (without sensitive data)
    logger.info(f"SLACK_BOT_TOKEN exists: {'Yes' if os.getenv('SLACK_BOT_TOKEN') else 'No'}")
    logger.info(f"SLACK_APP_TOKEN exists: {'Yes' if os.getenv('SLACK_APP_TOKEN') else 'No'}")
    logger.info(f"OPENAI_API_KEY exists: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
    logger.info(f"CHANNEL_ID exists: {'Yes' if os.getenv('CHANNEL_ID') else 'No'}")
    
    # Initialize Socket Mode client
    logger.info("Initializing Socket Mode client...")
    app = SocketModeClient(
        app_token=os.getenv('SLACK_APP_TOKEN'),
        web_client=WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
    )

    # Add event listeners
    app.on_connect = on_connect
    app.on_disconnect = on_disconnect
    app.on_error = on_error

    # Add event handler
    app.socket_mode_request_listeners.append(handle_slack_event)

    # Test the Slack connection
    try:
        logger.info("Testing Slack Web API connection...")
        auth_test = app.web_client.auth_test()
        logger.info(f"Connected as: {auth_test['user']} to workspace: {auth_test['team']}")
    except Exception as e:
        logger.error(f"Failed to connect to Slack: {e}")
        return

    # Start the app
    logger.info("⚡️ Connecting to Slack Socket Mode...")
    try:
        app.connect()
        logger.info("Socket Mode connection initiated...")
    except Exception as e:
        logger.error(f"Failed to connect to Socket Mode: {e}")
        return

    # Keep the program running
    import signal
    def signal_handler(signum, frame):
        logger.info("\nStopping the application...")
        app.disconnect()
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Bot is running and waiting for events...")
    
    # Keep the process alive
    while True:
        try:
            signal.pause()
        except AttributeError:
            import time
            time.sleep(1)

if __name__ == "__main__":
    main()