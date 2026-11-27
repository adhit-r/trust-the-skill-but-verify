"""HTTP routes for job submission and status."""

from .auth import require_token


def submit(request):
    require_token(request)
    # TODO: validate payload against the published schema
    return {"accepted": True}


def status(request, job_id):
    require_token(request)
    return {"job": job_id, "state": "unknown"}
