"""
Batch processing queue system for Calgentic
Handles multiple event operations (create/delete) for millions of users
"""

import json
import uuid
import time
from typing import Dict, List, Any, Optional, Tuple
from redis import Redis
import logging
from datetime import datetime, timezone
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import main
from metrics import record_operation_metric

logger = logging.getLogger(__name__)

class BatchJobStatus:
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BatchQueue:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.job_prefix = "batch_job"
        self.queue_key = "batch_queue"
        self.user_jobs_prefix = "user_batch_jobs"
        self.max_concurrent_jobs = 10
        self.job_timeout = 300  # 5 minutes
        
    def create_batch_job(self, user_id: str, job_type: str, operations: List[Dict], 
                        user_tz: str, tokens: Dict) -> str:
        """
        Create a new batch job for processing multiple operations
        """
        job_id = str(uuid.uuid4())
        job_data = {
            'id': job_id,
            'user_id': user_id,
            'job_type': job_type,  # 'batch_create' or 'batch_delete'
            'operations': operations,
            'user_tz': user_tz,
            'tokens': tokens,
            'status': BatchJobStatus.PENDING,
            'created_at': time.time(),
            'updated_at': time.time(),
            'progress': {
                'total': len(operations),
                'completed': 0,
                'failed': 0,
                'current_operation': None
            },
            'results': [],
            'errors': []
        }
        
        try:
            # Store job data
            self.redis.setex(
                f"{self.job_prefix}:{job_id}",
                self.job_timeout,
                json.dumps(job_data)
            )
            
            # Add to processing queue
            self.redis.lpush(self.queue_key, job_id)
            
            # Track user's jobs
            self.redis.sadd(f"{self.user_jobs_prefix}:{user_id}", job_id)
            self.redis.expire(f"{self.user_jobs_prefix}:{user_id}", self.job_timeout)
            
            logger.info(f"Created batch job {job_id} for user {user_id} with {len(operations)} operations")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to create batch job: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get current status of a batch job"""
        try:
            job_data = self.redis.get(f"{self.job_prefix}:{job_id}")
            if job_data:
                return json.loads(job_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return None
    
    def update_job_progress(self, job_id: str, completed: int = None, failed: int = None, 
                           current_operation: str = None, result: Dict = None, error: str = None):
        """Update job progress and results"""
        try:
            job_data = self.get_job_status(job_id)
            if not job_data:
                return False
            
            if completed is not None:
                job_data['progress']['completed'] = completed
            if failed is not None:
                job_data['progress']['failed'] = failed
            if current_operation:
                job_data['progress']['current_operation'] = current_operation
            if result:
                job_data['results'].append(result)
            if error:
                job_data['errors'].append({
                    'error': error,
                    'timestamp': time.time()
                })
            
            job_data['updated_at'] = time.time()
            
            # Update status based on progress
            total = job_data['progress']['total']
            completed_count = job_data['progress']['completed']
            failed_count = job_data['progress']['failed']
            
            if completed_count + failed_count >= total:
                job_data['status'] = BatchJobStatus.COMPLETED
            elif job_data['status'] == BatchJobStatus.PENDING:
                job_data['status'] = BatchJobStatus.PROCESSING
            
            self.redis.setex(
                f"{self.job_prefix}:{job_id}",
                self.job_timeout,
                json.dumps(job_data)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update job progress for {job_id}: {e}")
            return False
    
    def cancel_job(self, job_id: str, user_id: str) -> bool:
        """Cancel a batch job"""
        try:
            job_data = self.get_job_status(job_id)
            if not job_data or job_data['user_id'] != user_id:
                return False
            
            job_data['status'] = BatchJobStatus.CANCELLED
            job_data['updated_at'] = time.time()
            
            self.redis.setex(
                f"{self.job_prefix}:{job_id}",
                self.job_timeout,
                json.dumps(job_data)
            )
            
            logger.info(f"Cancelled batch job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    def get_user_jobs(self, user_id: str) -> List[Dict]:
        """Get all jobs for a user"""
        try:
            job_ids = self.redis.smembers(f"{self.user_jobs_prefix}:{user_id}")
            jobs = []
            
            for job_id in job_ids:
                job_data = self.get_job_status(job_id.decode())
                if job_data:
                    # Remove sensitive data
                    safe_job_data = {
                        'id': job_data['id'],
                        'job_type': job_data['job_type'],
                        'status': job_data['status'],
                        'progress': job_data['progress'],
                        'created_at': job_data['created_at'],
                        'updated_at': job_data['updated_at'],
                        'errors': job_data.get('errors', [])
                    }
                    jobs.append(safe_job_data)
            
            return sorted(jobs, key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get user jobs for {user_id}: {e}")
            return []

class BatchProcessor:
    def __init__(self, redis_client: Redis, max_workers: int = 5):
        self.queue = BatchQueue(redis_client)
        self.max_workers = max_workers
        self.running = False
        self.worker_thread = None
        
    def start_processing(self):
        """Start the batch job processor"""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_jobs, daemon=True)
        self.worker_thread.start()
        logger.info(f"Started batch processor with {self.max_workers} workers")
    
    def stop_processing(self):
        """Stop the batch job processor"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=30)
        logger.info("Stopped batch processor")
    
    def _process_jobs(self):
        """Main processing loop"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while self.running:
                try:
                    # Get next job from queue (blocking with timeout)
                    job_result = self.queue.redis.brpop(self.queue.queue_key, timeout=5)
                    
                    if not job_result:
                        continue
                    
                    job_id = job_result[1].decode()
                    job_data = self.queue.get_job_status(job_id)
                    
                    if not job_data or job_data['status'] == BatchJobStatus.CANCELLED:
                        continue
                    
                    # Process job in thread pool
                    future = executor.submit(self._process_single_job, job_data)
                    
                except Exception as e:
                    logger.error(f"Error in batch processing loop: {e}")
                    time.sleep(1)
    
    def _process_single_job(self, job_data: Dict):
        """Process a single batch job"""
        job_id = job_data['id']
        logger.info(f"Processing batch job {job_id} with {len(job_data['operations'])} operations")
        
        try:
            # Update status to processing
            self.queue.update_job_progress(job_id)
            
            completed = 0
            failed = 0
            
            for i, operation in enumerate(job_data['operations']):
                # Check if job was cancelled
                current_job_data = self.queue.get_job_status(job_id)
                if not current_job_data or current_job_data['status'] == BatchJobStatus.CANCELLED:
                    logger.info(f"Job {job_id} was cancelled, stopping processing")
                    return
                
                try:
                    # Update current operation
                    operation_desc = f"Processing operation {i+1}/{len(job_data['operations'])}"
                    self.queue.update_job_progress(job_id, current_operation=operation_desc)
                    
                    # Process the operation
                    result = self._process_operation(operation, job_data)
                    
                    if result.get('success'):
                        completed += 1
                        self.queue.update_job_progress(job_id, completed=completed, result=result)
                        
                        # Record metrics
                        record_operation_metric(
                            operation=job_data['job_type'],
                            user_id=job_data['user_id'],
                            success=True,
                            processing_time_ms=result.get('processing_time_ms', 0)
                        )
                    else:
                        failed += 1
                        error_msg = result.get('error', 'Unknown error')
                        self.queue.update_job_progress(
                            job_id, 
                            failed=failed, 
                            error=f"Operation {i+1}: {error_msg}"
                        )
                        
                        # Record metrics
                        record_operation_metric(
                            operation=job_data['job_type'],
                            user_id=job_data['user_id'],
                            success=False
                        )
                    
                    # Small delay to prevent overwhelming the API
                    time.sleep(0.1)
                    
                except Exception as e:
                    failed += 1
                    error_msg = f"Operation {i+1} failed: {str(e)}"
                    logger.error(error_msg)
                    self.queue.update_job_progress(job_id, failed=failed, error=error_msg)
            
            # Final update
            self.queue.update_job_progress(
                job_id, 
                completed=completed, 
                failed=failed,
                current_operation="Completed"
            )
            
            logger.info(f"Completed batch job {job_id}: {completed} successful, {failed} failed")
            
        except Exception as e:
            logger.error(f"Fatal error processing batch job {job_id}: {e}")
            self.queue.update_job_progress(job_id, error=f"Fatal error: {str(e)}")
    
    def _process_operation(self, operation: Dict, job_data: Dict) -> Dict:
        """Process a single operation within a batch"""
        start_time = time.time()
        
        try:
            tokens = job_data['tokens']
            user_tz = job_data['user_tz']
            job_type = job_data['job_type']
            
            if job_type == 'batch_delete':
                # For delete operations, we need the event ID
                event_id = operation.get('id')
                calendar_id = operation.get('calendarId', 'primary')
                
                if not event_id:
                    return {
                        'success': False,
                        'error': 'Missing event ID for deletion'
                    }
                
                result, updated_tokens = main.deleteEvent(
                    token_info=tokens,
                    eventId=event_id,
                    calendarId=calendar_id
                )
                
                # Update tokens for future operations
                job_data['tokens'] = updated_tokens
                
                processing_time = int((time.time() - start_time) * 1000)
                result['processing_time_ms'] = processing_time
                
                return result
                
            elif job_type == 'batch_create':
                # For create operations
                event_data = operation.copy()
                event_data['timeZone'] = user_tz
                
                result, updated_tokens = main.formatEvent(
                    token_info=tokens,
                    event=event_data
                )
                
                # Update tokens for future operations
                job_data['tokens'] = updated_tokens
                
                processing_time = int((time.time() - start_time) * 1000)
                result['processing_time_ms'] = processing_time
                
                return result
            
            else:
                return {
                    'success': False,
                    'error': f'Unsupported job type: {job_type}'
                }
                
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"Error processing operation: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time_ms': processing_time
            }

# Global batch processor instance
batch_processor = None

def init_batch_processor(redis_client: Redis, max_workers: int = 5):
    """Initialize the global batch processor"""
    global batch_processor
    batch_processor = BatchProcessor(redis_client, max_workers)
    batch_processor.start_processing()

def get_batch_queue() -> Optional[BatchQueue]:
    """Get the global batch queue instance"""
    if batch_processor:
        return batch_processor.queue
    return None