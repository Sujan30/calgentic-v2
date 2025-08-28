"""
Metrics and monitoring utilities for Calgentic
Designed to track performance and usage patterns for millions of users
"""

import time
import json
from typing import Dict, Optional, Any
from datetime import datetime, timezone
from redis import Redis
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.prefix = "metrics:calgentic"
    
    def record_operation(self, operation: str, user_id: str, 
                        success: bool = True, 
                        processing_time_ms: Optional[int] = None,
                        additional_data: Optional[Dict] = None):
        """
        Record an operation for metrics tracking
        """
        if not self.redis:
            return
        
        timestamp = int(time.time())
        date_key = datetime.now().strftime('%Y-%m-%d')
        hour_key = datetime.now().strftime('%Y-%m-%d:%H')
        
        try:
            # Track operation counts
            self.redis.hincrby(f"{self.prefix}:operations:daily:{date_key}", operation, 1)
            self.redis.hincrby(f"{self.prefix}:operations:hourly:{hour_key}", operation, 1)
            
            # Track success/failure rates
            status = "success" if success else "error"
            self.redis.hincrby(f"{self.prefix}:status:daily:{date_key}", f"{operation}:{status}", 1)
            
            # Track user activity
            if user_id:
                self.redis.sadd(f"{self.prefix}:active_users:daily:{date_key}", user_id)
                self.redis.sadd(f"{self.prefix}:active_users:hourly:{hour_key}", user_id)
                
                # User-specific operation count
                self.redis.hincrby(f"{self.prefix}:user_operations:{user_id}:{date_key}", operation, 1)
            
            # Track processing times for performance monitoring
            if processing_time_ms is not None:
                self.redis.lpush(f"{self.prefix}:processing_times:{operation}:{hour_key}", processing_time_ms)
                self.redis.ltrim(f"{self.prefix}:processing_times:{operation}:{hour_key}", 0, 999)  # Keep last 1000
            
            # Set expiration for cleanup (30 days for daily, 7 days for hourly, 1 day for processing times)
            self.redis.expire(f"{self.prefix}:operations:daily:{date_key}", 30 * 24 * 3600)
            self.redis.expire(f"{self.prefix}:operations:hourly:{hour_key}", 7 * 24 * 3600)
            self.redis.expire(f"{self.prefix}:status:daily:{date_key}", 30 * 24 * 3600)
            self.redis.expire(f"{self.prefix}:active_users:daily:{date_key}", 30 * 24 * 3600)
            self.redis.expire(f"{self.prefix}:active_users:hourly:{hour_key}", 7 * 24 * 3600)
            if user_id:
                self.redis.expire(f"{self.prefix}:user_operations:{user_id}:{date_key}", 30 * 24 * 3600)
            if processing_time_ms is not None:
                self.redis.expire(f"{self.prefix}:processing_times:{operation}:{hour_key}", 24 * 3600)
                
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")
    
    def record_delete_operation(self, user_id: str, success: bool, 
                               processing_time_ms: int,
                               event_id: Optional[str] = None,
                               calendar_id: str = "primary",
                               retry_count: int = 0):
        """
        Specialized method for recording delete operations
        """
        additional_data = {
            'event_id': event_id,
            'calendar_id': calendar_id,
            'retry_count': retry_count
        }
        
        self.record_operation('delete', user_id, success, processing_time_ms, additional_data)
        
        # Track delete-specific metrics
        if not self.redis:
            return
            
        date_key = datetime.now().strftime('%Y-%m-%d')
        hour_key = datetime.now().strftime('%Y-%m-%d:%H')
        
        try:
            # Track retry patterns
            if retry_count > 0:
                self.redis.hincrby(f"{self.prefix}:retries:daily:{date_key}", f"delete:{retry_count}", 1)
            
            # Track calendar usage
            self.redis.hincrby(f"{self.prefix}:calendar_usage:daily:{date_key}", f"delete:{calendar_id}", 1)
            
            # Set expiration
            self.redis.expire(f"{self.prefix}:retries:daily:{date_key}", 30 * 24 * 3600)
            self.redis.expire(f"{self.prefix}:calendar_usage:daily:{date_key}", 30 * 24 * 3600)
            
        except Exception as e:
            logger.error(f"Failed to record delete metrics: {e}")
    
    def get_metrics_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get a summary of metrics for the specified number of days
        """
        if not self.redis:
            return {}
        
        summary = {
            'operations': {},
            'success_rates': {},
            'active_users': {},
            'processing_times': {}
        }
        
        try:
            from datetime import date, timedelta
            
            for i in range(days):
                date_key = (date.today() - timedelta(days=i)).strftime('%Y-%m-%d')
                
                # Get operation counts
                operations = self.redis.hgetall(f"{self.prefix}:operations:daily:{date_key}")
                if operations:
                    summary['operations'][date_key] = {k.decode(): int(v) for k, v in operations.items()}
                
                # Get success rates
                statuses = self.redis.hgetall(f"{self.prefix}:status:daily:{date_key}")
                if statuses:
                    summary['success_rates'][date_key] = {k.decode(): int(v) for k, v in statuses.items()}
                
                # Get active users count
                active_users = self.redis.scard(f"{self.prefix}:active_users:daily:{date_key}")
                summary['active_users'][date_key] = active_users
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {}
    
    def get_delete_metrics(self) -> Dict[str, Any]:
        """
        Get specific metrics for delete operations
        """
        if not self.redis:
            return {}
        
        try:
            from datetime import date, timedelta
            
            today = date.today().strftime('%Y-%m-%d')
            yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Get delete operation counts
            today_ops = self.redis.hgetall(f"{self.prefix}:operations:daily:{today}")
            yesterday_ops = self.redis.hgetall(f"{self.prefix}:operations:daily:{yesterday}")
            
            # Get delete success rates
            today_status = self.redis.hgetall(f"{self.prefix}:status:daily:{today}")
            yesterday_status = self.redis.hgetall(f"{self.prefix}:status:daily:{yesterday}")
            
            # Get retry patterns
            today_retries = self.redis.hgetall(f"{self.prefix}:retries:daily:{today}")
            
            delete_metrics = {
                'deletes_today': int(today_ops.get(b'delete', 0)),
                'deletes_yesterday': int(yesterday_ops.get(b'delete', 0)),
                'success_today': int(today_status.get(b'delete:success', 0)),
                'errors_today': int(today_status.get(b'delete:error', 0)),
                'success_yesterday': int(yesterday_status.get(b'delete:success', 0)),
                'errors_yesterday': int(yesterday_status.get(b'delete:error', 0)),
                'retry_patterns': {k.decode(): int(v) for k, v in today_retries.items()},
            }
            
            # Calculate success rates
            if delete_metrics['deletes_today'] > 0:
                delete_metrics['success_rate_today'] = delete_metrics['success_today'] / delete_metrics['deletes_today']
            else:
                delete_metrics['success_rate_today'] = 0
                
            if delete_metrics['deletes_yesterday'] > 0:
                delete_metrics['success_rate_yesterday'] = delete_metrics['success_yesterday'] / delete_metrics['deletes_yesterday']
            else:
                delete_metrics['success_rate_yesterday'] = 0
            
            return delete_metrics
            
        except Exception as e:
            logger.error(f"Failed to get delete metrics: {e}")
            return {}

# Global metrics collector
metrics_collector = None

def init_metrics(redis_client: Redis):
    """Initialize the global metrics collector"""
    global metrics_collector
    metrics_collector = MetricsCollector(redis_client)

def record_operation_metric(operation: str, user_id: str, success: bool = True, 
                           processing_time_ms: Optional[int] = None):
    """Convenience function to record operation metrics"""
    if metrics_collector:
        metrics_collector.record_operation(operation, user_id, success, processing_time_ms)

def record_delete_metric(user_id: str, success: bool, processing_time_ms: int,
                        event_id: Optional[str] = None, calendar_id: str = "primary", 
                        retry_count: int = 0):
    """Convenience function to record delete metrics"""
    if metrics_collector:
        metrics_collector.record_delete_operation(
            user_id, success, processing_time_ms, event_id, calendar_id, retry_count
        )