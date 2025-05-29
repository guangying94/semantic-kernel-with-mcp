"""
Semantic Kernel MCP Integration with Chainlit

This application provides a conversational AI interface that integrates:
- Microsoft Semantic Kernel for AI orchestration
- Model Context Protocol (MCP) for tool integration  
- Chainlit for the web-based chat interface
- Azure OpenAI for language model capabilities

Core functionality:
- Dynamically connects to MCP servers and registers their tools
- Routes chat messages through Semantic Kernel with function calling
- Provides real-time logging and debugging capabilities
- Handles MCP server lifecycle (connect/disconnect) gracefully
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv
import chainlit as cl
from mcp import ClientSession

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.mcp import MCPSsePlugin
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)

# ============================================================================
# Logging Configuration
# ============================================================================

class CapturingHandler(logging.Handler):
    """Custom logging handler to capture and store Semantic Kernel logs for debugging."""
    
    def __init__(self):
        super().__init__()
        self.logs: List[str] = []
        
    def emit(self, record: logging.LogRecord) -> None:
        """Capture log records and store formatted messages."""
        log_entry = self.format(record)
        self.logs.append(log_entry)
        
    def get_logs(self) -> List[str]:
        """Return all captured log messages."""
        return self.logs
        
    def clear(self) -> None:
        """Clear all captured log messages."""
        self.logs = []


def setup_logging() -> CapturingHandler:
    """Configure logging for Semantic Kernel with custom capturing handler."""
    capturing_handler = CapturingHandler()
    capturing_handler.setFormatter(
        logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    )
    
    # Add handler to semantic kernel loggers
    sk_logger = logging.getLogger("semantic_kernel")
    sk_logger.setLevel(logging.DEBUG)
    sk_logger.addHandler(capturing_handler)
    
    return capturing_handler


# ============================================================================
# Application Initialization
# ============================================================================

# Load environment variables
load_dotenv()

# Initialize logging
capturing_handler = setup_logging()

# Initialize Semantic Kernel
kernel = Kernel()

def create_azure_chat_service() -> AzureChatCompletion:
    """Create and configure Azure OpenAI chat completion service."""
    required_env_vars = [
        "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME",
        "AZURE_OPENAI_API_KEY", 
        "AZURE_OPENAI_BASE_URL",
        "AZURE_OPENAI_API_VERSION"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    return AzureChatCompletion(
        deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        base_url=os.getenv("AZURE_OPENAI_BASE_URL"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        service_id="azure-openai-svc",
    )

# Initialize and add chat service to kernel
chat_completion_service = create_azure_chat_service()
kernel.add_service(chat_completion_service)


# ============================================================================
# MCP Integration Functions
# ============================================================================


def extract_mcp_tools(tools_list) -> List[Dict[str, Any]]:
    """Extract and format tool information from MCP tools list."""
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema,
        } for tool in tools_list
    ]


@cl.on_mcp_connect
async def on_mcp_connect(connection, session: ClientSession) -> None:
    """
    Handle MCP server connection and integration with Semantic Kernel.
    
    This function:
    1. Lists available tools from the MCP server
    2. Stores tool information in user session
    3. Creates and connects MCPSsePlugin to Semantic Kernel
    4. Handles connection errors gracefully
    """
    try:
        # List available tools from MCP server
        result = await session.list_tools()
        print(f"Connected to MCP: {connection.name}")
        print(f"Available tools: {result.tools}")
        
        # Extract and store tool information
        tools = extract_mcp_tools(result.tools)
        mcp_tools = cl.user_session.get("mcp_tools", {})
        mcp_tools[connection.name] = tools
        cl.user_session.set("mcp_tools", mcp_tools)
        
        # Integrate with Semantic Kernel
        await _integrate_mcp_with_kernel(connection)
        
    except Exception as e:
        error_msg = f"Failed to handle MCP connection for {connection.name}: {str(e)}"
        await cl.Message(content=error_msg).send()
        print(error_msg)


async def _integrate_mcp_with_kernel(connection) -> None:
    """Integrate MCP server with Semantic Kernel as a plugin."""
    try:
        # Get MCP server URL
        mcp_url = getattr(connection, 'url', None)
        if not mcp_url:
            raise ValueError(f"No URL found for MCP connection {connection.name}")
        
        print(f"Using MCP URL: {mcp_url}")
        
        # Create and connect MCPSsePlugin
        mcp_plugin = MCPSsePlugin(
            name=connection.name,
            description=f"MCP Plugin for {connection.name}",
            url=mcp_url,
        )
        
        await mcp_plugin.connect()
        kernel.add_plugin(mcp_plugin)
        
        # Store plugin reference for cleanup
        mcp_plugins = cl.user_session.get("mcp_plugins", {})
        mcp_plugins[connection.name] = mcp_plugin
        cl.user_session.set("mcp_plugins", mcp_plugins)
        
        await cl.Message(content=f"Successfully connected {connection.name} to Semantic Kernel").send()
        print(f"Added MCP plugin {connection.name} to Semantic Kernel")
        
    except Exception as e:
        error_msg = f"Failed to integrate {connection.name} with Semantic Kernel: {str(e)}"
        await cl.Message(content=error_msg).send()
        print(error_msg)


def find_mcp_for_tool(tool_name: str) -> Optional[str]:
    """Find which MCP server provides the specified tool."""
    mcp_tools = cl.user_session.get("mcp_tools", {})
    
    for connection_name, tools in mcp_tools.items():
        if any(tool.get("name") == tool_name for tool in tools):
            return connection_name
    
    return None


@cl.step(type="tool")
async def call_tool(tool_use) -> str:
    """
    Execute a tool call through the appropriate MCP server.
    
    This function:
    1. Identifies which MCP server provides the requested tool
    2. Retrieves the MCP session for that server
    3. Executes the tool with provided input
    4. Returns the result or error message
    """
    tool_name = tool_use.name
    tool_input = tool_use.input
    
    current_step = cl.context.current_step
    current_step.name = tool_name
    
    try:
        # Find which MCP server provides this tool
        mcp_name = find_mcp_for_tool(tool_name)
        if not mcp_name:
            error_msg = f"Tool {tool_name} not found in any MCP connection"
            current_step.output = json.dumps({"error": error_msg})
            return current_step.output
        
        # Get MCP session
        mcp_session_data = cl.context.session.mcp_sessions.get(mcp_name)
        if not mcp_session_data:
            error_msg = f"MCP session {mcp_name} not found"
            current_step.output = json.dumps({"error": error_msg})
            return current_step.output
        
        mcp_session, _ = mcp_session_data
        
        # Execute tool call
        current_step.output = await mcp_session.call_tool(tool_name, tool_input)
        
    except Exception as e:
        error_msg = f"Error executing tool {tool_name}: {str(e)}"
        current_step.output = json.dumps({"error": error_msg})
        print(error_msg)
    
    return current_step.output


# ============================================================================
# Chainlit Event Handlers
# ============================================================================


@cl.on_chat_start
async def start_chat() -> None:
    """
    Initialize chat session with required session variables.
    
    Sets up:
    - Empty chat history
    - MCP plugins tracking
    - Other session state management
    """
    cl.user_session.set("mcp_plugins", {})
    cl.user_session.set("mcp_tools", {})
    cl.user_session.set("history", ChatHistory())


def create_thought_elements(thought_process: List[str]) -> List[cl.Text]:
    """Create formatted thought process elements for display."""
    thought_elements = []
    
    # Extract plugin usage from logs
    plugin_logs = [log for log in thought_process 
                  if "plugin" in log.lower() or "function" in log.lower()]
    
    if plugin_logs:
        thought_elements.append(
            cl.Text(name="Plugin Activity", content="\n".join(plugin_logs))
        )
    
    # Add all logs for full visibility
    if thought_process:
        thought_elements.append(
            cl.Text(name="Semantic Kernel Logs", content="\n".join(thought_process))
        )
    
    return thought_elements


@cl.on_message
async def on_message(msg: cl.Message) -> None:
    """
    Handle incoming chat messages and generate AI responses.
    
    This function:
    1. Adds user message to chat history
    2. Processes message through Semantic Kernel with function calling
    3. Displays thinking process and logs
    4. Returns AI response to user
    """
    try:
        # Get chat history and add user message
        history = cl.user_session.get("history")
        if not history:
            history = ChatHistory()
            cl.user_session.set("history", history)
        
        history.add_user_message(msg.content)
        
        # Clear previous logs
        capturing_handler.clear()
        
        async with cl.Step(name="Thinking...") as step:
            try:
                # Configure execution settings with function calling
                execution_settings = AzureChatPromptExecutionSettings()
                execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
                
                # Get AI response
                response = await chat_completion_service.get_chat_message_content(
                    chat_history=history,
                    settings=execution_settings,
                    kernel=kernel,
                )
                
                # Add response to history
                history.add_message(response)
                
                # Display thinking process
                thought_process = capturing_handler.get_logs()
                thought_elements = create_thought_elements(thought_process)
                
                if thought_elements:
                    step.elements = thought_elements
                    await step.update()
                
                # Send response to user
                await cl.Message(content=str(response)).send()
                
            except Exception as e:
                error_msg = f"Error processing message: {str(e)}"
                await cl.Message(content=error_msg).send()
                print(error_msg)
                
    except Exception as e:
        error_msg = f"Unexpected error in message handler: {str(e)}"
        await cl.Message(content=error_msg).send()
        print(error_msg)


@cl.on_mcp_disconnect
async def on_mcp_disconnect(connection_name: str) -> None:
    """
    Handle MCP server disconnection and cleanup.
    
    This function:
    1. Removes tools from session storage
    2. Disconnects and removes MCP plugin from Semantic Kernel
    3. Cleans up session state
    4. Notifies user of disconnection status
    """
    try:
        # Remove stored tools
        mcp_tools = cl.user_session.get("mcp_tools", {})
        if connection_name in mcp_tools:
            del mcp_tools[connection_name]
            cl.user_session.set("mcp_tools", mcp_tools)
        
        # Cleanup plugin from Semantic Kernel
        mcp_plugins = cl.user_session.get("mcp_plugins", {})
        if connection_name in mcp_plugins:
            plugin = mcp_plugins[connection_name]
            
            # Disconnect the plugin if possible
            if hasattr(plugin, 'disconnect'):
                await plugin.disconnect()
            
            # Remove from tracking
            # Note: Semantic Kernel may not have direct plugin removal,
            # so we just track disconnection state
            del mcp_plugins[connection_name]
            cl.user_session.set("mcp_plugins", mcp_plugins)
            
            await cl.Message(content=f"Successfully disconnected {connection_name} from Semantic Kernel").send()
            print(f"Removed MCP plugin {connection_name} from Semantic Kernel")
        else:
            await cl.Message(content=f"MCP connection {connection_name} was not found in active plugins").send()
            
    except Exception as e:
        error_msg = f"Error during MCP disconnection for {connection_name}: {str(e)}"
        await cl.Message(content=error_msg).send()
        print(error_msg)