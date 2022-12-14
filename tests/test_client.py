import asyncio
from client import Lago
from aiolago.utils import logger
from aiolago import Charge, BillableMetricResponse, Plan


customer_id = "gexai_demo"

metric_name = "Demo API Requests"
metric_id = "demo_requests"

plan_name = "Demo Plan"
plan_id = "demo_plan"

async def create_demo_customer():
    customer = await Lago.customers.async_create(
        external_id = customer_id,
        address_line1 = "000 Growth Engine Ave.",
        address_line2 = None,
        city = "Houston",
        currency = "USD",
        country = "US",
        email = f"{customer_id}@growthengineai.com",
        legal_name = "API Demo Customer",
        legal_number = "00-000-000",
        name = "API Demo User",
        phone = "1-000-0000-0000",
        state = "TX",
        url = "https://growthengineai.com",
        billing_configuration = {
            "tax_rate": 8.25,
        },
        zipcode = "77005",
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
