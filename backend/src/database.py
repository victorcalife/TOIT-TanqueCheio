from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import redis
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

# Redis connection
redis_client = None

def init_database(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize Redis
    global redis_client
    redis_url = app.config.get('REDIS_URL')
    if redis_url:
        try:
            redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            redis_client.ping()
            app.logger.info("Redis connection established")
        except Exception as e:
            app.logger.error(f"Redis connection failed: {e}")
            redis_client = None
    
    return db

def get_redis():
    """Get Redis client instance"""
    return redis_client

# Database utility functions
def create_tables():
    """Create all database tables"""
    db.create_all()

def drop_tables():
    """Drop all database tables"""
    db.drop_all()

def reset_database():
    """Reset database (drop and create all tables)"""
    drop_tables()
    create_tables()

# Cache utilities
def cache_set(key, value, expire=3600):
    """Set value in cache with expiration"""
    if redis_client:
        try:
            return redis_client.setex(key, expire, value)
        except Exception as e:
            print(f"Cache set error: {e}")
    return False

def cache_get(key):
    """Get value from cache"""
    if redis_client:
        try:
            return redis_client.get(key)
        except Exception as e:
            print(f"Cache get error: {e}")
    return None

def cache_delete(key):
    """Delete key from cache"""
    if redis_client:
        try:
            return redis_client.delete(key)
        except Exception as e:
            print(f"Cache delete error: {e}")
    return False

def cache_exists(key):
    """Check if key exists in cache"""
    if redis_client:
        try:
            return redis_client.exists(key)
        except Exception as e:
            print(f"Cache exists error: {e}")
    return False

# Session management for JWT blacklist
def blacklist_token(jti, expires_in):
    """Add token to blacklist"""
    if redis_client:
        try:
            return redis_client.setex(f"blacklist:{jti}", expires_in, "true")
        except Exception as e:
            print(f"Blacklist token error: {e}")
    return False

def is_token_blacklisted(jti):
    """Check if token is blacklisted"""
    if redis_client:
        try:
            return redis_client.exists(f"blacklist:{jti}")
        except Exception as e:
            print(f"Check blacklist error: {e}")
    return False

# Rate limiting utilities
def check_rate_limit(identifier, limit, window):
    """Check if rate limit is exceeded"""
    if not redis_client:
        return False
    
    try:
        key = f"rate_limit:{identifier}"
        current = redis_client.get(key)
        
        if current is None:
            redis_client.setex(key, window, 1)
            return False
        
        if int(current) >= limit:
            return True
        
        redis_client.incr(key)
        return False
    except Exception as e:
        print(f"Rate limit check error: {e}")
        return False

def get_rate_limit_remaining(identifier, limit, window):
    """Get remaining rate limit count"""
    if not redis_client:
        return limit
    
    try:
        key = f"rate_limit:{identifier}"
        current = redis_client.get(key)
        
        if current is None:
            return limit
        
        return max(0, limit - int(current))
    except Exception as e:
        print(f"Rate limit remaining error: {e}")
        return limit

