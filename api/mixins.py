from rest_framework.exceptions import NotFound
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Workout


class WorkoutAccessMixin:
    """
    Provides workout ownership check for views.
    Return 404 if workout doesn't exist or belongs to another user to prevent information leakage.
    """
    lookup_url_kwarg_workout = "workout_id"
    def get_workout(self):
        workout_id = self.kwargs.get(self.lookup_url_kwarg_workout)
        try:
            workout = Workout.objects.get(pk=workout_id)
        except Workout.DoesNotExist:
            raise NotFound("Workout not found")
        if workout.owner != self.request.user:
            raise NotFound("Workout not found")
        return workout

class JWTAuthMixin:
    """
    Authenticate a user via JWT and set the auth header for the client.
    """
    def authenticate(self, user):
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")