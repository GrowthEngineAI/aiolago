## aiolago Changelogs

- 0.0.4 (2022-12-15)
  - Add support for `metric_groups` querying
  - Resolve some issues with billable metrics

- 0.0.3 (2022-12-15)
  - Reconfigure how configuration and initialization work
  - change some params to be more consistent
    - `apikey` -> `api_key`
    - `apipath` -> `api_path`
    - `apikey_header` -> `api_key_header`
    - `apipath` -> `api_path`


- 0.0.2 (2022-12-14)
  - Fix `options` to become `params` in `get_all` methods
  - Resolve model creation methods to return unused `kwargs`
  - Add additional params to `@on_event` decorator  

- 0.0.1 (2022-12-13)
    - Initial release.