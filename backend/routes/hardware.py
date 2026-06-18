"""
Hardware deployment status endpoint.
Currently returns mock data — replace with OPS database integration when ready.
"""
from fastapi import APIRouter

router = APIRouter()

# Deterministic mock: rotates through all 3 states based on last digit of deal_id
# so the UI can be tested with any deal.
def _mock_status(deal_id: str) -> dict:
    try:
        last = int(str(deal_id).strip()[-1])
    except (ValueError, IndexError):
        last = 0

    if last <= 3:
        return {"status": "Not Deployed", "deployment_date": None}
    elif last <= 6:
        return {"status": "Ongoing", "deployment_date": "2025-06-01"}
    else:
        return {"status": "Deployed", "deployment_date": "2025-01-15"}


@router.get("/api/deals/{deal_id}/hardware-status")
def get_hardware_status(deal_id: str):
    return _mock_status(deal_id)
