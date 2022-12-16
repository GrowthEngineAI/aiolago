# aiolago
 Unofficial Asyncronous Python Client for Lago


 **Latest Version**: [![PyPI version](https://badge.fury.io/py/aiolago.svg)](https://badge.fury.io/py/aiolago)

 **[Official Client](https://github.com/getlago/lago-python-client)**

## Features

- Unified Asyncronous and Syncronous Python Client for [Lago](https://www.getlago.com/)
- Supports Python 3.6+
- Strongly Typed with [Pydantic](https://pydantic-docs.helpmanual.io/)
- Includes Function Wrappers to quickly add to existing projects
- Utilizes Environment Variables for Configuration

---

## Installation

```bash
# Install from PyPI
pip install aiolago

# Install from source
pip install git+https://github.com/GrowthEngineAI/aiolago.git
```

## Usage

WIP - Simple Usage Example

```python
import asyncio
from aiolago import Lago
from aiolago.utils import logger

"""
Environment Vars that map to Lago.configure:
all vars are prefixed with LAGO_

LAGO_API_KEY (apikey): str
LAGO_URL (url): str takes precedence over LAGO_SCHEME | LAGO_HOST | LAGO_PORT
LAGO_SCHEME (scheme): str - defaults to 'http://'
LAGO_HOST (host): str - defaults to None
LAGO_PORT (port): int - defaults to 3000
LAGO_API_PATH (api_path): str - defaults to '/api/v1'
LAGO_TIMEOUT (timeout): int - defaults to 10
LAGO_IGNORE_ERRORS (ignore_errors): bool = defaults to False
"""

Lago.configure(
    api_key = '...',
    url = '',
)


customer_id = "gexai_demo"

metric_name = "Demo API Requests"
metric_id = "demo_requests"

plan_name = "Demo Plan"
plan_id = "demo_plan"


async def create_demo_customer():
    customer = await Lago.customers.async_create(
        external_id = customer_id,
        email = f"{customer_id}@growthengineai.com",
        billing_configuration = {
            "tax_rate": 8.25,
        },
    )
    logger.info(f'Created Customer: {customer}')
    return customer


flat_rate = 0.021
volume_rate = 0.025
base_rate = 0.023

rates = {
    'volume': [
        {
            'from_value': 0,
            'to_value': 2500,
            'flat_amount': '0',
            'per_unit_amount': str(round(volume_rate, 5)),
        },
        # 20% discount
        {
            'from_value': 2501,
            'to_value': 10000,
            'flat_amount': '0',
            'per_unit_amount': str(round(volume_rate * .8, 5)),
        },
        # 50% discount
        {
            'from_value': 10001,
            'flat_amount': '0',
            'per_unit_amount': str(round(volume_rate * .5, 5)),
        },
    ],
    'graduated': [
        {
            'to_value': 2500,
            'from_value': 0,
            'flat_amount': '0',
            'per_unit_amount': str(round(base_rate, 5)),
        },
        # 25% discount
        {
            'from_value': 2501,
            'flat_amount': '0',
            'per_unit_amount': str(round(base_rate * .75, 5)),
        },
    ],
    # 'standard': str(round(flat_rate, 5)),
}


def create_charge(
    metric_id: str,
    name: str = 'volume'
) -> Charge:
    # https://doc.getlago.com/docs/api/plans/plan-object

    if name in {'volume', 'graduated'}:
        return Charge(
            billable_metric_id = metric_id,
            charge_model = name,
            amount_currency = 'USD',
            properties = {
                f'{name}_ranges': rates[name],
            }
        )
    return Charge(
        billable_metric_id = metric_id,
        charge_model = name,
        amount_currency = 'USD',
        properties = {
            'amount': rates[name]
        },
    )
    


async def create_metric() -> BillableMetricResponse:
    """
    The upsert logic creates a new metric if it doesn't exist.
    """
    return await Lago.billable_metrics.async_upsert(
        resource_id = metric_id,
        name = metric_name,
        code = metric_id,
        description = 'Demo API Requests',
        aggregation_type = "sum_agg",
        field_name = "consumption"
    )
    


async def create_plan() -> Plan:
    
    plan = await Lago.plans.async_exists(
        resource_id = plan_id,
    )
    if not plan:
        metric = await create_metric()
        plan_obj = Plan(
            name = plan_name,
            amount_cents = 0,
            amount_currency = 'USD',
            code = plan_id,
            interval = "monthly",
            description = "Demo API Plan",
            pay_in_advance = False
        )
        for rate in rates:
            charge = create_charge(
                name = rate,
                metric_id = metric.resource_id,
            )
            plan_obj.add_charge_to_plan(charge)
        plan = await Lago.plans.async_create(plan_obj)
        logger.info(f'Created Plan: {plan}')
    return plan


async def run_test():
    plan = await create_plan()

asyncio.run(run_test())

```