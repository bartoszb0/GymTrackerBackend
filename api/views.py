from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated

from .mixins import WorkoutAccessMixin
from .models import Exercise, User, Workout
from .serializers import (ExerciseSerializer, ProteinSerializer,
                          UserSerializer, WorkoutSerializer)


class CreateUserAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class WorkoutListCreateAPIView(generics.ListCreateAPIView):
    """
    List all workouts assigned to user that makes request.
    Allow creation of new workout.
    """
    serializer_class = WorkoutSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Workout.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class WorkoutDestroyAPIView(generics.DestroyAPIView):
    """
    Allow user to delete workout created by him.
    """
    serializer_class = WorkoutSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'workout_id'

    def get_queryset(self):
        return Workout.objects.filter(owner=self.request.user)


class ExerciseListCreateAPIView(WorkoutAccessMixin, generics.ListCreateAPIView):
    """
    List all exercises for a given workout (owned by the user)
    and allow creation of new exercises for that workout.
    """
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Exercise.objects.filter(workout=self.get_workout())
    
    def perform_create(self, serializer):
        serializer.save(workout=self.get_workout())


class ExerciseRetrieveUpdateDestroyAPIView(WorkoutAccessMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Allow user to update weight associated with exercise made by him and
    delete the exercise.
    """
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'exercise_id'
    http_method_names = ['patch', 'delete']
    
    def get_queryset(self):
        return Exercise.objects.filter(workout=self.get_workout())
    

class ProteinRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the user's protein data.
    - GET: Returns current protein stats (resets daily counter if needed).
    - PATCH: Allows updating the daily goal or adding protein intake.
    """
    serializer_class = ProteinSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch']

    def get_object(self):
        """
        Returns the current user and ensures today's protein counter is reset
        if the last update was not today.
        """
        user = self.request.user
        user.reset_todays_protein()
        return user
    
    def partial_update(self, request, *args, **kwargs):
        """
        Partially updates the user's protein data.

        - Adds a value from 'protein_to_add' if provided and valid.
        - Updates the user's protein goal or today's protein via the standard serializer update.
        """
        kwargs['partial'] = True
        protein_to_add = request.data.get('protein_to_add') 
        if protein_to_add is not None:
            try:
                protein_to_add = int(protein_to_add)
            except (ValueError, TypeError):
                raise ValidationError("Protein amount must be a valid number.")

            self.get_object().add_protein(protein_to_add)

        return self.update(request, *args, **kwargs)

