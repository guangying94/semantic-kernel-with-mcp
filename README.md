# Semantic Kernel MCP Integration

A powerful conversational AI application that integrates Microsoft Semantic Kernel with Model Context Protocol (MCP) servers through a beautiful Chainlit web interface.

## 🚀 Features

- **AI Orchestration**: Microsoft Semantic Kernel for intelligent function calling and AI workflows
- **Tool Integration**: Dynamic connection to MCP servers for extensible tool capabilities
- **Web Interface**: Beautiful, real-time chat interface powered by Chainlit
- **Azure OpenAI**: Enterprise-grade language model integration
- **Real-time Debugging**: Live logging and thought process visualization
- **Dynamic Plugin Management**: Automatic MCP server discovery and integration

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Chainlit UI   │◄──►│ Semantic Kernel  │◄──►│  Azure OpenAI   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│  MCP Servers    │◄──►│   MCP Plugins    │
│  (Tools)        │    │  (Integration)   │
└─────────────────┘    └──────────────────┘
```

## 📋 Prerequisites

- Python 3.8+
- Azure OpenAI account and deployment
- MCP servers (optional, included examples available)

## ⚙️ Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_BASE_URL=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-01
```

## 🔧 Local Development

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
```bash
cp .env.example .env
# Edit .env with your Azure OpenAI credentials
```

### 3. Run the Application
```bash
chainlit run main.py
```

The application will be available at `http://localhost:8000`

### 5. Connect MCP Servers (Optional)

The repository includes example MCP servers:

#### SQL MCP Server
Follow the instructions in the `sql-mcp` directory to set up a SQL MCP server that can handle database queries.

#### RAG MCP Server
Follow the instructions in the `rag-mcp` directory to set up a RAG MCP server for document retrieval and search capabilities.

#### Browser MCP Server
Follow the instructions in the `browser-mcp` directory to set up a Browser MCP server for web browsing and scraping tools.

## 🐳 Docker Deployment

### Build and Run
```bash
# Build the image
docker build -t semantic-kernel-mcp .

# Run the container
docker run -p 8000:8000 --env-file .env semantic-kernel-mcp
```

## 🔌 MCP Server Integration

### Connecting to MCP Servers

1. Start your MCP servers
2. In the Chainlit interface, add the MCP server URLs in the settings
3. Available tools will be dynamically registered with Semantic Kernel
4. Tools can be invoked through natural language conversation

### Example MCP Servers Included

- **SQL MCP**: Database querying and management tools
- **RAG MCP**: Document retrieval and search capabilities  
- **Browser MCP**: Web browsing and scraping tools

## 🛠️ Development

### Project Structure
```
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── chainlit.md            # Chainlit configuration
├── .chainlit/             # Chainlit settings
├── sql-mcp/               # SQL MCP server
├── rag-mcp/               # RAG MCP server
└── browser-mcp/           # Browser MCP server
```

### Key Components

- **CapturingHandler**: Custom logging for debugging AI interactions
- **MCP Integration**: Dynamic plugin loading and tool registration
- **Chainlit Handlers**: Chat interface and user session management
- **Semantic Kernel**: AI orchestration and function calling

## 📚 Usage Examples

### Database Queries (with SQL MCP)
```
User: "How many customers do I have？ can you summarize their demographics?"
AI: [Executes SQL query through MCP and returns results]
```

### Document Search (with RAG MCP)
```
User: "Find information about machine learning in our documents"
AI: [Searches documents and provides relevant information]
```

## 🔧 Troubleshooting

### Common Issues

**Missing Environment Variables**
```bash
# Verify all required environment variables are set
python -c "import os; print([k for k in ['AZURE_OPENAI_CHAT_DEPLOYMENT_NAME', 'AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_BASE_URL', 'AZURE_OPENAI_API_VERSION'] if not os.getenv(k)])"
```

**MCP Connection Issues**
- Ensure MCP servers are running and accessible
- Check firewall and network connectivity
- Verify MCP server URLs and ports

**Azure OpenAI Connection**
- Validate API key and endpoint URL
- Ensure deployment name matches your Azure configuration
- Check API version compatibility

## 📞 Support

For issues and questions:
- Create an issue in the GitHub repository
- Check existing documentation and examples
- Review logs for error details

---

Built with ❤️ using [Microsoft Semantic Kernel](https://github.com/microsoft/semantic-kernel), [Model Context Protocol](https://github.com/modelcontextprotocol), and [Chainlit](https://github.com/Chainlit/chainlit)