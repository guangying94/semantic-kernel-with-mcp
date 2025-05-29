# RAG MCP Server (Based on Information Assistant)

A Model Context Protocol (MCP) server that interfaces with an Information Assistant service to provide knowledge base querying capabilities.

More information about Information Assistant can be found at [Microsoft Information Assistant Acclerator](https://github.com/microsoft/pubsec-info-assistant).

## Overview

This service provides an MCP interface for interacting with an Information Assistant (IA) knowledge base. It exposes two main functions:

- **Query Knowledge Base**: Ask questions against the knowledge base and get responses with citations
- **Retrieve References**: Get the full content for specific citations

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your IA endpoint:
   ```
   IA_ENDPOINT=https://your-ia-service-endpoint
   ```

## Usage

Start the server:

```
python main.py --debug
```

Optional parameters:
- `--debug`: Enable debug logging

## Docker

Build and run with Docker:

```
docker build -t mcp-server .
docker run -p 8000:8000 -e IA_ENDPOINT=https://your-ia-service-endpoint mcp-server
```

## API

The server implements the Model Context Protocol (MCP) and provides two tools:

- `post_question_to_ia`: Query the knowledge base
- `get_reference`: Retrieve reference content

For more details, see the docstrings in the code.