"""
Rate limiting utility for Calgentic API endpoints
Designed for high-scale applications with millions of users
"""

import time
import json
from typing import Dict, Tuple, Optional
from redis import Redis
import os
from functools import wraps
from flask import request, jsonify, g, session
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        
        # Rate limits (requests per window)
        self.limits = {
            'delete': {'requests': 10, 'window': 600},    # 10 deletes per 10 minutes
            'create': {'requests': 30, 'window': 600},    # 30 creates per 10 minutes  
            'view': {'requests': 100, 'window': 600},     # 100 views per 10 minutes
            'prompt': {'requests': 50, 'window': 600},    # 50 total prompts per 10 minutes
            'batch': {'requests': 5, 'window': 600},      # 5 batch jobs per 10 minutes
        }
    
    def is_allowed(self, user_id: str, action_type: str) -> Tuple[bool, Dict]:
        """
        Check if user is allowed to perform action
        Returns (is_allowed, rate_limit_info)
        """
        if not self.redis or not user_id:
            return True, {}
        
        limit_config = self.limits.get(action_type, self.limits['prompt'])
        max_requests = limit_config['requests']
        window_seconds = limit_config['window']
        
        key = f"rate_limit:{action_type}:{user_id}"
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        try:
            # Remove expired entries
            self.redis.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            current_count = self.redis.zcard(key)
            
            rate_limit_info = {
                'action': action_type,
                'limit': max_requests,
                'remaining': max(0, max_requests - current_count),
                'reset_time': window_start + window_seconds,
                'window_seconds': window_seconds
            }
            
            if current_count >= max_requests:
                logger.warning(f"Rate limit exceeded for user {user_id}, action {action_type}")
                return False, rate_limit_info
            
            # Add current request
            self.redis.zadd(key, {f"{current_time}:{os.urandom(8).hex()}": current_time})
            self.redis.expire(key, window_seconds)
            
            rate_limit_info['remaining'] -= 1
            return True, rate_limit_info
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Allow request if Redis is down
            return True, {'error': 'rate_limiter_unavailable'}
    
    def get_rate_limit_headers(self, rate_limit_info: Dict) -> Dict[str, str]:
        """Generate HTTP headers for rate limiting"""
        if not rate_limit_info or 'error' in rate_limit_info:
            return {}
        
        return {
            'X-RateLimit-Limit': str(rate_limit_info['limit']),
            'X-RateLimit-Remaining': str(rate_limit_info['remaining']),
            'X-RateLimit-Reset': str(rate_limit_info['reset_time']),
            'X-RateLimit-Window': str(rate_limit_info['window_seconds'])
        }

# Global rate limiter instance
rate_limiter = None

def init_rate_limiter(redis_client: Redis):
    """Initialize the global rate limiter"""
    global rate_limiter
    rate_limiter = RateLimiter(redis_client)

def rate_limit(action_type: str):
    """
    Decorator for rate limiting API endpoints
    Usage: @rate_limit('delete')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not rate_limiter:
                return f(*args, **kwargs)
            
            # Get user ID from session
            try:
                user_session = getattr(g, 'user_session', None) or session.get('user', {})
                user_id = user_session.get('db_user_id') or user_session.get('id')
                logger.debug(f"Rate limiter: user_session={user_session}, user_id={user_id}")
            except Exception as e:
                logger.error(f"Rate limiter session access error: {e}")
                user_id = None
            
            if not user_id:
                logger.warning(f"Rate limiting skipped - no user ID found for {action_type}")
                return f(*args, **kwargs)
            
            # Check rate limit
            is_allowed, rate_info = rate_limiter.is_allowed(user_id, action_type)
            
            if not is_allowed:
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many {action_type} requests. Please try again later.',
                    'rate_limit': rate_info
                })
                response.status_code = 429
                
                # Add rate limit headers
                for header, value in rate_limiter.get_rate_limit_headers(rate_info).items():
                    response.headers[header] = value
                
                return response
            
            # Execute the function
            response = f(*args, **kwargs)
            
            # Add rate limit headers to successful responses
            if hasattr(response, 'headers'):
                for header, value in rate_limiter.get_rate_limit_headers(rate_info).items():
                    response.headers[header] = value
            
            return response
            
        return decorated_function
    return decorator

def check_global_rate_limit(user_id: str) -> Tuple[bool, Dict]:
    """Check global rate limit for a user across all actions"""
    if not rate_limiter or not user_id:
        return True, {}
    
    # Global limit: 200 requests per hour
    key = f"rate_limit:global:{user_id}"
    current_time = int(time.time())
    window_seconds = 3600  # 1 hour
    window_start = current_time - window_seconds
    max_requests = 200
    
    try:
        # Remove expired entries
        rate_limiter.redis.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        current_count = rate_limiter.redis.zcard(key)
        
        rate_limit_info = {
            'action': 'global',
            'limit': max_requests,
            'remaining': max(0, max_requests - current_count),
            'reset_time': window_start + window_seconds,
            'window_seconds': window_seconds
        }
        
        if current_count >= max_requests:
            logger.warning(f"Global rate limit exceeded for user {user_id}")
            return False, rate_limit_info
        
        # Add current request
        rate_limiter.redis.zadd(key, {f"{current_time}:{os.urandom(8).hex()}": current_time})
        rate_limiter.redis.expire(key, window_seconds)
        
        rate_limit_info['remaining'] -= 1
        return True, rate_limit_info
        
    except Exception as e:
        logger.error(f"Global rate limiter error: {e}")
        return True, {'error': 'rate_limiter_unavailable'}