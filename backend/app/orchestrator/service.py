def _m6_response(success, intent, message, data=None):
    return {
        "success": success,
        "intent": intent,
        "data": data or {},
        "message": message,
        "next_action": None,
    }


def _call_m3():
    return "M3 called"


def _call_m2():
    return "M2 called"


def _call_m4():
    return "M4 called"


def _route_doctor_lookup(intent):
    services_called = [_call_m3()]
    return _m6_response(
        True,
        intent,
        "Routed doctor lookup through M3.",
        {"services_called": services_called},
    )


def _route_book_appointment(intent):
    services_called = [_call_m3(), _call_m2(), _call_m4()]
    return _m6_response(
        True,
        intent,
        "Routed appointment booking through M3, then M2, then M4.",
        {"services_called": services_called},
    )


def _route_bed_availability(intent):
    services_called = [_call_m2()]
    return _m6_response(
        True,
        intent,
        "Routed bed availability check through M2.",
        {"services_called": services_called},
    )


def _clarification_response(intent="UNKNOWN"):
    return _m6_response(
        True,
        intent,
        "I need a bit more information to help. Could you clarify what you need?",
        {"services_called": []},
    )


def process_request(intent_data):
    intent = "UNKNOWN"
    if isinstance(intent_data, dict):
        raw_intent = intent_data.get("intent", "UNKNOWN")
        if isinstance(raw_intent, str) and raw_intent.strip():
            intent = raw_intent.strip().upper()

    match intent:
        case "FIND_DOCTOR" | "CHECK_DOCTOR_AVAILABILITY":
            return _route_doctor_lookup(intent)
        case "BOOK_APPOINTMENT":
            return _route_book_appointment(intent)
        case "CHECK_BED_AVAILABILITY":
            return _route_bed_availability(intent)
        case "UNKNOWN":
            return _clarification_response()
        case _:
            return _clarification_response()
