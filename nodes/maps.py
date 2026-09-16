from typing import Any, Dict, List, Optional
import requests

from state import Status
from utils.error_handling import should_retry


# ============================================================
# CONFIG
# ============================================================

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

HEADERS = {
    "User-Agent": "AI-Engineer-Tool-Agent/1.0"
}


# ============================================================
# BASIC HELPERS
# ============================================================

def normalize_text(text: str) -> str:
    return " ".join(
        str(text)
        .lower()
        .replace(",", " ")
        .replace("-", " ")
        .split()
    )


def words(text: str) -> List[str]:
    return [
        word
        for word in normalize_text(text).split()
        if len(word) > 2
    ]


def candidate_text(candidate: Dict[str, Any]) -> str:
    return normalize_text(
        " ".join(
            [
                str(candidate.get("display_name", "")),
                str(candidate.get("name", "")),
                str(candidate.get("type", "")),
                str(candidate.get("category", "")),
                str(candidate.get("class", "")),
            ]
        )
    )


def get_step(state):
    step = state.get("active_step")

    if step is not None:
        return step

    steps = state.get("steps", [])

    if steps:
        return steps[0]

    return None


# ============================================================
# LOCATION CONTEXT
# ============================================================

def infer_city_context(query: str, context: str = "") -> str:
    """
    Infer a useful geographic context from the request.

    This prevents generic names such as "Central" from
    resolving to unrelated countries.
    """

    combined = normalize_text(
        f"{query} {context}"
    )

    # Chennai-specific places
    chennai_places = [
        "marina beach",
        "chennai central",
        "egmore",
        "guindy",
        "tambaram",
        "velachery",
        "t nagar",
        "adyar",
        "anna nagar",
        "perambur",
        "koyambedu",
        "porur",
        "chromepet",
        "potheri",
        "srm",
        "ktr",
    ]

    for place in chennai_places:
        if place in combined:
            return "Chennai, Tamil Nadu, India"

    # Explicit Chennai
    if "chennai" in combined:
        return "Chennai, Tamil Nadu, India"

    # Other common Indian cities
    if "bangalore" in combined or "bengaluru" in combined:
        return "Bengaluru, Karnataka, India"

    if "mumbai" in combined:
        return "Mumbai, Maharashtra, India"

    if "delhi" in combined:
        return "Delhi, India"

    if "hyderabad" in combined:
        return "Hyderabad, Telangana, India"

    return ""


# ============================================================
# GEOCODING
# ============================================================

def geocode(query: str) -> List[Dict[str, Any]]:
    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": 8,
        "dedupe": 1,
    }

    response = requests.get(
        NOMINATIM_URL,
        params=params,
        headers=HEADERS,
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        return []

    return data


# ============================================================
# LOCATION TYPE DETECTION
# ============================================================

def expected_location_type(query: str) -> Optional[str]:

    q = normalize_text(query)

    if "airport" in q:
        return "airport"

    if "beach" in q:
        return "beach"

    if (
        "station" in q
        or "central" in q
        or "railway" in q
    ):
        return "station"

    if (
        "college" in q
        or "university" in q
        or "institute" in q
    ):
        return "education"

    return None


# ============================================================
# CANDIDATE SCORING
# ============================================================

def name_score(
    query: str,
    candidate: Dict[str, Any],
) -> float:

    q = normalize_text(query)

    text = candidate_text(candidate)

    score = 0.0

    if q in text:
        score += 50.0

    query_words = words(query)

    for word in query_words:
        if word in text:
            score += 8.0

    name = normalize_text(
        candidate.get("name", "")
    )

    if name and name == q:
        score += 50.0

    return score


def context_match_score(
    query: str,
    context: str,
    candidate: Dict[str, Any],
) -> float:

    if not context:
        return 0.0

    text = candidate_text(candidate)

    context_words = words(context)

    score = 0.0

    for word in context_words:

        if word in text:
            score += 15.0

    return score


def geographic_score(
    query: str,
    context: str,
    candidate: Dict[str, Any],
) -> float:

    text = candidate_text(candidate)

    score = 0.0

    combined_context = (
        f"{context} "
        f"{infer_city_context(query, context)}"
    )

    context_words = words(
        combined_context
    )

    important_words = {
        "chennai",
        "tamil",
        "nadu",
        "india",
        "delhi",
        "mumbai",
        "hyderabad",
        "bangalore",
        "bengaluru",
        "karnataka",
        "maharashtra",
        "telangana",
        "agra",
        "potheri",
        "ramapuram",
    }

    for word in context_words:

        if (
            word in important_words
            and word in text
        ):
            score += 30.0

    return score


def type_score(
    query: str,
    candidate: Dict[str, Any],
) -> float:

    expected = expected_location_type(query)

    if expected is None:
        return 0.0

    text = candidate_text(candidate)

    # --------------------------------------------------------
    # AIRPORT
    # --------------------------------------------------------

    if expected == "airport":

        if "airport" in text:

            if "bus depot" in text:
                return -100.0

            if "bus station" in text:
                return -100.0

            if "bus stop" in text:
                return -100.0

            return 100.0

        return -30.0

    # --------------------------------------------------------
    # BEACH
    # --------------------------------------------------------

    if expected == "beach":

        if "beach" in text:
            return 100.0

        return -30.0

    # --------------------------------------------------------
    # STATION
    # --------------------------------------------------------

    if expected == "station":

        if "railway station" in text:
            return 100.0

        if "train station" in text:
            return 100.0

        if "station" in text:
            return 70.0

        return -40.0

    # --------------------------------------------------------
    # EDUCATION
    # --------------------------------------------------------

    if expected == "education":

        if (
            "university" in text
            or "college" in text
            or "institute" in text
        ):
            return 80.0

        return -20.0

    return 0.0


def score_candidate(
    query: str,
    context: str,
    candidate: Dict[str, Any],
) -> float:

    return (
        name_score(
            query,
            candidate,
        )
        + context_match_score(
            query,
            context,
            candidate,
        )
        + geographic_score(
            query,
            context,
            candidate,
        )
        + type_score(
            query,
            candidate,
        )
    )


# ============================================================
# LOCATION RESOLUTION
# ============================================================

def resolve_location(
    query: str,
    context: str = "",
) -> Dict[str, Any]:

    query = str(query).strip()

    if not query:
        return {
            "status": "not_found",
            "location": query,
            "message": "Location was empty.",
        }

    try:
        candidates = geocode(query)
    except Exception as exc:
        return {
            "status": "not_found",
            "location": query,
            "message": (
                f"Could not search for location "
                f"'{query}': {exc}"
            ),
        }

    if not candidates:
        return {
            "status": "not_found",
            "location": query,
            "message": (
                f"Could not find location: {query}"
            ),
        }

    # ========================================================
    # SPECIAL CASE FOR "CENTRAL"
    #
    # Keep it ambiguous, but put Chennai Central first.
    # This allows the user to test numbered selection.
    # ========================================================

    if normalize_text(query) == "central":

        chennai_candidates = geocode(
            "Chennai Central railway station, Chennai, India"
        )

        combined = []

        if chennai_candidates:
            combined.append(
                chennai_candidates[0]
            )

        combined.extend(candidates)

        # Remove duplicate display names
        unique_candidates = []
        seen = set()

        for candidate in combined:

            display_name = candidate.get(
                "display_name",
                candidate.get(
                    "name",
                    "Unknown location",
                ),
            )

            key = normalize_text(
                display_name
            )

            if key in seen:
                continue

            seen.add(key)

            unique_candidates.append(
                candidate
            )

        # ----------------------------------------------------
        # Always show clarification for "Central"
        # ----------------------------------------------------

        top_candidates = unique_candidates[:3]

        candidate_names = []

        for candidate in top_candidates:

            name = candidate.get(
                "display_name",
                candidate.get(
                    "name",
                    query,
                ),
            )

            candidate_names.append(name)

        message = (
            f'I found multiple locations '
            f'matching "{query}".\n\n'
            "Did you mean:\n"
        )

        for index, name in enumerate(
            candidate_names,
            start=1,
        ):
            message += (
                f"{index}. {name}\n"
            )

        message += (
            f'\nPlease specify which '
            f'"{query}" you mean.'
        )

        return {
            "status": "clarification_required",
            "location": query,
            "message": message,
            "candidates": candidate_names,
        }

    # ========================================================
    # NORMAL SCORING FOR ALL OTHER LOCATIONS
    # ========================================================

    scored = []

    for candidate in candidates:

        score = score_candidate(
            query,
            context,
            candidate,
        )

        scored.append(
            (
                score,
                candidate,
            )
        )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    best_score, best_candidate = scored[0]

    # ========================================================
    # REAL AMBIGUITY
    # ========================================================

    if len(scored) > 1:

        second_score, _ = scored[1]

        score_difference = (
            best_score - second_score
        )

        if score_difference < 12:

            top_candidates = [
                item[1].get(
                    "display_name",
                    item[1].get(
                        "name",
                        query,
                    ),
                )
                for item in scored[:3]
            ]

            unique_candidates = []

            for item in top_candidates:

                if item not in unique_candidates:
                    unique_candidates.append(item)

            message = (
                f'I found multiple locations '
                f'matching "{query}".\n\n'
                "Did you mean:\n"
            )

            for index, item in enumerate(
                unique_candidates,
                start=1,
            ):
                message += (
                    f"{index}. {item}\n"
                )

            message += (
                f'\nPlease specify which '
                f'"{query}" you mean.'
            )

            return {
                "status": "clarification_required",
                "location": query,
                "message": message,
                "candidates": unique_candidates,
            }

    return {
        "status": "resolved",
        "candidate": best_candidate,
    }


# ============================================================
# ROUTING
# ============================================================

def get_route(
    origin: Dict[str, Any],
    destination: Dict[str, Any],
    mode: str = "driving",
) -> Dict[str, Any]:

    # --------------------------------------------------------
    # OSRM supports driving in this implementation.
    # --------------------------------------------------------

    mode = str(
        mode or "driving"
    ).lower()

    if mode != "driving":

        # Instead of crashing, fall back to driving.
        mode = "driving"

    origin_lon = float(
        origin["lon"]
    )

    origin_lat = float(
        origin["lat"]
    )

    destination_lon = float(
        destination["lon"]
    )

    destination_lat = float(
        destination["lat"]
    )

    coordinates = (
        f"{origin_lon},{origin_lat};"
        f"{destination_lon},{destination_lat}"
    )

    url = (
        f"{OSRM_URL}/{coordinates}"
    )

    params = {
        "overview": "false",
        "alternatives": "false",
        "steps": "false",
    }

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("code") != "Ok":

        raise RuntimeError(
            data.get(
                "message",
                "Routing service failed.",
            )
        )

    routes = data.get(
        "routes",
        []
    )

    if not routes:

        raise RuntimeError(
            "No route could be found."
        )

    route = routes[0]

    distance_km = round(
        float(route["distance"]) / 1000,
        2,
    )

    duration_minutes = round(
        float(route["duration"]) / 60
    )

    return {
        "distance_km": distance_km,
        "duration_minutes": duration_minutes,
        "mode": mode,
    }


# ============================================================
# MAPS NODE
# ============================================================

def maps_node(
    state: Dict[str, Any]
) -> Dict[str, Any]:

    step = get_step(state)

    if step is None:

        return {
            "outputs": {},
            "task_status": state.get(
                "task_status",
                {},
            ),
            "active_step": None,
            "error": "No active maps step.",
        }

    output_key = step.output_key

    task_status = dict(
        state.get(
            "task_status",
            {},
        )
    )

    previous = task_status.get(
        output_key,
        {}
    )

    retries = previous.get(
        "retries",
        0
    )

    # --------------------------------------------------------
    # MARK RUNNING
    # --------------------------------------------------------

    task_status[output_key] = {
        "status": Status.RUNNING,
        "retries": retries,
        "error": None,
    }

    try:

        tool_input = dict(
            step.tool_input or {}
        )

        origin_query = str(
            tool_input.get(
                "origin",
                "",
            )
        ).strip()

        destination_query = str(
            tool_input.get(
                "destination",
                "",
            )
        ).strip()

        mode = str(
            tool_input.get(
                "mode",
                "driving",
            )
        ).lower()

        if not origin_query:

            raise ValueError(
                "Origin location is required."
            )

        if not destination_query:

            raise ValueError(
                "Destination location is required."
            )

        # ----------------------------------------------------
        # ALWAYS NORMALIZE ROUTING MODE
        # ----------------------------------------------------

        if mode not in {
            "driving"
        }:
            mode = "driving"

        tool_input["mode"] = mode

        # ----------------------------------------------------
        # ORIGIN
        # ----------------------------------------------------

        origin_resolution = resolve_location(
            origin_query,
            context=destination_query,
        )

        if (
            origin_resolution["status"]
            == "clarification_required"
        ):

            message = origin_resolution[
                "message"
            ]

            task_status[output_key] = {
                "status": Status.FAILED,
                "retries": retries,
                "error": message,
            }

            return {
                "outputs": {
                    output_key: {
                        "status":
                            "clarification_required",
                        "location":
                            origin_query,
                        "message":
                            message,
                        "candidates":
                            origin_resolution.get(
                                "candidates",
                                [],
                            ),
                    }
                },
                "task_status": task_status,
                "active_step": None,
                "error": message,
            }

        if (
            origin_resolution["status"]
            == "not_found"
        ):

            message = origin_resolution[
                "message"
            ]

            task_status[output_key] = {
                "status": Status.FAILED,
                "retries": retries,
                "error": message,
            }

            return {
                "outputs": {
                    output_key: {
                        "status": "not_found",
                        "location": origin_query,
                        "message": message,
                    }
                },
                "task_status": task_status,
                "active_step": None,
                "error": message,
            }

        # ----------------------------------------------------
        # DESTINATION
        # ----------------------------------------------------

        destination_resolution = resolve_location(
            destination_query,
            context=origin_query,
        )

        if (
            destination_resolution["status"]
            == "clarification_required"
        ):

            message = destination_resolution[
                "message"
            ]

            task_status[output_key] = {
                "status": Status.FAILED,
                "retries": retries,
                "error": message,
            }

            return {
                "outputs": {
                    output_key: {
                        "status":
                            "clarification_required",
                        "location":
                            destination_query,
                        "message":
                            message,
                        "candidates":
                            destination_resolution.get(
                                "candidates",
                                [],
                            ),
                    }
                },
                "task_status": task_status,
                "active_step": None,
                "error": message,
            }

        if (
            destination_resolution["status"]
            == "not_found"
        ):

            message = destination_resolution[
                "message"
            ]

            task_status[output_key] = {
                "status": Status.FAILED,
                "retries": retries,
                "error": message,
            }

            return {
                "outputs": {
                    output_key: {
                        "status": "not_found",
                        "location":
                            destination_query,
                        "message": message,
                    }
                },
                "task_status": task_status,
                "active_step": None,
                "error": message,
            }

        # ----------------------------------------------------
        # GET RESOLVED LOCATIONS
        # ----------------------------------------------------

        origin = origin_resolution[
            "candidate"
        ]

        destination = destination_resolution[
            "candidate"
        ]

        # ----------------------------------------------------
        # ROUTE
        # ----------------------------------------------------

        route = get_route(
            origin,
            destination,
            mode=mode,
        )

        distance_km = route[
            "distance_km"
        ]

        duration_minutes = route[
            "duration_minutes"
        ]

        result = (
            f"The route from "
            f"{origin_query} to "
            f"{destination_query} "
            f"is approximately "
            f"{distance_km} km and takes "
            f"around {duration_minutes} "
            f"minutes by driving."
        )

        # ----------------------------------------------------
        # COMPLETED
        # ----------------------------------------------------

        task_status[output_key] = {
            "status": Status.COMPLETED,
            "retries": retries,
            "error": None,
        }

        return {
            "outputs": {
                output_key: result,
            },
            "task_status": task_status,
            "active_step": None,
            "error": None,
        }

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as exc:

        error_message = str(exc)

        if should_retry(
            state,
            output_key,
            error_message,
        ):

            task_status[output_key] = {
                "status": Status.PENDING,
                "retries": retries + 1,
                "error": error_message,
            }

        else:

            task_status[output_key] = {
                "status": Status.FAILED,
                "retries": retries,
                "error": error_message,
            }

        return {
            "outputs": {},
            "task_status": task_status,
            "active_step": None,
            "error": error_message,
        }