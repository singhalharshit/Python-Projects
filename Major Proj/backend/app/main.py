"""
FastAPI main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings
from app.core.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Decision Assistant API",
    description="Personalized daily decision assistant for social media creators",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Force allow all for debugging
    # allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Debug logging to file
    with open("startup_log.txt", "a") as f:
        f.write(f"\n--- Startup at {__import__('datetime').datetime.now()} ---\n")
    
    logger.info("Starting Decision Assistant API...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
        with open("startup_log.txt", "a") as f:
            f.write("Database initialized\n")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        with open("startup_log.txt", "a") as f:
            f.write(f"Database init failed: {e}\n")
    
    # Initialize Vector Store
    try:
        from app.core.database import SessionLocal
        from app.models.creator import Creator
        from app.services.intelligence.vector_store import vector_store
        import numpy as np
        
        db = SessionLocal()
        try:
            logger.info("Loading creators into Vector Store...")
            with open("startup_log.txt", "a") as f:
                f.write("Querying creators...\n")
                
            creators = db.query(Creator).filter(Creator.embedding.isnot(None)).all()
            
            with open("startup_log.txt", "a") as f:
                f.write(f"Found {len(creators)} creators with embeddings\n")
            
            if creators:
                embeddings = []
                ids = []
                metadata = []
                
                for c in creators:
                    if c.embedding:
                        embeddings.append(c.embedding)
                        ids.append(c.id)
                        metadata.append({
                            'platform': c.platform,
                            'name': c.name,
                            'handle': c.handle,
                            'follower_count': c.subscriber_count,
                            'language': c.language,
                            'niche': c.niche,
                            'tags': c.tags
                        })
                
                if embeddings:
                    # Convert to numpy array
                    embedding_matrix = np.array(embeddings, dtype=np.float32)
                    vector_store.build_index(embedding_matrix, ids, metadata)
                    logger.info(f"Vector Store initialized with {len(ids)} creators")
                    with open("startup_log.txt", "a") as f:
                        f.write(f"Vector Store index built with {len(ids)} creators\n")
                        return f"{ids} and here the following ids."
                else:
                    logger.warning("No creators with embeddings found in database")
                    return ""
            else:
                logger.warning("No creators found in database")
                
        except Exception as e:
            logger.error(f"Failed to initialize Vector Store: {e}")
            with open("startup_log.txt", "a") as f:
                f.write(f"Vector Store init failed: {e}\n")
                import traceback
                f.write(traceback.format_exc())
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to setup Vector Store context: {e}")
        with open("startup_log.txt", "a") as f:
            f.write(f"Context setup failed: {e}\n")
    
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Decision Assistant API...")


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "message": "Decision Assistant API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2025-12-29T02:05:07Z"
    }


# Import and include routers
from app.api.routes import auth, users, recommendations

app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])


# [NEW] Onboarding API
from app.api.routes import onboarding, decision, actions, competitors, feedback
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(decision.router, prefix="/api/decision", tags=["decision"])
app.include_router(actions.router, prefix="/api/actions", tags=["actions"])
app.include_router(competitors.router, prefix="/api/competitors", tags=["competitors"])
app.include_router(feedback.router, prefix="/api", tags=["feedback-learning"])



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG
    )
