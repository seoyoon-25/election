"""
Google Calendar API endpoints.

Provides endpoints for:
- OAuth connection flow
- Listing events from Google Calendar
- Creating/updating/deleting events
"""

from datetime import datetime
from typing import Annotated, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db,
    get_campaign_membership,
    require_permission,
    CampaignMember,
)
from app.config import get_settings
from app.models import CampaignMembership, Permission
from app.schemas.google_calendar import (
    OAuthStartResponse,
    GoogleCalendarConnectionResponse,
    GoogleCalendarConnectionStatus,
    GoogleCalendarDisconnectResponse,
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventResponse,
    CalendarEventList,
)
from app.services.google_auth_service import (
    GoogleAuthService,
    OAuthStateStore,
    OAuthFlowError,
    ConnectionNotFoundError,
)
from app.services.google_calendar_service import (
    GoogleCalendarService,
    CalendarNotConnectedError,
    EventNotFoundError,
    CalendarAPIError,
)


router = APIRouter(prefix="/campaigns/{campaign_id}/calendar", tags=["Calendar"])


# =============================================================================
# OAuth Flow Endpoints
# =============================================================================


@router.get("/connect", response_model=OAuthStartResponse)
async def start_oauth_flow(
    campaign_id: int,
    membership: CampaignMember,
    redirect_uri: str = Query(
        ...,
        description="Frontend URL to redirect to after OAuth completes",
    ),
    db: AsyncSession = Depends(get_db),
    _: Annotated[None, Depends(require_permission(Permission.CAMPAIGN_EDIT))] = None,
):
    """
    Start Google OAuth flow to connect a calendar.

    Returns an authorization URL to redirect the user to Google's consent screen.
    After authorization, Google will redirect back to our callback endpoint.
    """
    settings = get_settings()

    # Build callback URL (our backend endpoint)
    callback_url = f"{settings.api_base_url}/api/v1/campaigns/{campaign_id}/calendar/callback"

    auth_service = GoogleAuthService(db)
    authorization_url, state = auth_service.get_authorization_url(
        campaign_id=campaign_id,
        redirect_uri=callback_url,
        frontend_redirect_uri=redirect_uri,
    )

    return OAuthStartResponse(
        authorization_url=authorization_url,
        state=state,
    )


@router.get("/callback")
async def oauth_callback(
    campaign_id: int,
    code: Optional[str] = Query(None),
    state: str = Query(...),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Google OAuth callback.

    This endpoint is called by Google after user authorization.
    It exchanges the authorization code for tokens and redirects to the frontend.
    """
    settings = get_settings()

    # Validate state and get redirect URI
    state_data = OAuthStateStore.validate_state(state)
    if state_data is None:
        # State expired or invalid - redirect with error
        frontend_url = f"{settings.frontend_base_url}/campaigns/{campaign_id}/settings/calendar"
        params = urlencode({
            "status": "error",
            "error": "invalid_state",
            "message": "Session expired. Please try again.",
        })
        return RedirectResponse(url=f"{frontend_url}?{params}")

    frontend_redirect = state_data["redirect_uri"]

    # Check for OAuth error
    if error:
        params = urlencode({
            "status": "error",
            "error": error,
            "message": error_description or "Authorization was denied.",
        })
        return RedirectResponse(url=f"{frontend_redirect}?{params}")

    if not code:
        params = urlencode({
            "status": "error",
            "error": "no_code",
            "message": "No authorization code received.",
        })
        return RedirectResponse(url=f"{frontend_redirect}?{params}")

    try:
        # Build callback URL for token exchange
        callback_url = f"{settings.api_base_url}/api/v1/campaigns/{campaign_id}/calendar/callback"

        auth_service = GoogleAuthService(db)

        # Re-create state for exchange (we already validated it)
        OAuthStateStore._states[state] = state_data

        await auth_service.exchange_code_for_tokens(
            code=code,
            state=state,
            redirect_uri=callback_url,
        )

        # Success - redirect to frontend
        params = urlencode({"status": "success"})
        return RedirectResponse(url=f"{frontend_redirect}?{params}")

    except OAuthFlowError as e:
        params = urlencode({
            "status": "error",
            "error": "oauth_failed",
            "message": str(e),
        })
        return RedirectResponse(url=f"{frontend_redirect}?{params}")
    except Exception as e:
        params = urlencode({
            "status": "error",
            "error": "unexpected_error",
            "message": "An unexpected error occurred. Please try again.",
        })
        return RedirectResponse(url=f"{frontend_redirect}?{params}")


@router.delete("/disconnect", response_model=GoogleCalendarDisconnectResponse)
async def disconnect_calendar(
    campaign_id: int,
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
    _: Annotated[None, Depends(require_permission(Permission.CAMPAIGN_EDIT))] = None,
):
    """
    Disconnect Google Calendar from this campaign.

    Revokes OAuth tokens and removes the connection.
    """
    try:
        auth_service = GoogleAuthService(db)
        await auth_service.disconnect_calendar(campaign_id)

        return GoogleCalendarDisconnectResponse(
            success=True,
            message="Google Calendar disconnected successfully.",
        )

    except ConnectionNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Google Calendar connection found.",
        )


@router.get("/status", response_model=GoogleCalendarConnectionStatus)
async def get_connection_status(
    campaign_id: int,
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
    _: Annotated[None, Depends(require_permission(Permission.EVENT_VIEW))] = None,
):
    """
    Get the current Google Calendar connection status.

    Returns connection details including the connected account email
    and last sync time.
    """
    service = GoogleCalendarService(db)
    return await service.get_connection_status(campaign_id)


@router.get("/connection", response_model=GoogleCalendarConnectionResponse)
async def get_connection_details(
    campaign_id: int,
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
    _: Annotated[None, Depends(require_permission(Permission.CAMPAIGN_EDIT))] = None,
):
    """
    Get detailed Google Calendar connection information.

    Returns full connection details for admin view.
    """
    auth_service = GoogleAuthService(db)
    connection = await auth_service.get_connection(campaign_id)

    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Google Calendar connection found.",
        )

    return connection


# =============================================================================
# Event Endpoints
# =============================================================================


@router.get("/events", response_model=CalendarEventList)
async def list_events(
    campaign_id: int,
    membership: CampaignMember,
    time_min: Optional[datetime] = Query(
        None,
        description="Start of time range (defaults to now)",
    ),
    time_max: Optional[datetime] = Query(
        None,
        description="End of time range (defaults to 30 days from now)",
    ),
    max_results: int = Query(
        50,
        ge=1,
        le=250,
        description="Maximum number of events to return",
    ),
    page_token: Optional[str] = Query(
        None,
        description="Token for pagination",
    ),
    db: AsyncSession = Depends(get_db),
    _: Annotated[None, Depends(require_permission(Permission.EVENT_VIEW))] = None,
):
    """
    List events from the connected Google Calendar.

    Returns events within the specified time range, sorted by start time.
    Supports pagination for large result sets.
    """
    try:
        service = GoogleCalendarService(db)
        return await service.list_events(
            campaign_id=campaign_id,
            time_min=time_min,
            time_max=time_max,
            max_results=max_results,
            page_token=page_token,
        )

    except CalendarNotConnectedError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Google Calendar connected. Please connect a calendar first.",
        )
    except CalendarAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@router.post(
    "/events",
    response_model=CalendarEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_event(
    campaign_id: int,
    event_data: CalendarEventCreate,
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
    _: Annotated[None, Depends(require_permission(Permission.EVENT_CREATE))] = None,
):
    """
    Create an event in the connected Google Calendar.

    The event will be synced to our local cache for audit purposes.
    Attendees will receive email notifications if send_notifications is True.
    """
    try:
        service = GoogleCalendarService(db)
        return await service.create_event(
            campaign_id=campaign_id,
            event_data=event_data,
            created_by_id=membership.id,
        )

    except CalendarNotConnectedError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Google Calendar connected. Please connect a calendar first.",
        )
    except CalendarAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@router.get("/events/{event_id}", response_model=CalendarEventResponse)
async def get_event(
    campaign_id: int,
    event_id: str,
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
    _: Annotated[None, Depends(require_permission(Permission.EVENT_VIEW))] = None,
):
    """
    Get a single event from the connected Google Calendar.
    """
    try:
        service = GoogleCalendarService(db)
        return await service.get_event(
            campaign_id=campaign_id,
            event_id=event_id,
        )

    except CalendarNotConnectedError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Google Calendar connected.",
        )
    except EventNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found.",
        )
    except CalendarAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@router.patch("/events/{event_id}", response_model=CalendarEventResponse)
async def update_event(
    campaign_id: int,
    event_id: str,
    event_data: CalendarEventUpdate,
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
    _: Annotated[None, Depends(require_permission(Permission.EVENT_EDIT_ALL))] = None,
):
    """
    Update an event in the connected Google Calendar.

    Only provided fields will be updated. Attendees will receive
    notifications if send_notifications is True.
    """
    try:
        service = GoogleCalendarService(db)
        return await service.update_event(
            campaign_id=campaign_id,
            event_id=event_id,
            event_data=event_data,
        )

    except CalendarNotConnectedError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Google Calendar connected.",
        )
    except EventNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found.",
        )
    except CalendarAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    campaign_id: int,
    event_id: str,
    membership: CampaignMember,
    send_notifications: bool = Query(
        True,
        description="Whether to send cancellation notifications to attendees",
    ),
    db: AsyncSession = Depends(get_db),
    _: Annotated[None, Depends(require_permission(Permission.EVENT_DELETE))] = None,
):
    """
    Delete an event from the connected Google Calendar.

    The event will also be removed from our local cache.
    Attendees will receive cancellation notifications if send_notifications is True.
    """
    try:
        service = GoogleCalendarService(db)
        await service.delete_event(
            campaign_id=campaign_id,
            event_id=event_id,
            send_notifications=send_notifications,
        )

    except CalendarNotConnectedError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Google Calendar connected.",
        )
    except EventNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found.",
        )
    except CalendarAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
