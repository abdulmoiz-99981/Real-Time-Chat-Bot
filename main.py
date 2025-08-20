from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
from models import ChatRequest, ChatResponse, ErrorResponse
from ai_provider import ai_provider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Chatbot API",
    description="A modern AI chatbot with FastAPI backend and web interface",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface(request: Request):
    """
    Serve the main chat interface
    """
    logger.info("Chat interface requested")
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest):
    """
    Handle chat messages and return AI responses
    """
    try:
        user_message = chat_request.message.strip()
        logger.info(f"Received message: {user_message[:50]}...")
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get AI response
        ai_response = await ai_provider.call_ai_service(user_message)
        
        logger.info(f"AI response generated: {ai_response[:50]}...")
        
        return ChatResponse(reply=ai_response, status="success")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Sorry, I'm having trouble processing your message right now. Please try again."
        )

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "AI Chatbot API"}

@app.get("/api/info")
async def api_info():
    """
    Get API information
    """
    return {
        "name": "AI Chatbot API",
        "version": "1.0.0",
        "description": "A modern AI chatbot with intelligent responses",
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "interface": "/"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
