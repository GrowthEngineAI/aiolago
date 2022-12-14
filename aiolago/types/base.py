import json
import aiohttpx
import backoff

from lazyops.types import BaseModel, Field, lazyproperty
from lazyops.utils import ObjectEncoder

from aiolago.utils.logs import logger
from aiolago.utils.config import settings

from aiolago.types.errors import APIError, fatal_exception

from typing import Dict, Optional, Any, List, Type, Callable, Union

__all__ = [
    'BaseRoute',
    'BaseResource',
    'RESPONSE_SUCCESS_CODES',
]

RESPONSE_SUCCESS_CODES = [
    200, 
    201, 
    202, 
    204
]


class BaseResource(BaseModel):

    @lazyproperty
    def resource_id(self):
        if hasattr(self, 'lago_id'):
            return self.lago_id

        return self.id if hasattr(self, 'id') else None
        


class BaseRoute(BaseModel):
    client: aiohttpx.Client
    headers: Dict[str, str] = Field(default_factory = settings.get_headers)
    success_codes: Optional[List[int]] = RESPONSE_SUCCESS_CODES
    input_model: Optional[Type[BaseResource]] = None
    response_model: Optional[Type[BaseResource]] = None
    usage_model: Optional[Type[BaseResource]] = None

    # Options
    timeout: Optional[int] = None
    debug_enabled: Optional[bool] = False
    on_error: Optional[Callable] = None
    ignore_errors: Optional[bool] = False


    @lazyproperty
    def api_resource(self):
        return ''

    @lazyproperty
    def root_name(self):
        return ''
    
    @lazyproperty
    def download_enabled(self):
        return False
    
    @lazyproperty
    def usage_enabled(self):
        return False
    
    def _send(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        # ignore_errors: Optional[bool] = None,
        timeout: Optional[int] = None,
        retries: Optional[int] = None,
        **kwargs
    ) -> aiohttpx.Response:
        # if ignore_errors is None: ignore_errors = self.ignore_errors
        if retries is None: retries = settings.max_retries
        if timeout is None: timeout = self.timeout
        @backoff.on_exception(
            backoff.expo, Exception, max_tries = retries + 1, giveup = fatal_exception
        )
        def _retryable_send():
            return self.client.request(
                method = method,
                url = url,
                params = params,
                data = data,
                headers = headers,
                timeout = timeout,
                **kwargs
            )
        return _retryable_send()
    
    async def _async_send(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        # ignore_errors: Optional[bool] = None,
        timeout: Optional[int] = None,
        retries: Optional[int] = None,
        **kwargs
    ) -> aiohttpx.Response:
        # if ignore_errors is None: ignore_errors = self.ignore_errors
        if retries is None: retries = settings.max_retries
        if timeout is None: timeout = self.timeout
        @backoff.on_exception(
            backoff.expo, Exception, max_tries = retries + 1, giveup = fatal_exception
        )
        async def _retryable_async_send():
            return await self.client.async_request(
                method = method,
                url = url,
                params = params,
                data = data,
                headers = headers,
                timeout = timeout,
                **kwargs
            )
        return await _retryable_async_send()


    def find(
        self, 
        resource_id: str, 
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Type[BaseResource]:
        """
        GET a Single Resource

        :param resource_id: The ID of the Resource to GET
        :param params: Optional Query Parameters
        """
        api_resource = f'{self.api_resource}/{resource_id}'
        # api_response = self.client.get(
        api_response = self._send(
            method = 'GET',
            url = api_resource, 
            params = params,
            headers = self.headers,
            **kwargs
        )
        data = self.handle_response(api_response)
        if data: data = data.json().get(self.root_name)
        return self.prepare_response(data)


    async def async_find(
        self, 
        resource_id: str, 
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    )  -> Type[BaseResource]:
        """
        GET a Single Resource

        :param resource_id: The ID of the Resource to GET
        :param params: Optional Query Parameters
        """
        api_resource = f'{self.api_resource}/{resource_id}'
        # api_response = await self.client.async_get(
        api_response = await self._async_send(
            method = 'GET',
            url = api_resource, 
            params = params,
            headers = self.headers,
            timeout = self.timeout,
            **kwargs
        )
        data = self.handle_response(api_response)
        if data: data = data.json().get(self.root_name)
        return self.prepare_response(data)

    def find_all(
        self, 
        options: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Union[List[Type[BaseResource]], Dict[str, Any]]]:
        """
        GET all available objects of Resource

        :param options: Optional Query Parameters
        
        :return: Dict[str, Union[List[Type[BaseResource]], Dict[str, Any]]]
        """
        # api_response = self.client.get(
        api_response = self._send(
            method = 'GET',
            url = self.api_resource,
            params = options,
            headers = self.headers,
            timeout = self.timeout,
            **kwargs
        )
        data = self.handle_response(api_response)
        if data: data = data.json()
        return self.prepare_index_response(data)

    async def async_find_all(
        self, 
        options: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Union[List[Type[BaseResource]], Dict[str, Any]]]:
        """
        GET all available objects of Resource

        :param options: Optional Query Parameters

        :return: Dict[str, Union[List[Type[BaseResource]], Dict[str, Any]]]
        """
        # api_response = await self.client.async_get(
        api_response = await self._async_send(
            method = 'GET',
            url = self.api_resource,
            params = options,
            headers = self.headers,
            timeout = self.timeout,
            **kwargs
        )
        data = self.handle_response(api_response)
        if data: data = data.json()
        return self.prepare_index_response(data)

    def get(
        self, 
        resource_id: str, 
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Type[BaseResource]:
        """
        GET a Single Resource

        :param resource_id: The ID of the Resource to GET
        :param params: Optional Query Parameters
        """
        return self.find(resource_id = resource_id, params = params, **kwargs)
    
    async def async_get(
        self,
        resource_id: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Type[BaseResource]:
        """
        GET a Single Resource

        :param resource_id: The ID of the Resource to GET
        :param params: Optional Query Parameters
        """
        return await self.async_find(resource_id = resource_id, params = params, **kwargs)

    def get_all(
        self,
        options: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Union[List[Type[BaseResource]], Dict[str, Any]]]:
        """
        GET all available objects of Resource

        :param options: Optional Query Parameters

        :return: Dict[str, Union[List[Type[BaseResource]], Dict[str, Any]]]
        """
        return self.find_all(options = options, **kwargs)
    
    async def async_get_all(
        self,
        options: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Union[List[Type[BaseResource]], Dict[str, Any]]]:
        """
        GET all available objects of Resource

        :param options: Optional Query Parameters
        
        :return: Dict[str, Union[List[Type[BaseResource]], Dict[str, Any]]]
        """
        return await self.async_find_all(options = options, **kwargs)    


    def destroy(
        self, 
        resource_id: str,
        **kwargs
    ):
        """
        DELETE a Resource

        :param resource_id: The ID of the Resource to DELETE
        """
        api_resource = f'{self.api_resource}/{resource_id}'
        # api_response = self.client.delete(
        api_response = self._send(
            method = 'DELETE',
            url = api_resource,
            headers = self.headers,
            timeout = self.timeout,
            **kwargs
        )
        data = self.handle_response(api_response)
        if data: data = data.json().get(self.root_name)
        return self.prepare_response(data)
    
    async def async_destroy(
        self, 
        resource_id: str,
        **kwargs
    ):
        """
        DELETE a Resource

        :param resource_id: The ID of the Resource to DELETE
        """
        api_resource = f'{self.api_resource}/{resource_id}'
        # api_response = await self.client.async_delete(
        api_response = await self._async_send(
            method = 'DELETE',
            url = api_resource,
            headers = self.headers,
            timeout = self.timeout,
            **kwargs
        )
        data = self.handle_response(api_response)
        if data: data = data.json().get(self.root_name)
        return self.prepare_response(data)

    def create(
        self, 
        input_object: Optional[Type[BaseResource]] = None,
        **kwargs
    ):
        """
        Create a Resource

        :param input_object: Input Object to Create
        """
        if input_object is None: 
            input_object = self.input_model.parse_obj(kwargs)
            kwargs = {}
        
        query_parameters = {
            self.root_name: input_object.dict(exclude_none=True)
        }
        data = json.dumps(query_parameters, cls = ObjectEncoder)
        # api_response = self.client.post(
        api_response = self._send(
            method = 'POST',
            url = self.api_resource,
            data = data,
            headers = self.headers,
            timeout = self.timeout,
            **kwargs
        )
        data = self.handle_response(api_response)
        if data is None: return True
        return self.prepare_response(data.json().get(self.root_name))
    
    async def async_create(
        self, 
        input_object: Optional[Type[BaseResource]] = None,
        **kwargs
    ):
        """
        Create a Resource

        :param input_object: Input Object to Create
        """
        if input_object is None: 
            input_object = self.input_model.parse_obj(kwargs)
            kwargs = {}
        
        query_parameters = {
            self.root_name: input_object.dict()
        }
        data = json.dumps(query_parameters, cls = ObjectEncoder)
        # api_response = await self.client.async_post(
        api_response = await self._async_send(
            method = 'POST',
            url = self.api_resource,
            data = data,
            headers = self.headers,
            timeout = self.timeout,
            **kwargs
        )
        data = self.handle_response(api_response)
        if data is None: return True
        return self.prepare_response(data.json().get(self.root_name))
    
    def batch_create(
        self, 
        input_object: Optional[Type[BaseResource]] = None,
        return_response: bool = False,
        **kwargs
    ):
        """
        Batch Create Resources

        :param input_object: Input Object to Create
        :param return_response: Return the Response Object
        """
        if input_object is None: 
            input_object = self.input_model.parse_obj(kwargs)
            kwargs = {}

        api_resource = f'{self.api_resource}/batch'
        query_parameters = {
            self.root_name: input_object.dict()
        }
        data = json.dumps(query_parameters, cls = ObjectEncoder)
        # api_response = self.client.post(
        api_response = self._send(
            method = 'POST',
            url = api_resource,
            data = data,
            headers = self.headers,
            timeout = self.timeout,
            **kwargs
        )
        resp = self.handle_response(api_response)
        return resp if return_response else True

    async def async_batch_create(
        self, 
        input_object: Optional[Type[BaseResource]] = None,
        return_response: bool = False,
        **kwargs
    ):
        """
        Batch Create Resources

        :param input_object: Input Object to Create
        :param return_response: Return the Response Object
        """
        if input_object is None: 
            input_object = self.input_model.parse_obj(kwargs)
            kwargs = {}

        api_resource = f'{self.api_resource}/batch'
        query_parameters = {
            self.root_name: input_object.dict()
        }
        data = json.dumps(query_parameters)
        # api_response = await self.client.async_post(
        api_response = await self._async_send(  
            method = 'POST',
            url = api_resource,
            data = data,
            headers = self.headers,
            timeout = self.timeout,
            **kwargs
        )
        resp = self.handle_response(api_response)
        return resp if return_response else True


    def update(
        self, 
        input_object: Optional[Type[BaseResource]] = None,
        identifier: str = None,
        **kwargs
    ):
        """
        Update a Resource

        :param input_object: Input Object to Update
        :param identifier: The ID of the Resource to Update
        """
        if input_object is None: 
            input_object = self.input_model.parse_obj(kwargs)
            kwargs = {}
        
        api_resource = self.api_resource
        #identifier = identifier or getattr(input_object, 'code', None)
        if identifier is not None:
            api_resource = f'{api_resource}/{identifier}'

        query_parameters = {
            self.root_name: input_object.dict(exclude_none = True)
        }
        data = json.dumps(query_parameters, cls = ObjectEncoder)
        # api_response = self.client.put(
        api_response = self._send(
            method = 'PUT',
            url = api_resource,
            data = data,
            #params = query_parameters,
            headers = self.headers,
            timeout = self.timeout,
            **kwargs
        )
        data = self.handle_response(api_response).json().get(self.root_name)
        return self.prepare_response(data)

    async def async_update(
        self, 
        input_object: Optional[Type[BaseResource]] = None,
        identifier: str = None,
        **kwargs
    ):
        """
        Update a Resource

        :param input_object: Input Object to Update
        :param identifier: The ID of the Resource to Update
        """
        if input_object is None: 
            input_object = self.input_model.parse_obj(kwargs)
            kwargs = {}
        
        input_object = input_object or self.input_model
        api_resource = self.api_resource
        #identifier = identifier or getattr(input_object, 'code', None)
        if identifier is not None:
            api_resource = f'{api_resource}/{identifier}'
        query_parameters = {
            self.root_name: input_object.dict(exclude_none = True)
        }
        data = json.dumps(query_parameters, cls = ObjectEncoder)
        # api_response = await self.client.async_put(
        api_response = await self._async_send(
            method = 'PUT',
            url = api_resource,
            data = data,
            headers = self.headers,
            timeout = self.timeout,
            **kwargs
        )
        data = self.handle_response(api_response).json().get(self.root_name)
        return self.prepare_response(data)
    
    """
    Extra Methods
    """

    def exists(
        self,
        resource_id: str,
        **kwargs
    ) -> bool:
        """
        See whether a Resource Exists

        :param resource_id: The ID of the Resource to Valid
        """
        try:
            return self.find(resource_id = resource_id, **kwargs)
        except Exception:
            return False
    
    async def async_exists(
        self,
        resource_id: str,
        **kwargs
    ) -> bool:
        """
        See whether a Resource Exists

        :param resource_id: The ID of the Resource to Valid
        """
        try:
            return await self.async_find(resource_id = resource_id, **kwargs)
        except Exception:
            return False
    
    def upsert(
        self,
        resource_id: str,
        input_object: Optional[Type[BaseResource]] = None,
        update_existing: bool = False, 
        overwrite_existing: bool = False,
        **kwargs
    ):
        """
        Upsert a Resource
        Validates whether the Resource exists, and if it does, updates it. 
        If it doesn't, creates it.
        If update_existing is True, it will always update the Resource
        If overwrite_existing is True, it will re-create the Resource

        :resource_id: The ID of the Resource to Upsert
        :param input_object: Input Object to Upsert
        :param update_existing (bool): Whether to update the Resource if it exists
        :overwrite_existing (bool): Whether to overwrite the Resource if it exists
        """
        resource = self.exists(resource_id = resource_id, **kwargs)
        if resource is not None:
            if update_existing:
                return self.update(input_object = input_object, identifier = resource_id, **kwargs)
            if overwrite_existing:
                self.destroy(resource_id = resource_id, **kwargs)
                return self.create(input_object = input_object, **kwargs)
            return resource
        return self.create(input_object = input_object, **kwargs)
    
    async def async_upsert(
        self,
        resource_id: str,
        input_object: Optional[Type[BaseResource]] = None,
        update_existing: bool = False, 
        overwrite_existing: bool = False,
        **kwargs
    ):
        """
        Upsert a Resource
        Validates whether the Resource exists, and if it does, updates it. 
        If it doesn't, creates it.
        If update_existing is True, it will always update the Resource
        If overwrite_existing is True, it will re-create the Resource

        :resource_id: The ID of the Resource to Upsert
        :param input_object: Input Object to Upsert
        :param update_existing (bool): Whether to update the Resource if it exists
        :overwrite_existing (bool): Whether to overwrite the Resource if it exists
        """
        resource = await self.async_exists(resource_id = resource_id, **kwargs)
        if resource is not None:
            if update_existing:
                return self.async_update(input_object = input_object, identifier = resource_id, **kwargs)
            if overwrite_existing:
                await self.async_destroy(resource_id = resource_id, **kwargs)
                return await self.async_create(input_object = input_object, **kwargs)
            return resource
        return await self.async_create(input_object = input_object, **kwargs)

    def download(
        self, 
        resource_id: str,
        **kwargs
    ):
        """
        Download a Resource

        :param resource_id: The ID of the Resource to Download
        """
        if not self.download_enabled:
            raise NotImplementedError('Download is not enabled for this resource')
        
        api_resource = f'{self.api_resource}/{resource_id}/download'
        # api_response = self.client.post(
        api_response = self._send(
            method = 'POST',
            url = api_resource, 
            headers = self.headers,
            timeout = self.timeout,
            **kwargs
        )
        data = self.handle_response(api_response).json().get(self.root_name())
        return self.prepare_response(data)

    async def async_download(
        self, 
        resource_id: str,
        **kwargs
    ):
        """
        Download a Resource

        :param resource_id: The ID of the Resource to Download
        """
        if not self.download_enabled:
            raise NotImplementedError('Download is not enabled for this resource')
        api_resource = f'{self.api_resource}/{resource_id}/download'
        #api_response = await self.client.async_post(
        api_response = await self._async_send(
            method = 'POST',
            url = api_resource, 
            headers = self.headers,
            timeout = self.timeout,
            **kwargs
        )
        data = self.handle_response(api_response).json().get(self.root_name())
        return self.prepare_response(data)


    def current_usage(
        self, 
        resource_id: str, 
        external_subscription_id: str,
        usage_object: Type[BaseResource] = None,
        **kwargs
    ):
        """
        Get Current Usage for a Resource

        :param resource_id: The ID of the Resource to Get Usage For
        """
        if not self.usage_enabled:
            raise NotImplementedError('Usage is not enabled for this resource')
        api_resource = f'{self.api_resource}/{resource_id}/current_usage'
        #api_response = self.client.get(
        api_response = self._send(
            method = 'GET',
            url = api_resource, 
            params = {'external_subscription_id': external_subscription_id},
            headers = self.headers,
            **kwargs
        )
        data = self.handle_response(api_response).json().get('customer_usage')
        usage_object = usage_object or self.usage_model
        return usage_object.parse_obj(data)
    
    async def async_current_usage(
        self, 
        resource_id: str, 
        external_subscription_id: str,
        usage_object: Type[BaseResource] = None,
        **kwargs
    ):
        """
        Get Current Usage for a Resource

        :param resource_id: The ID of the Resource to Get Usage For
        """
        api_resource = f'{self.api_resource}/{resource_id}/current_usage'
        #api_response = await self.client.async_get(
        api_response = await self._async_send(
            method = 'GET',
            url = api_resource, 
            params = {'external_subscription_id': external_subscription_id},
            headers = self.headers,
            timeout = self.timeout,
            **kwargs
        )
        data = self.handle_response(api_response).json().get('customer_usage')
        usage_object = usage_object or self.usage_model
        return usage_object.parse_obj(data)

    def prepare_response(
        self, 
        data: Dict,
        response_object: Optional[Type[BaseResource]] = None,
        **kwargs
    ):
        """
        Prepare the Response Object
        
        :param data: The Response Data
        :param response_object: The Response Object
        """
        response_object = response_object or self.response_model
        if response_object:
            return response_object.parse_obj(data)
        raise NotImplementedError('Response model not defined for this resource.')

    def handle_response(
        self, 
        response: aiohttpx.Response,
        **kwargs
    ):
        """
        Handle the Response

        :param response: The Response
        """
        if self.debug_enabled:
            logger.info(f'[{response.status_code} - {response.request.url}] headers: {response.headers}, body: {response.text}')
        
        if response.status_code in self.success_codes:
            return response if response.text else None
        
        if self.ignore_errors:
            return None
        
        raise APIError(
            url = response.request.url,
            status = response.status_code,
            payload = response.text
        )

    def prepare_index_response(
        self, 
        data: Dict[str, Any],
        response_object: Optional[Type[BaseResource]] = None,
        **kwargs
    ):
        """
        Prepare the Response Object for Index Requests

        :param data: The Response Data
        :param response_object: The Response Object
        """
        collection = [
            self.prepare_response(el, response_object = response_object) for el in data[self.api_resource]
        ]
        return {
            self.api_resource: collection,
            'meta': data['meta']
        }





