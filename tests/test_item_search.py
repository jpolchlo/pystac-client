import json
from datetime import datetime, timedelta

import pystac
import pytest
from dateutil.tz import gettz, tzutc

from pystac_api import API
from pystac_api.item_search import ItemSearch

from .helpers import ASTRAEA_URL, read_data_file

SEARCH_URL = f'{ASTRAEA_URL}/search'
INTERSECTS_EXAMPLE = {
    'type': 'Polygon',
    'coordinates': [[
        [-73.21, 43.99],
        [-73.21, 44.05],
        [-73.12, 44.05],
        [-73.12, 43.99],
        [-73.21, 43.99]
    ]]
}


class TestItemSearchParams:
    @pytest.fixture(scope='function')
    def astraea_api(self):
        api_content = read_data_file('astraea_api.json', parse_json=True)
        return API.from_dict(api_content)

    def test_tuple_bbox(self):
        # Tuple input
        search = ItemSearch(url=ASTRAEA_URL, bbox=(-104.5, 44.0, -104.0, 45.0))
        assert search.request.json['bbox'] == (-104.5, 44.0, -104.0, 45.0)

    def test_list_bbox(self):
        # List input
        search = ItemSearch(url=ASTRAEA_URL, bbox=[-104.5, 44.0, -104.0, 45.0])
        assert search.request.json['bbox'] == (-104.5, 44.0, -104.0, 45.0)

    def test_string_bbox(self):
        # String Input
        search = ItemSearch(url=ASTRAEA_URL, bbox='-104.5,44.0,-104.0,45.0')
        assert search.request.json['bbox'] == (-104.5, 44.0, -104.0, 45.0)

    def test_generator_bbox(self):
        # Generator Input
        def bboxer():
            yield from [-104.5, 44.0, -104.0, 45.0]

        search = ItemSearch(url=ASTRAEA_URL, bbox=bboxer())
        assert search.request.json['bbox'] == (-104.5, 44.0, -104.0, 45.0)

    def test_single_string_datetime(self):
        # Single timestamp input
        search = ItemSearch(url=ASTRAEA_URL, datetime='2020-02-01T00:00:00Z')
        assert search.request.json['datetime'] == '2020-02-01T00:00:00Z'

    def test_range_string_datetime(self):
        # Timestamp range input
        search = ItemSearch(url=ASTRAEA_URL, datetime='2020-02-01T00:00:00Z/2020-02-02T00:00:00Z')
        assert search.request.json['datetime'] == '2020-02-01T00:00:00Z/2020-02-02T00:00:00Z'

    def test_list_of_strings_datetime(self):
        # Timestamp list input
        search = ItemSearch(url=ASTRAEA_URL, datetime=['2020-02-01T00:00:00Z', '2020-02-02T00:00:00Z'])
        assert search.request.json['datetime'] == '2020-02-01T00:00:00Z/2020-02-02T00:00:00Z'

    def test_open_range_string_datetime(self):
        # Open timestamp range input
        search = ItemSearch(url=ASTRAEA_URL, datetime='2020-02-01T00:00:00Z/..')
        assert search.request.json['datetime'] == '2020-02-01T00:00:00Z/..'

    def test_single_datetime_object(self):
        start = datetime(2020, 2, 1, 0, 0, 0, tzinfo=tzutc())

        # Single datetime input
        search = ItemSearch(url=ASTRAEA_URL, datetime=start)
        assert search.request.json['datetime'] == '2020-02-01T00:00:00Z'

    def test_list_of_datetimes(self):
        start = datetime(2020, 2, 1, 0, 0, 0, tzinfo=tzutc())
        end = datetime(2020, 2, 2, 0, 0, 0, tzinfo=tzutc())

        # Datetime range input
        search = ItemSearch(url=ASTRAEA_URL, datetime=[start, end])
        assert search.request.json['datetime'] == '2020-02-01T00:00:00Z/2020-02-02T00:00:00Z'

    def test_open_list_of_datetimes(self):
        start = datetime(2020, 2, 1, 0, 0, 0, tzinfo=tzutc())

        # Open datetime range input
        search = ItemSearch(url=ASTRAEA_URL, datetime=(start, None))
        assert search.request.json['datetime'] == '2020-02-01T00:00:00Z/..'

    def test_localized_datetime_converted_to_utc(self):
        # Localized datetime input (should be converted to UTC)
        start_localized = datetime(2020, 2, 1, 0, 0, 0, tzinfo=gettz('US/Eastern'))
        search = ItemSearch(url=ASTRAEA_URL, datetime=start_localized)
        assert search.request.json['datetime'] == '2020-02-01T05:00:00Z'

    def test_single_collection_string(self):
        # Single ID string
        search = ItemSearch(url=ASTRAEA_URL, collections='naip')
        assert search.request.json['collections'] == ('naip',)

    def test_multiple_collection_string(self):
        # Comma-separated ID string
        search = ItemSearch(url=ASTRAEA_URL, collections='naip,landsat8_l1tp')
        assert search.request.json['collections'] == ('naip', 'landsat8_l1tp')

    def test_list_of_collection_strings(self):
        # List of ID strings
        search = ItemSearch(url=ASTRAEA_URL, collections=['naip', 'landsat8_l1tp'])
        assert search.request.json['collections'] == ('naip', 'landsat8_l1tp')

    def test_generator_of_collection_strings(self):
        # Generator of ID strings
        def collectioner():
            yield from ['naip', 'landsat8_l1tp']

        search = ItemSearch(url=ASTRAEA_URL, collections=collectioner())
        assert search.request.json['collections'] == ('naip', 'landsat8_l1tp')

    @pytest.mark.vcr
    def test_collection_object(self, astraea_api):
        collection = astraea_api.get_child('landsat8_l1tp')

        # Single pystac.Collection
        search = ItemSearch(url=ASTRAEA_URL, collections=collection)
        assert search.request.json['collections'] == ('landsat8_l1tp',)

    @pytest.mark.vcr
    def test_mixed_collection_object_and_string(self, astraea_api):
        collection = astraea_api.get_child('landsat8_l1tp')

        # Mixed list
        search = ItemSearch(url=ASTRAEA_URL, collections=[collection, 'naip'])
        assert search.request.json['collections'] == ('landsat8_l1tp', 'naip')

    def test_single_id_string(self):
        # Single ID
        search = ItemSearch(url=ASTRAEA_URL, ids='m_3510836_se_12_060_20180508_20190331')
        assert search.request.json['ids'] == ('m_3510836_se_12_060_20180508_20190331',)

    def test_multiple_id_string(self):
        # Comma-separated ID string
        search = ItemSearch(
            url=ASTRAEA_URL,
            ids='m_3510836_se_12_060_20180508_20190331,m_3510840_se_12_060_20180504_20190331'
        )
        assert search.request.json['ids'] == (
            'm_3510836_se_12_060_20180508_20190331',
            'm_3510840_se_12_060_20180504_20190331'
        )

    def test_list_of_id_strings(self):
        # List of IDs
        search = ItemSearch(
            url=ASTRAEA_URL,
            ids=[
                'm_3510836_se_12_060_20180508_20190331',
                'm_3510840_se_12_060_20180504_20190331'
            ]
        )
        assert search.request.json['ids'] == (
            'm_3510836_se_12_060_20180508_20190331',
            'm_3510840_se_12_060_20180504_20190331'
        )

    def test_generator_of_id_string(self):
        # Generator of IDs
        def ids():
            yield from [
                'm_3510836_se_12_060_20180508_20190331',
                'm_3510840_se_12_060_20180504_20190331'
            ]

        search = ItemSearch(
            url=ASTRAEA_URL,
            ids=ids()
        )
        assert search.request.json['ids'] == (
            'm_3510836_se_12_060_20180508_20190331',
            'm_3510840_se_12_060_20180504_20190331'
        )

    def test_intersects_dict(self):
        # Dict input
        search = ItemSearch(url=SEARCH_URL, intersects=INTERSECTS_EXAMPLE)
        assert search.request.json['intersects'] == INTERSECTS_EXAMPLE

    def test_intersects_json_string(self):
        # JSON string input
        search = ItemSearch(url=SEARCH_URL, intersects=json.dumps(INTERSECTS_EXAMPLE))
        assert search.request.json['intersects'] == INTERSECTS_EXAMPLE


class TestItemSearch:
    @pytest.fixture(scope='function')
    def astraea_api(self):
        api_content = read_data_file('astraea_api.json', parse_json=True)
        return API.from_dict(api_content)

    def test_method(self):
        # Default method should be POST...
        search = ItemSearch(url=ASTRAEA_URL)
        assert search.method == 'POST'

        # "method" argument should take precedence over presence of "intersects"
        search = ItemSearch(url=ASTRAEA_URL, method='GET', intersects=INTERSECTS_EXAMPLE)
        assert search.method == 'GET'

    @pytest.mark.vcr
    def test_results(self):
        search = ItemSearch(
            url=SEARCH_URL,
            collections='naip',
            max_items=20,
            limit=10,
        )
        results = search.items()

        assert all(isinstance(item, pystac.Item) for item in results)

    @pytest.mark.vcr
    def test_ids_results(self):
        ids = [
            'm_3510836_se_12_060_20180508_20190331',
            'm_3510840_se_12_060_20180504_20190331'
        ]
        search = ItemSearch(
            url=SEARCH_URL,
            ids=ids,
        )
        results = list(search.items())

        assert len(results) == 2
        assert all(item.id in ids for item in results)

    @pytest.mark.vcr
    def test_datetime_results(self):
        # Datetime range string
        datetime_ = '2019-01-01T00:00:01Z/2019-01-01T00:00:10Z'
        search = ItemSearch(
            url=SEARCH_URL,
            datetime=datetime_
        )
        results = list(search.items())
        assert len(results) == 12

        min_datetime = datetime(2019, 1, 1, 0, 0, 1, tzinfo=tzutc())
        max_datetime = datetime(2019, 1, 1, 0, 0, 10, tzinfo=tzutc())
        search = ItemSearch(
            url=SEARCH_URL,
            datetime=(min_datetime, max_datetime)
        )
        results = search.items()
        assert all(min_datetime <= item.datetime <= (max_datetime + timedelta(seconds=1))for item in results)

    @pytest.mark.vcr
    def test_intersects_results(self):
        # GeoJSON-like dict
        intersects_dict = {
            'type': 'Polygon',
            'coordinates': [[
                [-73.21, 43.99],
                [-73.21, 44.05],
                [-73.12, 44.05],
                [-73.12, 43.99],
                [-73.21, 43.99]
            ]]
        }
        search = ItemSearch(
            url=SEARCH_URL,
            intersects=intersects_dict,
            collections='naip'
        )
        results = list(search.items())
        assert len(results) == 30

        # Geo-interface object
        class MockGeoObject:
            __geo_interface__ = intersects_dict

        intersects_obj = MockGeoObject()
        search = ItemSearch(
            url=SEARCH_URL,
            intersects=intersects_obj,
            collections='naip'
        )
        results = search.items()
        assert all(isinstance(item, pystac.Item) for item in results)

    @pytest.mark.vcr
    def test_result_paging(self):
        search = ItemSearch(
            url=SEARCH_URL,
            bbox=(-73.21, 43.99, -73.12, 44.05),
            collections='naip',
            limit=10,
            max_items=20,
        )

        # Check that the current page changes on the ItemSearch instance when a new page is requested
        pages = list(search.item_collections())

        assert pages[1] != pages[2]
        assert pages[1].features != pages[2].features
