# AI Chatbot UI with Local Models

A modern, responsive chatbot interface built with React and TypeScript, featuring real-time AI conversations with local language models.

![Demo](demo/image.png)

## ✨ Features

- 🎨 **Modern UI**: Clean, responsive design with dark/light theme support
- 🤖 **Local AI Models**: Supports both Ollama and Hugging Face Transformers
- ⚡ **Real-time Streaming**: WebSocket-based streaming responses
- 💬 **Chat History**: Sidebar with conversation management
- 🎯 **TypeScript**: Fully typed for better development experience
- 📱 **Mobile Responsive**: Works seamlessly on desktop and mobile

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd chatbot-ui-master
   ```

2. **Install frontend dependencies**
   ```bash
   npm install
   ```

3. **Set up Python backend**
   ```bash
   cd testbackend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## 🛠️ Usage

### Option 1: Hugging Face Transformers (Recommended for beginners)

1. **Start the backend**
   ```bash
   cd testbackend
   source venv/bin/activate
   python test_huggingface.py
   ```

2. **Start the frontend**
   ```bash
   npm run dev
   ```

3. **Open your browser** to `http://localhost:8501`

### Option 2: Ollama (Better performance)

1. **Install Ollama**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Pull a model**
   ```bash
   ollama pull llama3.2:1b  # or any other model
   ```

3. **Update frontend WebSocket URL**
   ```typescript
   // In src/pages/chat/chat.tsx
   const socket = new WebSocket("ws://localhost:8090");
   ```

4. **Start Ollama backend**
   ```bash
   cd testbackend
   source venv/bin/activate
   python test.py
   ```

5. **Start frontend**
   ```bash
   npm run dev
   ```

## 🏗️ Project Structure

```
chatbot-ui-master/
├── src/
│   ├── components/          # React components
│   ├── pages/              # Main pages
│   ├── context/            # React contexts
│   └── interfaces/         # TypeScript interfaces
├── testbackend/
│   ├── test.py             # Ollama backend
│   ├── test_huggingface.py # Hugging Face backend
│   └── requirements.txt    # Python dependencies
└── package.json           # Node.js dependencies
```

## 🎯 Available Models

### Hugging Face Transformers
- `distilgpt2` (Default - lightweight)
- `gpt2`
- `microsoft/DialoGPT-small`
- `microsoft/DialoGPT-medium`

### Ollama
- `llama3.2:1b` (Recommended)
- `llama3.2:3b`
- `phi3:mini`
- `gemma2:2b`

## 🔧 Configuration

### Backend Ports
- Hugging Face backend: `8091`
- Ollama backend: `8090`
- Frontend: `8501`

### Environment Variables
```bash
# Backend port (optional)
PORT=8090

# Model selection (optional)
MODEL_NAME=distilgpt2
```

## 🛠️ Development

### Build for Production
```bash
npm run build
npm run serve
```

### Linting
```bash
npm run lint
```

## 📦 Dependencies

### Frontend
- React 18
- TypeScript
- Tailwind CSS
- Framer Motion
- Radix UI Components

### Backend
- websockets
- aiohttp
- transformers
- torch
- ollama (optional)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with React and TypeScript
- UI components from Radix UI
- Styling with Tailwind CSS
- AI models from Hugging Face and Ollama
- Original UI design inspired by [Vercel's AI Chatbot](https://github.com/vercel/ai-chatbot)

## 🐛 Troubleshooting

### Common Issues

1. **WebSocket connection failed**
   - Ensure backend is running on the correct port
   - Check firewall settings

2. **Model loading errors**
   - Verify Python dependencies are installed
   - Check available system memory

3. **Frontend build issues**
   - Clear node_modules and reinstall: `rm -rf node_modules package-lock.json && npm install`

For more help, please open an issue in the repository.

## Credits

Original chatbot UI template by:
- [Leon Binder](https://github.com/LeonBinder)
- [Christoph Handschuh](https://github.com/ChristophHandschuh)

Extended with local AI model integration.
