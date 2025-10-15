from django.urls import path

from . import views

urlpatterns = [
    path('workouts/', views.WorkoutListCreateAPIView.as_view(), name="workouts"),
    path('workouts/<int:workout_id>/', views.WorkoutDestroyAPIView.as_view(), name="workout-delete"),
    path('workouts/<int:workout_id>/exercises/', views.ExerciseListCreateAPIView.as_view(), name="exercises"),
    path('workouts/<int:workout_id>/exercises/<int:exercise_id>/', views.ExerciseRetrieveUpdateDestroyAPIView.as_view(), name="exercise-detail"),
    path('protein/', views.ProteinRetrieveUpdateAPIView.as_view(), name="protein"),

]