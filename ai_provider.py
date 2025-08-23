from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
import time
import json
import asyncio
from datetime import datetime
import uvicorn

app = FastAPI(
    title="AI Chat API",
    description="OpenAI-compatible chat completion API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Models
class Message(BaseModel):
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")
    name: Optional[str] = Field(None, description="Name of the sender")

class ChatCompletionRequest(BaseModel):
    model: str = Field(default="gpt-3.5-turbo", description="Model to use")
    messages: List[Message] = Field(..., description="List of messages")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    stream: Optional[bool] = Field(default=False)
    stop: Optional[List[str]] = Field(default=None)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    user: Optional[str] = Field(default=None)

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Usage

class StreamChoice(BaseModel):
    index: int
    delta: Dict[str, Any]
    finish_reason: Optional[str]

class ChatCompletionStreamResponse(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[StreamChoice]

class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str
    permission: List[Dict] = []
    root: str
    parent: Optional[str] = None

class ModelsResponse(BaseModel):
    object: str = "list"
    data: List[ModelInfo]

# Available models
AVAILABLE_MODELS = {
    "gpt-3.5-turbo": {
        "id": "gpt-3.5-turbo",
        "object": "model",
        "created": 1677610602,
        "owned_by": "openai",
        "root": "gpt-3.5-turbo",
        "parent": None
    },
    "gpt-4": {
        "id": "gpt-4",
        "object": "model", 
        "created": 1687882411,
        "owned_by": "openai",
        "root": "gpt-4",
        "parent": None
    },
    "gpt-4-turbo": {
        "id": "gpt-4-turbo",
        "object": "model",
        "created": 1712361441,
        "owned_by": "openai", 
        "root": "gpt-4-turbo",
        "parent": None
    }
}

# Authentication
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # In production, validate against your database
    valid_keys = ["sk-test123", "sk-prod456"]  # Replace with actual key validation
    if credentials.credentials not in valid_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

# Mock AI response generator
def generate_ai_response(messages: List[Message], model: str, temperature: float) -> str:
    """
    Replace this with your actual AI model integration
    This is a mock response generator
    """
    last_message = messages[-1].content if messages else ""
    
    # Mock responses based on input
    responses = [
        f"I understand you're asking about: {last_message[:50]}... Here's my response.",
        "That's an interesting question. Let me think about that.",
        "Based on what you've shared, I would suggest...",
        "I can help you with that. Here are some thoughts:",
        "That's a great point. From my perspective..."
    ]
    
    # Simple hash-based selection for consistency
    response_idx = hash(last_message) % len(responses)
    base_response = responses[response_idx]
    
    # Add some variation based on temperature
    if temperature > 1.0:
        base_response += " I'm feeling quite creative today!"
    elif temperature < 0.3:
        base_response = "Based on the data, " + base_response.lower()
    
    return base_response

def count_tokens(text: str) -> int:
    """Simple token counter - replace with actual tokenizer"""
    return len(text.split())

# API Endpoints
@app.get("/")
async def root():
    return {"message": "AI Chat API", "version": "1.0.0"}

@app.get("/v1/models", response_model=ModelsResponse)
async def list_models(api_key: str = Depends(verify_api_key)):
    models = [ModelInfo(**model_info) for model_info in AVAILABLE_MODELS.values()]
    return ModelsResponse(data=models)

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    api_key: str = Depends(verify_api_key)
):
    # Validate model
    if request.model not in AVAILABLE_MODELS:
        raise HTTPException(status_code=400, detail=f"Model {request.model} not found")
    
    # Generate response
    response_content = generate_ai_response(
        request.messages, 
        request.model, 
        request.temperature
    )
    
    # Calculate tokens
    prompt_tokens = sum(count_tokens(msg.content) for msg in request.messages)
    completion_tokens = count_tokens(response_content)
    
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"
    
    if request.stream:
        # Streaming response
        async def generate_stream():
            words = response_content.split()
            for i, word in enumerate(words):
                chunk = ChatCompletionStreamResponse(
                    id=completion_id,
                    created=int(time.time()),
                    model=request.model,
                    choices=[StreamChoice(
                        index=0,
                        delta={"content": word + " "} if i < len(words) - 1 else {"content": word},
                        finish_reason=None if i < len(words) - 1 else "stop"
                    )]
                )
                yield f"data: {chunk.json()}\n\n"
                await asyncio.sleep(0.1)  # Simulate streaming delay
            
            yield "data: [DONE]\n\n"
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(generate_stream(), media_type="text/plain")
    
    else:
        # Regular response
        return ChatCompletionResponse(
            id=completion_id,
            created=int(time.time()),
            model=request.model,
            choices=[Choice(
                index=0,
                message=Message(role="assistant", content=response_content),
                finish_reason="stop"
            )],
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            )
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
