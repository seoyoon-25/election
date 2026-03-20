"""
API v1 Router

Combines all v1 API routes into a single router.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.members import router as members_router
from app.api.v1.boards import router as boards_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.calendar import router as calendar_router
from app.api.v1.invitations import router as invitations_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth_router)
api_router.include_router(campaigns_router)
api_router.include_router(members_router)
api_router.include_router(boards_router)
api_router.include_router(tasks_router)
api_router.include_router(approvals_router)
api_router.include_router(calendar_router)
api_router.include_router(invitations_router)


# API info endpoint
@api_router.get("/", tags=["API Info"])
async def api_info():
    """Get API information and available endpoints."""
    return {
        "version": "v1",
        "endpoints": {
            "auth": {
                "register": "POST /auth/register",
                "login": "POST /auth/login",
                "logout": "POST /auth/logout",
                "refresh": "POST /auth/refresh",
                "me": "GET /auth/me",
                "update_me": "PATCH /auth/me",
                "change_password": "POST /auth/password/change",
                "reset_request": "POST /auth/password/reset-request",
                "reset_confirm": "POST /auth/password/reset-confirm",
            },
            "campaigns": {
                "create": "POST /campaigns",
                "list": "GET /campaigns",
                "get": "GET /campaigns/{id}",
                "update": "PATCH /campaigns/{id}",
                "delete": "DELETE /campaigns/{id}",
                "activate": "POST /campaigns/{id}/activate",
                "archive": "POST /campaigns/{id}/archive",
            },
            "members": {
                "list": "GET /members",
                "me": "GET /members/me",
                "get": "GET /members/{id}",
                "update": "PATCH /members/{id}",
                "remove": "DELETE /members/{id}",
                "invite": "POST /members/invite",
            },
            "boards": {
                "list": "GET /boards",
                "create": "POST /boards",
                "get": "GET /boards/{id}",
                "update": "PATCH /boards/{id}",
                "delete": "DELETE /boards/{id}",
                "stats": "GET /boards/{id}/stats",
                "columns": {
                    "list": "GET /boards/{id}/columns",
                    "create": "POST /boards/{id}/columns",
                    "update": "PATCH /boards/{id}/columns/{column_id}",
                    "delete": "DELETE /boards/{id}/columns/{column_id}",
                    "reorder": "PUT /boards/{id}/columns/reorder",
                },
            },
            "tasks": {
                "list": "GET /tasks",
                "create": "POST /tasks?board_id={board_id}",
                "get": "GET /tasks/{id}",
                "update": "PATCH /tasks/{id}",
                "delete": "DELETE /tasks/{id}",
                "move": "POST /tasks/{id}/move",
                "reorder": "PUT /tasks/reorder?column_id={column_id}",
                "assignees": {
                    "list": "GET /tasks/{id}/assignees",
                    "add": "POST /tasks/{id}/assignees",
                    "remove": "DELETE /tasks/{id}/assignees/{member_id}",
                },
                "comments": {
                    "list": "GET /tasks/{id}/comments",
                    "add": "POST /tasks/{id}/comments",
                    "update": "PATCH /tasks/{id}/comments/{comment_id}",
                    "delete": "DELETE /tasks/{id}/comments/{comment_id}",
                },
                "history": "GET /tasks/{id}/history",
            },
            "approvals": {
                "workflows": {
                    "list": "GET /approvals/workflows",
                    "create": "POST /approvals/workflows",
                    "get": "GET /approvals/workflows/{id}",
                    "update": "PATCH /approvals/workflows/{id}",
                    "delete": "DELETE /approvals/workflows/{id}",
                    "steps": {
                        "add": "POST /approvals/workflows/{id}/steps",
                        "update": "PATCH /approvals/workflows/{id}/steps/{step_id}",
                        "delete": "DELETE /approvals/workflows/{id}/steps/{step_id}",
                        "reorder": "PUT /approvals/workflows/{id}/steps/reorder",
                    },
                },
                "requests": {
                    "list": "GET /approvals/requests",
                    "create": "POST /approvals/requests",
                    "get": "GET /approvals/requests/{id}",
                    "pending": "GET /approvals/requests/pending",
                    "decide": "POST /approvals/requests/{id}/decide",
                    "cancel": "POST /approvals/requests/{id}/cancel",
                },
            },
            "calendar": {
                "note": "All calendar endpoints are nested under /campaigns/{campaign_id}/calendar",
                "oauth": {
                    "connect": "GET /campaigns/{id}/calendar/connect",
                    "callback": "GET /campaigns/{id}/calendar/callback",
                    "disconnect": "DELETE /campaigns/{id}/calendar/disconnect",
                    "status": "GET /campaigns/{id}/calendar/status",
                },
                "events": {
                    "list": "GET /campaigns/{id}/calendar/events",
                    "create": "POST /campaigns/{id}/calendar/events",
                    "get": "GET /campaigns/{id}/calendar/events/{event_id}",
                    "update": "PATCH /campaigns/{id}/calendar/events/{event_id}",
                    "delete": "DELETE /campaigns/{id}/calendar/events/{event_id}",
                },
            },
        },
        "authentication": {
            "type": "Bearer",
            "header": "Authorization: Bearer <access_token>",
            "campaign_header": "X-Campaign-ID: <campaign_id>",
        },
    }
