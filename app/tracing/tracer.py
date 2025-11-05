import time
from typing import Dict, Any, Optional
from functools import wraps
import json
from pathlib import Path
from datetime import datetime
from app.config import settings
from app.utils.logging_config import log


class LLMTracer:
    
    def __init__(self):
        self.enabled = settings.enable_tracing
        self.traces_dir = Path(settings.log_dir) / "traces"
        self.traces_dir.mkdir(exist_ok=True)
        self.current_trace = {}
    
    def start_trace(self, trace_id: str, operation: str, metadata: Dict[str, Any] = None):
        if not self.enabled:
            return
        
        self.current_trace = {
            "trace_id": trace_id,
            "operation": operation,
            "start_time": time.time(),
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
            "steps": [],
            "llm_calls": []
        }
    
    def log_step(self, step_name: str, data: Dict[str, Any] = None):
        if not self.enabled or not self.current_trace:
            return
        
        self.current_trace["steps"].append({
            "step": step_name,
            "timestamp": time.time(),
            "data": data or {}
        })
    
    def log_llm_call(self, model: str, prompt: str, response: str, 
                     tokens_used: int = 0, cost: float = 0.0):
        if not self.enabled or not self.current_trace:
            return
        
        self.current_trace["llm_calls"].append({
            "model": model,
            "prompt_preview": prompt[:200],
            "response_preview": response[:200],
            "tokens": tokens_used,
            "cost": cost,
            "timestamp": time.time()
        })
    
    def end_trace(self):
        if not self.enabled or not self.current_trace:
            return
        
        self.current_trace["end_time"] = time.time()
        self.current_trace["duration"] = self.current_trace["end_time"] - self.current_trace["start_time"]
        
        trace_file = self.traces_dir / f"trace_{self.current_trace['trace_id']}.json"
        with open(trace_file, 'w') as f:
            json.dump(self.current_trace, f, indent=2)
        
        log.info(f"Trace saved: {trace_file}")
        self.current_trace = {}
    
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        trace_file = self.traces_dir / f"trace_{trace_id}.json"
        if trace_file.exists():
            with open(trace_file, 'r') as f:
                return json.load(f)
        return None


tracer = LLMTracer()


def trace_operation(operation_name: str):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            trace_id = f"{operation_name}_{int(time.time())}"
            tracer.start_trace(trace_id, operation_name)
            try:
                result = await func(*args, **kwargs)
                tracer.end_trace()
                return result
            except Exception as e:
                tracer.log_step("error", {"error": str(e)})
                tracer.end_trace()
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            trace_id = f"{operation_name}_{int(time.time())}"
            tracer.start_trace(trace_id, operation_name)
            try:
                result = func(*args, **kwargs)
                tracer.end_trace()
                return result
            except Exception as e:
                tracer.log_step("error", {"error": str(e)})
                tracer.end_trace()
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


__all__ = ["LLMTracer", "tracer", "trace_operation"]