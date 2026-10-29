from rest_framework.permissions import AllowAny

# Public, read-only for the MVP (open question 5). Swap for IsAuthenticated or a custom
# permission when access control lands (E10).
PERMISSION = [AllowAny]
