from typing import Optional, Type
from aiolago.types.base import BaseRoute, BaseResource, lazyproperty

__all__ = [
    'BillableMetric',
    'BillableMetricResponse',
    'BillableMetricRoute',
]

class BillableMetric(BaseResource):
    name: Optional[str]
    code: Optional[str]
    description: Optional[str]
    aggregation_type: Optional[str]
    field_name: Optional[str]


class BillableMetricResponse(BaseResource):
    lago_id: str
    name: str
    code: str
    description: Optional[str]
    aggregation_type: Optional[str]
    field_name: Optional[str]
    created_at: str


class BillableMetricRoute(BaseRoute):
    input_model: Optional[Type[BaseResource]] = BillableMetric
    response_model: Optional[Type[BaseResource]] = BillableMetricResponse
    usage_model: Optional[Type[BaseResource]] = None

    @lazyproperty
    def api_resource(self):
        return 'billable_metrics'

    @lazyproperty
    def root_name(self):
        return 'billable_metric'
    
