"""
Token & Queue module (Member 4).

Owns everything that happens AFTER a patient checks in for a confirmed
appointment: OPD token generation, queue ordering, position/wait-time
calculation, and doctor-side queue control (call / complete / skip).

This package deliberately does not import Patient, Appointment, or Doctor
ORM models from other modules -- see models.py and service.py for details
on how appointment verification is decoupled via a mockable client.
"""

from app.tokens.models import Token, TokenStatus

__all__ = ["Token", "TokenStatus"]