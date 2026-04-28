# Coding Rules

## 1. Section Headers

Use `# --- Section Name ---` with single dashes.

```python
# --- Custom Exception Classes ---

class NotFoundException(AppException):
    ...


# --- Exception Handlers ---

async def app_exception_handler(...):
    ...
```

## 2. Dependency Injection

Use `Annotated` for dependency type aliases (Python 3.9+):

```python
from typing import Annotated

from fastapi import Depends

# Good
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

# Avoid
AuthServiceDep = Depends(get_auth_service)
```

## 3. Route Readability

- One parameter per line with trailing comma
- Include a short docstring on every route
- Raise exceptions at the end of validation block

```python
@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    response: Response,
    auth_service: AuthServiceDep,
):
    """Authenticate with email and password."""
    token = await auth_service.login(
        email=request.email,
        password=request.password,
    )

    if not token:
        raise UnauthorizedException("Invalid email or password")

    return handle_auth_result(response, token)
```

## 4. Service Constructor Readability

One argument per line:

```python
return AuthService(
    auth_repo=auth_repo,
    session_manager=session_manager,
)
```

## 5. Dicts and Data Structuring

Multi-line with trailing comma:

```python
user_payload = {
    "id": user_id,
    "email": data["email"],
    "password_hash": password_hash,
}
```
