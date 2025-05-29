# Playwright Browser MCP Server
This project implements a Model Context Protocol (MCP) server for browser automation using Playwright. The source code is based on this repository: [Playwright MCP Server](https://github.com/microsoft/playwright-mcp).

To deploy this MCP server as container, you can use the provided Dockerfile. The server is designed to run in a containerized environment, making it easy to deploy and scale.

Steps to deploy the MCP server:
1. **Clone the Repository**: 
```bash
git clone https://github.com/microsoft/playwright-mcp
cd playwright-mcp
```
2. **Build the Docker Image**:
```bash
# Replace the dockerfile with the one provided in this repository
docker build -t playwright-mcp .
```
3. **Run the Docker Container**:
```bash
docker run -p 8931:8931 playwright-mcp
```