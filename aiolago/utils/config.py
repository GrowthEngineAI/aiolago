from typing import Optional, Dict
from lazyops.types import BaseSettings, lazyproperty
from aiolago.version import VERSION



class LagoSettings(BaseSettings):

    url: Optional[str] = None
    scheme: Optional[str] = 'http://'
    host: Optional[str] = None
    port: Optional[int] = 3000
    
    apikey: Optional[str] = None
    apipath: Optional[str] = '/api/v1/'

    apikey_header: Optional[str] = None
    organization_id: Optional[str] = None

    ignore_errors: Optional[bool] = False
    debug_enabled: Optional[bool] = True

    timeout: Optional[int] = 10
    max_retries: Optional[int] = 3
    
    class Config:
        env_prefix = 'LAGO_'
        case_sensitive = False

    @lazyproperty
    def api_url(self) -> str:
        if self.url:
            return self.url
        if self.host:
            url = f"{self.scheme}{self.host}"
            if self.port: url += f":{self.port}"
            return url
        
        # Return the official Lago API URL
        return "https://api.getlago.com"
    
    @lazyproperty
    def base_url(self) -> str:
        if self.apipath:
            from urllib.parse import urljoin
            return urljoin(self.api_url, self.apipath)
        return self.api_url
    
    @lazyproperty
    def headers(self):
        _headers = {"Content-Type": "application/json", "User-Agent": f"aiolago/{VERSION}"}
        if self.apikey: 
            if self.apikey_header:
                _headers[self.apikey_header] = self.apikey
            else:
                _headers['Authorization'] = f'Bearer {self.apikey}'
        return _headers


    def get_headers(
        self, 
        apikey: Optional[str] = None, 
        apikey_header: Optional[str] = None, 
        **kwargs
    ) -> Dict[str, str]:

        headers = self.headers.copy()
        if kwargs: headers.update(**kwargs)
        apikey_header = apikey_header if apikey_header is not None else self.apikey_header
        apikey = apikey if apikey is not None else self.apikey
        if apikey:
            if apikey_header:
                headers[apikey_header] = apikey
            else:
                headers['Authorization'] = f'Bearer {apikey}'
        return headers

    def get_api_url(
        self, 
        host: Optional[str] = None, 
        port: Optional[int] = None, 
        scheme: Optional[str] = None, 
        url: Optional[str] = None,
        **kwargs
    ) -> str:
        if url: return url
        if host:
            url = f"{scheme or self.scheme}{host}"
            if port: url += f":{port}"
            return url
        return self.api_url

    def get_base_api_url(
        self, 
        host: Optional[str] = None, 
        port: Optional[int] = None, 
        scheme: Optional[str] = None, 
        url: Optional[str] = None,
        apipath: Optional[str] = None,
        **kwargs
    ) -> str:
        api_url = self.get_api_url(
            host=host,
            port=port,
            scheme=scheme,
            url=url,
        )
        apipath = apipath or self.apipath
        if apipath:
            from urllib.parse import urljoin
            return urljoin(api_url, apipath)
        return api_url

settings = LagoSettings()