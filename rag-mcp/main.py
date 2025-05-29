# server.py
from mcp.server.fastmcp import FastMCP
import os
import json
import logging
import requests
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional
from requests.exceptions import RequestException, Timeout, ConnectionError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get environment variables with validation
IA_ENDPOINT = os.getenv("IA_ENDPOINT")
if not IA_ENDPOINT:
    logger.error("IA_ENDPOINT environment variable not set. Please check your .env file.")
    raise ValueError("IA_ENDPOINT environment variable is required")

# Create an MCP server
mcp = FastMCP("Info Assistant with MCP Server")

@mcp.tool()
def post_question_to_ia(query: str, folder: str = "All", model_name: str = "gpt-4.1", top_k: int = 5) -> str:
    """Retrieve answer from internal knowledge base.
    
    This function sends a query to the Information Assistant service and returns the response.
    
    Args:
        query: The user's question to be answered by the knowledge base
        folder: The specific knowledge folder to search in (defaults to 'All' if not provided)
        model_name: The language model to be used for the query (defaults to 'gpt-4.1' if not provided)
        top_k: The number of top results to return (defaults to 5 if not provided)
        
    Returns:
        A JSON string containing the response from the IA service, including the answer and references
    
    Raises:
        RequestException: If there's an issue with the HTTP request
        ValueError: If required parameters are missing or invalid
        json.JSONDecodeError: If there's an issue parsing the response
    """
    if not query:
        logger.error("Query parameter is required")
        return json.dumps({"error": "Query parameter is required"})

    url = f"{IA_ENDPOINT}/chat"
    data = {
        "history": [{"user": query}],
        "approach": 1,
        "overrides": {
            "semantic_ranker": True,
            "semantic_captions": False,
            "top": top_k,
            "suggest_followup_questions": False,
            "user_persona": "Analyst",
            "system_persona": "AI Assistant",
            "ai_persona": "",
            "response_length": 2048,
            "response_temp": 0.6,
            "selected_folders": folder,
            "selected_tags": "",
            "selected_model": model_name
        },
        "citation_lookup": {},
        "thought_chain": {}
    }
    
    try:
        logger.info(f"Sending query to IA service: {query[:50]}...")
        response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        reference: List[Dict[str, Any]] = []
        
        # Process the response to concatenate all content
        full_sentence = ""
        for line in response.iter_lines():
            if line:
                try:
                    json_line = json.loads(line)
                    content = json_line.get("content", "")
                    citation = json_line.get("work_citation_lookup", {})
                    if content:
                        full_sentence += content
                    if citation:
                        reference = [
                            {
                                "citation_key": key,
                                "citation": value["citation"].split('/content/',1)[1] if '/content/' in value["citation"] else value["citation"],
                                "page_number": value["page_number"],
                            }
                            for key, value in citation.items()
                        ]
                except json.JSONDecodeError as e:
                    logger.warning(f"Could not parse response line: {e}")
                    continue
        
        result = {
            "response": full_sentence,
            "reference": reference,
        }
        
        logger.info(f"Successfully retrieved response from IA service")
        return json.dumps(result)
        
    except Timeout:
        logger.error("Request to IA service timed out")
        return json.dumps({"error": "Request to IA service timed out"})
    except ConnectionError:
        logger.error(f"Could not connect to IA service at {IA_ENDPOINT}")
        return json.dumps({"error": f"Could not connect to IA service"})
    except RequestException as e:
        logger.error(f"Error communicating with IA service: {str(e)}")
        return json.dumps({"error": f"Error communicating with IA service: {str(e)}"})
    except Exception as e:
        logger.error(f"Unexpected error in post_question_to_ia: {str(e)}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})

@mcp.tool()
def get_reference(source: str) -> str:
    """Retrieve the content for a given source.
    
    This function fetches the reference information and content for a specific source.
    
    Args:
        source: The source identifier for which to retrieve the reference
        
    Returns:
        A JSON string containing the file URI, page number, and content
        
    Raises:
        RequestException: If there's an issue with the HTTP request
        ValueError: If required parameters are missing or invalid
        json.JSONDecodeError: If there's an issue parsing the response
    """
    if not source:
        logger.error("Source parameter is required")
        return json.dumps({"error": "Source parameter is required"})
    
    url = f"{IA_ENDPOINT}/getcitation"
    data = {
        "citation": source,
    }
    
    try:
        logger.info(f"Requesting citation for source: {source[:50]}...")
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        
        try:
            result = response.json()
            
            citation = {
                "file_uri": result.get("file_uri", ""),
                "page_number": result.get("pages", ""),
                "content": result.get("content", ""),
            }
            
            logger.info(f"Successfully retrieved citation")
            return json.dumps(citation)
            
        except json.JSONDecodeError as e:
            logger.error(f"Could not parse JSON response: {str(e)}")
            return json.dumps({"error": f"Could not parse response from citation service"})
            
    except Timeout:
        logger.error("Request to citation service timed out")
        return json.dumps({"error": "Request to citation service timed out"})
    except ConnectionError:
        logger.error(f"Could not connect to citation service at {IA_ENDPOINT}")
        return json.dumps({"error": f"Could not connect to citation service"})
    except RequestException as e:
        logger.error(f"Error communicating with citation service: {str(e)}")
        return json.dumps({"error": f"Error communicating with citation service: {str(e)}"})
    except Exception as e:
        logger.error(f"Unexpected error in get_reference: {str(e)}")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})

if __name__ == "__main__":
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="MCP Server for Information Assistant")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode with detailed logging")
    args = parser.parse_args()
    
    # Set logging level based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    logger.info(f"Starting MCP Server...")
    
    try:
        # Run the MCP server with Server-Sent Events transport
        mcp.run(transport="sse")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        raise