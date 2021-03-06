# Copyright (C) 2019-2021 HERE Europe B.V.
# SPDX-License-Identifier: Apache-2.0

"""This module contains class to interact with Location services REST APIs."""

import os
import urllib
import urllib.request
from datetime import datetime
from typing import List, Optional, Tuple

from here_location_services.config.routing_config import PlaceOptions, Scooter, WayPointOptions

from .geocoding_search_api import GeocodingSearchApi
from .isoline_routing_api import IsolineRoutingApi
from .responses import (
    BrowseResponse,
    DiscoverResponse,
    GeocoderResponse,
    IsolineResponse,
    LookupResponse,
    ReverseGeocoderResponse,
    RoutingResponse,
)
from .routing_api import RoutingApi


class LS:
    """
    A single interface for the user to interact with rest of
    the Location services APIs.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        proxies: Optional[dict] = None,
        country: str = "row",
    ):
        api_key = api_key or os.environ.get("LS_API_KEY")
        self.credentials = dict(api_key=api_key)
        self.proxies = proxies or urllib.request.getproxies()
        self.geo_search_api = GeocodingSearchApi(
            api_key=api_key,
            proxies=proxies,
            country=country,
        )
        self.isoline_routing_api = IsolineRoutingApi(
            api_key=api_key,
            proxies=proxies,
            country=country,
        )
        self.routing_api = RoutingApi(
            api_key=api_key,
            proxies=proxies,
            country=country,
        )

    def geocode(self, query: str, limit: int = 20, lang: str = "en-US") -> GeocoderResponse:
        """Calculate coordinates as result of geocoding for the given ``query``.

        :param query: A string containing the input query.
        :param limit: An int representing maximum number of results to be returned.
            Default value is 20.
        :param lang: A string to represent language to be used for result rendering from
            a list of BCP47 compliant Language Codes.
        :raises ValueError: If ``query`` is empty or having all whitespace characters.
        :return: :class:`GeocoderResponse` object.
        """
        if not query or query.isspace():
            raise ValueError(f"Invalid input query: {query}")

        resp = self.geo_search_api.get_geocoding(query, limit=limit, lang=lang)
        return GeocoderResponse.new(resp.json())

    def reverse_geocode(
        self, lat: float, lng: float, limit: int = 1, lang: str = "en-US"
    ) -> ReverseGeocoderResponse:
        """
        Return the address label string as the result of reverse-geocoding the
        given ``latitude`` and ``longitude``.

        :param lat: A float representing latitude of point.
        :param lng: A float representing longitude of point.
        :param limit: An int representing maximum number of results to be returned.
            Default value is 1.
        :param lang: A string to represent language to be used for result rendering from
            a list of BCP47 compliant Language Codes.
        :raises ValueError: If Latitude is not in range between -90 and 90 or
             Longitude is not in range between -180 and 180.
        :return: :class:`ReverseGeocoderResponse` object.
        """
        if not -90 <= lat <= 90:
            raise ValueError("Latitude must be in range -90 to 90.")
        if not -180 <= lng <= 180:
            raise ValueError("Longitude must be in range -180 to 180.")

        resp = self.geo_search_api.get_reverse_geocoding(lat=lat, lng=lng, limit=limit, lang=lang)
        return ReverseGeocoderResponse.new(resp.json())

    def calculate_isoline(
        self,
        mode: str,
        range: str,
        range_type: str,
        start: Optional[List[float]] = None,
        destination: Optional[List[float]] = None,
        arrival: Optional[str] = None,
        departure: Optional[str] = None,
    ) -> IsolineResponse:
        """Calculate isoline routing.

        Request a polyline that connects the endpoints of all routes
        leaving from one defined center with either a specified length
        or specified travel time.

        :param mode: A string representing how the route is calculated.
            Example: ``Type;TransportModes;TrafficMode;Feature``.
            ``fastest;car;traffic:disabled;motorway:-3``
        :param range: A string representing a range of isoline, unit is defined by
            parameter range type. Example: range='1000' or range='1000,2000,3000'
        :param range_type: A string representing a type of `range`. Possible values are
            ``distance``, ``time`` and ``consumption``. For distance the unit meters. For a
            time the unit is seconds.For consumption, it is defined by the consumption
            model.
        :param start: A list of latitude and longitude representing the center of isoline
            request. Isoline will cover all the roads which can be reached from this
            point within a given range. It can not be used in combination with the
            ``destination`` parameter.
        :param destination: A list of latitude and longitude representing the center of
            isoline request. Isoline will cover all roads from which this point can be
            reached within a given range. It can not be used in combination with the
            ``start`` parameter.
        :param arrival: A string representing the time when travel is expected to end.
            It can be used only if the parameter ``destination`` is also used.
            Example: arrival= '2013-07-04T17:00:00+02'.
        :param departure: A string representing the time when travel is expected to
            start. It can be used only if the parameter ``start`` is also used.
            Example: departure= '2013-07-04T17:00:00+02'
        :raises ValueError: If ``start`` and ``destination`` are provided togrther.
        :return: :class:`IsolineResponse` object.
        """

        if start and destination:
            raise ValueError("`start` and `destination` can not be provided together.")
        if start is None and destination is None:
            raise ValueError("please provide either `start` or `destination`.")
        if departure and start is None:
            raise ValueError("`departure` must be provided with `start`")
        if arrival and destination is None:
            raise ValueError("`arrival` must be provided with `destination`")

        resp = self.isoline_routing_api.get_isoline_routing(
            mode=mode,
            range=range,
            range_type=range_type,
            start=start,
            destination=destination,
            arrival=arrival,
            departure=departure,
        )
        response = resp.json()["response"]
        return IsolineResponse.new(response)

    def discover(
        self,
        query: str,
        center: Optional[List[float]] = None,
        radius: Optional[int] = None,
        country_codes: Optional[List] = None,
        bounding_box: Optional[List[float]] = None,
        limit: Optional[int] = None,
        lang: Optional[str] = None,
    ) -> DiscoverResponse:
        """Search places using Location Services discover endpoint.

        This method uses location services ``discover`` endpoint to search places based on
        query which is free-form text.
        There are three different combination of inputs as shown below to search places
        using discover:

        - ``center`` and ``country_code``
        - ``center`` and ``radius``
        - ``bounding_box``

        :param query: A string representing free-text query to search places.
        :param center: A list of latitude and longitude representing the center for
            search query.
        :param radius: A radius in meters along with center for searching places.
        :param country_codes: A list of  ISO 3166-1 alpha-3 country codes.
        :param bounding_box: A bounding box, provided as west longitude, south latitude,
            east longitude, north latitude.
        :param limit: An int representing maximum number of results to be returned.
        :param lang: A string to represent language to be used for result rendering from
            a list of BCP47 compliant Language Codes.
        :raises ValueError: If ``center`` and ``bounding_box`` are provided together.
        :return: :class:`DiscoverResponse` object.
        """
        if center and bounding_box:
            raise ValueError(
                f"Params: center:{center} and bounding_box:{bounding_box} "
                f"can not be provided together."
            )

        resp = self.geo_search_api.get_search_discover(
            query=query,
            center=center,
            radius=radius,
            country_codes=country_codes,
            bounding_box=bounding_box,
            limit=limit,
            lang=lang,
        )
        return DiscoverResponse.new(resp.json())

    def browse(
        self,
        center: List,
        radius: Optional[int] = None,
        country_codes: Optional[List] = None,
        bounding_box: Optional[List[float]] = None,
        categories: Optional[List] = None,
        limit: Optional[int] = None,
        name: Optional[str] = None,
        lang: Optional[str] = None,
    ) -> BrowseResponse:
        """Get search results for places based on different filters such as categories or name.

        :param center: A list of latitude and longitude representing the center for
            search query.
        :param radius: A radius in meters along with center for searching places.
        :param country_codes: A list of  ISO 3166-1 alpha-3 country codes.
        :param bounding_box: A bounding box, provided as west longitude, south latitude,
            east longitude, north latitude.
        :param categories: A list strings of category-ids.
        :param limit: An int representing maximum number of results to be returned.
        :param name: A string representing Full-text filter on POI names/titles.
        :param lang: A string to represent language to be used for result rendering from
            a list of BCP47 compliant Language Codes.
        :return: :class:`BrowseResponse` object.
        """
        resp = self.geo_search_api.get_search_browse(
            center=center,
            radius=radius,
            country_codes=country_codes,
            bounding_box=bounding_box,
            categories=categories,
            limit=limit,
            name=name,
            lang=lang,
        )
        return BrowseResponse.new(resp.json())

    def lookup(self, location_id: str, lang: Optional[str] = None) -> LookupResponse:
        """
        Get search results by providing ``location_id``.

        :param location_id: A string representing id.
        :param lang: A string to represent language to be used for result rendering from
            a list of BCP47 compliant Language Codes.
        :return: :class:`LookupResponse` object.
        """
        resp = self.geo_search_api.get_search_lookup(location_id=location_id, lang=lang)
        return LookupResponse.new(resp.json())

    def car_route(
        self,
        origin: List,
        destination: List,
        via: Optional[List[Tuple]] = None,
        origin_place_options: Optional[PlaceOptions] = None,
        destination_place_options: Optional[PlaceOptions] = None,
        via_place_options: Optional[PlaceOptions] = None,
        destination_waypoint_options: Optional[WayPointOptions] = None,
        via_waypoint_options: Optional[WayPointOptions] = None,
        departure_time: Optional[datetime] = None,
        routing_mode: str = "fast",
        alternatives: int = 0,
        units: str = "metric",
        lang: str = "en-US",
        return_results: Optional[List] = None,
        spans: Optional[List] = None,
    ) -> RoutingResponse:
        """Calculate ``car`` route between two endpoints.

        :param origin: A list of ``latitude`` and ``longitude`` of origin point of route.
        :param destination: A list of ``latitude`` and ``longitude`` of destination point of route.
        :param via: A list of tuples of ``latitude`` and ``longitude`` of via points.
        :param origin_place_options: :class:`PlaceOptions` optinal place options for ``origin``.
        :param destination_place_options: :class:`PlaceOptions` optinal place options
            for ``destination``.
        :param via_place_options: :class:`PlaceOptions` optinal place options for ``via``.
        :param destination_waypoint_options: :class:`WayPointOptions` optional waypoint options
            for ``destination``.
        :param via_waypoint_options: :class:`WayPointOptions` optional waypoint options for
            ``via``.
        :param departure_time: :class:`datetime.datetime` object.
        :param routing_mode: A string to represent routing mode. use config defined in :attr:`ROUTING_MODE <here_location_services.config.routing_config.ROUTING_MODE>`  # noqa: E501
        :param alternatives: Number of alternative routes to return aside from the optimal route.
            default value is ``0`` and maximum is ``6``.
        :param units: A string representing units of measurement used in guidance instructions.
            The default is metric.
        :param lang: A string representing preferred language of the response.
            The value should comply with the IETF BCP 47.
        :param return_results: A list of strings.
        :param spans: A list of strings to define which attributes are included in the response
            spans. use config defined in :attr:`ROUTING_SPANS <here_location_services.config.routing_config.ROUTING_SPANS>`  # noqa: E501
        :return: :class:`RoutingResponse` object.
        """
        resp = self.routing_api.route(
            transport_mode="car",
            origin=origin,
            destination=destination,
            via=via,
            origin_place_options=origin_place_options,
            destination_place_options=destination_place_options,
            via_place_options=via_place_options,
            destination_waypoint_options=destination_waypoint_options,
            via_waypoint_options=via_waypoint_options,
            departure_time=departure_time,
            routing_mode=routing_mode,
            alternatives=alternatives,
            units=units,
            lang=lang,
            return_results=return_results,
            spans=spans,
        )
        return RoutingResponse.new(resp.json())

    def bicycle_route(
        self,
        origin: List,
        destination: List,
        via: Optional[List[Tuple]] = None,
        origin_place_options: Optional[PlaceOptions] = None,
        destination_place_options: Optional[PlaceOptions] = None,
        via_place_options: Optional[PlaceOptions] = None,
        destination_waypoint_options: Optional[WayPointOptions] = None,
        via_waypoint_options: Optional[WayPointOptions] = None,
        departure_time: Optional[datetime] = None,
        routing_mode: str = "fast",
        alternatives: int = 0,
        units: str = "metric",
        lang: str = "en-US",
        return_results: Optional[List] = None,
        spans: Optional[List] = None,
    ) -> RoutingResponse:
        """Calculate ``bicycle`` route between two endpoints.

        :param origin: A list of ``latitude`` and ``longitude`` of origin point of route.
        :param destination: A list of ``latitude`` and ``longitude`` of destination point of route.
        :param via: A list of tuples of ``latitude`` and ``longitude`` of via points.
        :param origin_place_options: :class:`PlaceOptions` optinal place options for ``origin``.
        :param destination_place_options: :class:`PlaceOptions` optinal place options
            for ``destination``.
        :param via_place_options: :class:`PlaceOptions` optinal place options for ``via``.
        :param destination_waypoint_options: :class:`WayPointOptions` optional waypoint options
            for ``destination``.
        :param via_waypoint_options: :class:`WayPointOptions` optional waypoint options for
            ``via``.
        :param departure_time: :class:`datetime.datetime` object.
        :param routing_mode: A string to represent routing mode.
        :param alternatives: Number of alternative routes to return aside from the optimal route.
            default value is ``0`` and maximum is ``6``.
        :param units: A string representing units of measurement used in guidance instructions.
            The default is metric.
        :param lang: A string representing preferred language of the response.
            The value should comply with the IETF BCP 47.
        :param return_results: A list of strings.
        :param spans: A list of strings to define which attributes are included in the response
            spans.
        :return: :class:`RoutingResponse` object.
        """
        resp = self.routing_api.route(
            transport_mode="bicycle",
            origin=origin,
            destination=destination,
            via=via,
            origin_place_options=origin_place_options,
            destination_place_options=destination_place_options,
            via_place_options=via_place_options,
            destination_waypoint_options=destination_waypoint_options,
            via_waypoint_options=via_waypoint_options,
            departure_time=departure_time,
            routing_mode=routing_mode,
            alternatives=alternatives,
            units=units,
            lang=lang,
            return_results=return_results,
            spans=spans,
        )
        return RoutingResponse.new(resp.json())

    def truck_route(
        self,
        origin: List,
        destination: List,
        via: Optional[List[Tuple]] = None,
        origin_place_options: Optional[PlaceOptions] = None,
        destination_place_options: Optional[PlaceOptions] = None,
        via_place_options: Optional[PlaceOptions] = None,
        destination_waypoint_options: Optional[WayPointOptions] = None,
        via_waypoint_options: Optional[WayPointOptions] = None,
        departure_time: Optional[datetime] = None,
        routing_mode: str = "fast",
        alternatives: int = 0,
        units: str = "metric",
        lang: str = "en-US",
        return_results: Optional[List] = None,
        spans: Optional[List] = None,
    ) -> RoutingResponse:
        """Calculate ``truck`` route between two endpoints.

        :param origin: A list of ``latitude`` and ``longitude`` of origin point of route.
        :param destination: A list of ``latitude`` and ``longitude`` of destination point of route.
        :param via: A list of tuples of ``latitude`` and ``longitude`` of via points.
        :param origin_place_options: :class:`PlaceOptions` optinal place options for ``origin``.
        :param destination_place_options: :class:`PlaceOptions` optinal place options
            for ``destination``.
        :param via_place_options: :class:`PlaceOptions` optinal place options for ``via``.
        :param destination_waypoint_options: :class:`WayPointOptions` optional waypoint options
            for ``destination``.
        :param via_waypoint_options: :class:`WayPointOptions` optional waypoint options for
            ``via``.
        :param departure_time: :class:`datetime.datetime` object.
        :param routing_mode: A string to represent routing mode.
        :param alternatives: Number of alternative routes to return aside from the optimal route.
            default value is ``0`` and maximum is ``6``.
        :param units: A string representing units of measurement used in guidance instructions.
            The default is metric.
        :param lang: A string representing preferred language of the response.
            The value should comply with the IETF BCP 47.
        :param return_results: A list of strings.
        :param spans: A list of strings to define which attributes are included in the response
            spans.
        :return: :class:`RoutingResponse` object.
        """
        resp = self.routing_api.route(
            transport_mode="truck",
            origin=origin,
            destination=destination,
            via=via,
            origin_place_options=origin_place_options,
            destination_place_options=destination_place_options,
            via_place_options=via_place_options,
            destination_waypoint_options=destination_waypoint_options,
            via_waypoint_options=via_waypoint_options,
            departure_time=departure_time,
            routing_mode=routing_mode,
            alternatives=alternatives,
            units=units,
            lang=lang,
            return_results=return_results,
            spans=spans,
        )
        return RoutingResponse.new(resp.json())

    def scooter_route(
        self,
        origin: List,
        destination: List,
        via: Optional[List[Tuple]] = None,
        origin_place_options: Optional[PlaceOptions] = None,
        destination_place_options: Optional[PlaceOptions] = None,
        via_place_options: Optional[PlaceOptions] = None,
        destination_waypoint_options: Optional[WayPointOptions] = None,
        via_waypoint_options: Optional[WayPointOptions] = None,
        scooter: Optional[Scooter] = None,
        departure_time: Optional[datetime] = None,
        routing_mode: str = "fast",
        alternatives: int = 0,
        units: str = "metric",
        lang: str = "en-US",
        return_results: Optional[List] = None,
        spans: Optional[List] = None,
    ) -> RoutingResponse:
        """Calculate ``scooter`` route between two endpoints.

        :param origin: A list of ``latitude`` and ``longitude`` of origin point of route.
        :param destination: A list of ``latitude`` and ``longitude`` of destination point of route.
        :param via: A list of tuples of ``latitude`` and ``longitude`` of via points.
        :param origin_place_options: :class:`PlaceOptions` optinal place options for ``origin``.
        :param destination_place_options: :class:`PlaceOptions` optinal place options
            for ``destination``.
        :param via_place_options: :class:`PlaceOptions` optinal place options for ``via``.
        :param destination_waypoint_options: :class:`WayPointOptions` optional waypoint options
            for ``destination``.
        :param via_waypoint_options: :class:`WayPointOptions` optional waypoint options for
            ``via``.
        :param scooter: Additional attributes for scooter route.
        :param departure_time: :class:`datetime.datetime` object.
        :param routing_mode: A string to represent routing mode.
        :param alternatives: Number of alternative routes to return aside from the optimal route.
            default value is ``0`` and maximum is ``6``.
        :param units: A string representing units of measurement used in guidance instructions.
            The default is metric.
        :param lang: A string representing preferred language of the response.
            The value should comply with the IETF BCP 47.
        :param return_results: A list of strings.
        :param spans: A list of strings to define which attributes are included in the response
            spans.
        :return: :class:`RoutingResponse` object.
        """
        resp = self.routing_api.route(
            transport_mode="scooter",
            origin=origin,
            destination=destination,
            via=via,
            origin_place_options=origin_place_options,
            destination_place_options=destination_place_options,
            via_place_options=via_place_options,
            destination_waypoint_options=destination_waypoint_options,
            via_waypoint_options=via_waypoint_options,
            scooter=scooter,
            departure_time=departure_time,
            routing_mode=routing_mode,
            alternatives=alternatives,
            units=units,
            lang=lang,
            return_results=return_results,
            spans=spans,
        )
        return RoutingResponse.new(resp.json())

    def pedestrian_route(
        self,
        origin: List,
        destination: List,
        via: Optional[List[Tuple]] = None,
        origin_place_options: Optional[PlaceOptions] = None,
        destination_place_options: Optional[PlaceOptions] = None,
        via_place_options: Optional[PlaceOptions] = None,
        destination_waypoint_options: Optional[WayPointOptions] = None,
        via_waypoint_options: Optional[WayPointOptions] = None,
        departure_time: Optional[datetime] = None,
        routing_mode: str = "fast",
        alternatives: int = 0,
        units: str = "metric",
        lang: str = "en-US",
        return_results: Optional[List] = None,
        spans: Optional[List] = None,
    ) -> RoutingResponse:
        """Calculate ``pedestrian`` route between two endpoints.

        :param origin: A list of ``latitude`` and ``longitude`` of origin point of route.
        :param destination: A list of ``latitude`` and ``longitude`` of destination point of route.
        :param via: A list of tuples of ``latitude`` and ``longitude`` of via points.
        :param origin_place_options: :class:`PlaceOptions` optinal place options for ``origin``.
        :param destination_place_options: :class:`PlaceOptions` optinal place options
            for ``destination``.
        :param via_place_options: :class:`PlaceOptions` optinal place options for ``via``.
        :param destination_waypoint_options: :class:`WayPointOptions` optional waypoint options
            for ``destination``.
        :param via_waypoint_options: :class:`WayPointOptions` optional waypoint options for
            ``via``.
        :param departure_time: :class:`datetime.datetime` object.
        :param routing_mode: A string to represent routing mode.
        :param alternatives: Number of alternative routes to return aside from the optimal route.
            default value is ``0`` and maximum is ``6``.
        :param units: A string representing units of measurement used in guidance instructions.
            The default is metric.
        :param lang: A string representing preferred language of the response.
            The value should comply with the IETF BCP 47.
        :param return_results: A list of strings.
        :param spans: A list of strings to define which attributes are included in the response
            spans.
        :return: :class:`RoutingResponse` object.
        """
        resp = self.routing_api.route(
            transport_mode="pedestrian",
            origin=origin,
            destination=destination,
            via=via,
            origin_place_options=origin_place_options,
            destination_place_options=destination_place_options,
            via_place_options=via_place_options,
            destination_waypoint_options=destination_waypoint_options,
            via_waypoint_options=via_waypoint_options,
            departure_time=departure_time,
            routing_mode=routing_mode,
            alternatives=alternatives,
            units=units,
            lang=lang,
            return_results=return_results,
            spans=spans,
        )
        return RoutingResponse.new(resp.json())
