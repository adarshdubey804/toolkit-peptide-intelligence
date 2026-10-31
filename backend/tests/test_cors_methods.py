from fastapi.middleware.cors import CORSMiddleware
from app.main import app


def test_cors_allows_patch_for_frontend_workflows():
    cors = next(item for item in app.user_middleware if item.cls is CORSMiddleware)
    assert "PATCH" in cors.kwargs["allow_methods"]
