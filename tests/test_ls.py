# Copyright (C) 2019-2021 HERE Europe B.V.
# SPDX-License-Identifier: Apache-2.0

import os
from datetime import datetime

import pytest
from geojson import FeatureCollection

from here_location_services import LS
from here_location_services.config.routing_config import (
    ROUTE_COURSE,
    ROUTE_MATCH_SIDEOF_STREET,
    ROUTING_RETURN,
    ROUTING_SPANS,
    PlaceOptions,
    WayPointOptions,
)
from here_location_services.exceptions import ApiError
from here_location_services.responses import GeocoderResponse
from here_location_services.utils import get_apikey

LS_API_KEY = get_apikey()


@pytest.mark.skipif(not LS_API_KEY, reason="No api key found.")
def test_ls_geocoding():
    """Test geocoding api. """
    address = "200 S Mathilda Sunnyvale CA"
    ls = LS(api_key=LS_API_KEY)
    resp = ls.geocode(query=address, limit=2)
    assert isinstance(resp, GeocoderResponse)
    assert resp.__str__()
    assert resp.as_json_string()
    geo_json = resp.to_geojson()
    assert geo_json.type == "FeatureCollection"
    assert geo_json.features
    pos = resp.items[0]["position"]
    assert len(resp.items) == 2
    assert pos == {"lat": 37.37634, "lng": -122.03405}


@pytest.mark.skipif(not LS_API_KEY, reason="No api key found.")
def test_ls_geocoding_exception():
    """Test geocoding api exception."""
    address = "Goregaon West, Mumbai 400062, India"

    ls = LS(api_key="dummy")
    with pytest.raises(ApiError):
        ls.geocode(query=address)
    with pytest.raises(ValueError):
        ls.geocode(query="")
        ls.geocode(query="   ")


@pytest.mark.skipif(not LS_API_KEY, reason="No api key found.")
def test_ls_reverse_geocoding():
    """Test reverse geocoding."""
    ls = LS(api_key=LS_API_KEY)
    resp = ls.reverse_geocode(lat=19.1646, lng=72.8493)
    address = resp.items[0]["address"]["label"]
    assert (
        address == "Goregaon East Railway Station(East ENT), Goregaon West, Mumbai 400062, India"
    )
    resp1 = ls.reverse_geocode(lat=19.1646, lng=72.8493, limit=4)
    assert len(resp1.items) == 4


@pytest.mark.skipif(not LS_API_KEY, reason="No api key found.")
def test_ls_reverse_geocoding_exception():
    """Test reverse geocoding api exception."""
    ls = LS(api_key=LS_API_KEY)
    with pytest.raises(ValueError):
        ls.reverse_geocode(lat=91, lng=90)
    with pytest.raises(ValueError):
        ls.reverse_geocode(lat=19, lng=190)
    ls = LS(api_key="dummy")
    with pytest.raises(ApiError):
        ls.reverse_geocode(lat=19.1646, lng=72.8493)


@pytest.mark.skipif(not LS_API_KEY, reason="No api key found.")
def test_isonline_routing():
    """Test isonline routing api."""
    ls = LS(api_key=LS_API_KEY)
    result = ls.calculate_isoline(
        start=[52.5, 13.4],
        range="900",
        range_type="time",
        mode="fastest;car;",
        departure="2020-05-04T17:00:00+02",
    )

    coordinates = result.isoline[0]["component"][0]["shape"]
    assert coordinates[0]
    geo_json = result.to_geojson()
    assert geo_json.type == "Feature"
    assert geo_json.geometry.type == "Polygon"

    result2 = ls.calculate_isoline(
        destination=[52.5, 13.4],
        range="900",
        range_type="time",
        mode="fastest;car;",
        arrival="2020-05-04T17:00:00+02",
    )
    coordinates = result2.isoline[0]["component"][0]["shape"]
    assert coordinates[0]

    with pytest.raises(ValueError):
        ls.calculate_isoline(
            start=[52.5, 13.4],
            range="900",
            range_type="time",
            mode="fastest;car;",
            destination=[52.5, 13.4],
        )
    with pytest.raises(ApiError):
        ls2 = LS(api_key="dummy")
        ls2.calculate_isoline(
            start=[52.5, 13.4],
            range="900",
            range_type="time",
            mode="fastest;car;",
        )


@pytest.mark.skipif(not LS_API_KEY, reason="No api key found.")
def test_isonline_routing_exception():
    """Test isonline exceptions."""
    ls = LS(api_key=LS_API_KEY)
    with pytest.raises(ValueError):
        ls.calculate_isoline(
            range="900",
            range_type="time",
            mode="fastest;car;",
        )
    with pytest.raises(ValueError):
        ls.calculate_isoline(
            range="900",
            range_type="time",
            mode="fastest;car;",
            arrival="2020-05-04T17:00:00+02",
            start=[52.5, 13.4],
        )
    with pytest.raises(ValueError):
        ls.calculate_isoline(
            range="900",
            range_type="time",
            mode="fastest;car;",
            departure="2020-05-04T17:00:00+02",
            destination=[52.5, 13.4],
        )


@pytest.mark.skipif(not LS_API_KEY, reason="No api key found.")
def test_ls_discover():
    ls = LS(api_key=LS_API_KEY)
    result = ls.discover(query="starbucks", center=[19.1663, 72.8526], radius=10000, lang="en")
    assert len(result.items) == 20

    result2 = ls.discover(
        query="starbucks",
        center=[19.1663, 72.8526],
        country_codes=["IND"],
        limit=2,
    )
    assert len(result2.items) == 2

    result3 = ls.discover(
        query="starbucks",
        bounding_box=[13.08836, 52.33812, 13.761, 52.6755],
    )
    assert len(result3.items) == 20

    with pytest.raises(ValueError):
        ls.discover(
            query="starbucks",
            center=[52.5, 13.4],
            bounding_box=[13.08836, 52.33812, 13.761, 52.6755],
        )

    with pytest.raises(ApiError):
        ls2 = LS(api_key="dummy")
        ls2.discover(query="starbucks", center=[19.1663, 72.8526], radius=10000, limit=10)


@pytest.mark.skipif(not LS_API_KEY, reason="No api key found.")
def test_ls_browse():
    ls = LS(api_key=LS_API_KEY)
    result = ls.browse(
        center=[19.1663, 72.8526],
        radius=9000,
        limit=5,
        categories=["300-3000-0025", "300-3100.550-5510-0202", "500-5520,600-6100-0062"],
        lang="en",
    )
    assert len(result.items) == 5

    result2 = ls.browse(
        center=[19.1663, 72.8526],
        name="starbucks",
        country_codes=["IND"],
        limit=10,
        categories=["100-1000-0000"],
        lang="en",
    )
    assert len(result2.items) == 10

    result3 = ls.browse(
        center=[19.1663, 72.8526],
        name="starbucks",
        bounding_box=[13.08836, 52.33812, 13.761, 52.6755],
        categories=["100-1000-0000"],
        lang="en",
    )
    assert len(result3.items) == 20

    with pytest.raises(ApiError):
        ls2 = LS(api_key="dummy")
        ls2.browse(
            center=[19.1663, 72.8526],
            radius=9000,
            limit=5,
            categories=["300-3000-0025", "300-3100.550-5510-0202", "500-5520,600-6100-0062"],
        )


@pytest.mark.skipif(not LS_API_KEY, reason="No api key found.")
def test_ls_lookup():
    ls = LS(api_key=LS_API_KEY)
    result = ls.lookup(
        location_id="here:pds:place:276u0vhj-b0bace6448ae4b0fbc1d5e323998a7d2",
        lang="en",
    )
    assert result.response["title"] == "Frankfurt-Hahn Airport"

    with pytest.raises(ApiError):
        ls2 = LS(api_key="dummy")
        ls2.lookup(location_id="here:pds:place:276u0vhj-b0bace6448ae4b0fbc1d5e323998a7d2")


@pytest.mark.skipif(not LS_API_KEY, reason="No api key found.")
def test_credentials_exception():
    """Test exception if environment variable ``LS_API_KEY`` is not present."""
    api_key = os.environ.get("LS_API_KEY")
    del os.environ["LS_API_KEY"]
    with pytest.raises(Exception):
        _ = LS()
    os.environ["LS_API_KEY"] = api_key


@pytest.mark.skipif(not LS_API_KEY, reason="No api key found.")
def test_car_route():
    """Test routing API for car route."""
    ls = LS(api_key=LS_API_KEY)
    result = ls.car_route(
        origin=[52.51375, 13.42462],
        destination=[52.52332, 13.42800],
        via=[(52.52426, 13.43000)],
        return_results=[ROUTING_RETURN.polyline, ROUTING_RETURN.elevation],
        departure_time=datetime.now(),
        spans=[ROUTING_SPANS.names],
    )
    assert result.response["routes"][0]["sections"][0]["departure"]["place"]["location"] == {
        "lat": 52.5137479,
        "lng": 13.4246242,
        "elv": 76.0,
    }
    assert result.response["routes"][0]["sections"][1]["departure"]["place"]["location"] == {
        "lat": 52.5242323,
        "lng": 13.4301462,
        "elv": 80.0,
    }
    assert type(result.to_geojson()) == FeatureCollection


@pytest.mark.skipif(not LS_API_KEY, reason="No api key found.")
def test_car_route_extra_options():
    """Test routing API for car route."""
    place_options = PlaceOptions(
        course=ROUTE_COURSE.west,
        sideof_street_hint=[52.512149, 13.304076],
        match_sideof_street=ROUTE_MATCH_SIDEOF_STREET.always,
        radius=10,
        min_course_distance=10,
    )
    via_waypoint_options = WayPointOptions(stop_duration=0, pass_through=True)
    dest_waypoint_options = WayPointOptions(stop_duration=10, pass_through=False)
    ls = LS(api_key=LS_API_KEY)
    _ = ls.car_route(
        origin=[52.51375, 13.42462],
        destination=[52.52332, 13.42800],
        via=[(52.52426, 13.43000), (52.123, 13.22), (52.343, 13.444)],
        origin_place_options=place_options,
        destination_place_options=place_options,
        via_place_options=place_options,
        via_waypoint_options=via_waypoint_options,
        destination_waypoint_options=dest_waypoint_options,
        return_results=[ROUTING_RETURN.polyline, ROUTING_RETURN.elevation],
        departure_time=datetime.now(),
        spans=[ROUTING_SPANS.names],
    )


@pytest.mark.skipif(not LS_API_KEY, reason="No api key found.")
def test_bicycle_route():
    """Test routing API for car route."""
    ls = LS(api_key=LS_API_KEY)
    _ = ls.bicycle_route(
        origin=[52.51375, 13.42462],
        destination=[52.52332, 13.42800],
        via=[(52.52426, 13.43000)],
        return_results=[ROUTING_RETURN.polyline, ROUTING_RETURN.elevation],
        departure_time=datetime.now(),
        spans=[ROUTING_SPANS.names],
    )


@pytest.mark.skipif(not LS_API_KEY, reason="No api key found.")
def test_truck_route():
    """Test routing API for truck route."""
    ls = LS(api_key=LS_API_KEY)
    _ = ls.bicycle_route(
        origin=[52.51375, 13.42462],
        destination=[52.52332, 13.42800],
        via=[(52.52426, 13.43000)],
        return_results=[ROUTING_RETURN.polyline, ROUTING_RETURN.elevation],
        departure_time=datetime.now(),
        spans=[ROUTING_SPANS.names],
    )


@pytest.mark.skipif(not LS_API_KEY, reason="No api key found.")
def test_scooter_route():
    """Test routing API for scooter route."""
    ls = LS(api_key=LS_API_KEY)
    _ = ls.scooter_route(
        origin=[52.51375, 13.42462],
        destination=[52.52332, 13.42800],
        via=[(52.52426, 13.43000)],
        return_results=[ROUTING_RETURN.polyline, ROUTING_RETURN.elevation],
        departure_time=datetime.now(),
        spans=[ROUTING_SPANS.names],
    )


@pytest.mark.skipif(not LS_API_KEY, reason="No api key found.")
def test_pedestrian_route():
    """Test routing API for pedestrian route."""
    ls = LS(api_key=LS_API_KEY)
    _ = ls.pedestrian_route(
        origin=[52.51375, 13.42462],
        destination=[52.52332, 13.42800],
        via=[(52.52426, 13.43000)],
        return_results=[ROUTING_RETURN.polyline, ROUTING_RETURN.elevation],
        departure_time=datetime.now(),
        spans=[ROUTING_SPANS.names],
    )
