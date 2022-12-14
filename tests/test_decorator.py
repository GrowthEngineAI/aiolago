import uuid
import asyncio
import random
from client import Lago
from typing import Dict, List, Any
from aiolago.utils import logger


customer_id = "gexai_demo"
metric_id = "demo_requests"

async def get_customer_id(*args, **kwargs):
    return customer_id

async def get_metric_id(*args, **kwargs):
    return metric_id

async def extra_properties(*args, **kwargs):
    return {
        "consumption": 1
    }

async def event_callback(args: List, result: Any, properties: Dict, kwargs: Dict, wrapper_kwargs: Dict):
    properties['consumption'] = random.randrange(5, 10)
    logger.info(f'Event callback: {args}, {result}, {properties}, {kwargs}, {wrapper_kwargs}')
    return properties


@Lago.on_event(
    customer_id = get_customer_id,
    metric_id = get_metric_id,
    extra_properties_func = extra_properties,
    include_duration = True,
    usage_callback = event_callback
)
async def log_event(*args, **kwargs):
    return str(uuid.uuid4())


async def run_test(n_times: int = 10):
    for _ in range(n_times):
        res = await log_event(
            model = 'test_model',
        )
    
    logger.info('Done logging usage')

asyncio.run(run_test())