from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.hashers import is_password_usable
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .mixins import JWTAuthMixin
from .models import Exercise, User, Workout


class CreateUserAPITestCase(APITestCase):
    def setUp(self):
        self.existing_user = User.objects.create_user(username="user", password="userpass")

        self.url = reverse('register')
    
    def test_too_short_password(self):
        """ Password shorter than 6 character gets rejected """
        response = self.client.post(self.url, {
            "username": "new_user",
            "password": "short"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  
        self.assertFalse(User.objects.filter(username="new_user").exists())

    def test_too_common_password(self):
        response = self.client.post(self.url, {
            "username": "new_user",
            "password": "password"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="new_user").exists())

    def test_entirely_numeric_password(self):
        """ Validate that the password is not entirely numeric """
        response = self.client.post(self.url, {
            "username": "new_user",
            "password": "123456"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="new_user").exists())

    def test_password_too_similiar_to_username(self):
        response = self.client.post(self.url, {
            "username": "new_user",
            "password": "new_user"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="new_user").exists())

    def test_username_already_taken(self):
        """ Creating account with username already taken is rejected """
        response = self.client.post(self.url, {
            "username": self.existing_user.username,
            "password": "StrongPass123!"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="new_user").exists())

    def test_username_is_case_insensitive(self):
        """ Usernames are treated case insensitive """
        response = self.client.post(self.url, {
            "username": self.existing_user.username.upper(),
            "password": "StrongPass123!"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="new_user").exists())

    def test_missing_username(self):
        user_count_before = User.objects.count()
        response = self.client.post(self.url, {
            "password": "StrongPass123!"
        })
        user_count_after = User.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(user_count_before, user_count_after)

    def test_missing_password(self):
        response = self.client.post(self.url, {
            "username": "new_user"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="new_user").exists())

    def test_correct_user_credentials_create_user(self):
        response = self.client.post(self.url, {
            "username": "new_user",
            "password": "StrongPass123!"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="new_user").exists())
    
    def test_password_is_not_returned_in_response(self):
        """ Password is not returned in response when creating new user """
        response = self.client.post(self.url, {
            "username": "new_user",
            "password": "StrongPass123!"
        })
        self.assertNotIn('password', response.data)

    def test_password_is_hashed_on_creation(self):
        """ Password is hashed on creation and stored in database as hashed """
        self.client.post(self.url, {
            "username": "new_user",
            "password": "StrongPass123!"
        })
        user = User.objects.get(username="new_user")
        self.assertTrue(is_password_usable(user.password))
        self.assertNotEqual(user.password, "StrongPass123!")


class WorkoutListCreateAPITestCase(JWTAuthMixin, APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='userpass')
        self.user2 = User.objects.create_user(username='user2', password='userpass')

        self.workout_user1 = Workout.objects.create(owner=self.user1, name="workout1")
        self.workout_user2 = Workout.objects.create(owner=self.user2, name="workout2")

        self.new_workout = {
            "name": "New workout"
        }

        self.url = reverse('workouts')

    """ GET """
    def test_unauthorized_user_cant_access_workout_list(self):
        """Anonymous user should receive 401 trying to receive workout."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_with_no_workouts_gets_empty_list(self):
        self.authenticate(self.user1)
        Workout.objects.filter(owner=self.user1).delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_each_user_gets_only_his_workouts(self):
        """Each user gets to see only workout assigned to him."""
        for user in [self.user1, self.user2]:
            self.authenticate(user)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            for workout in response.data:
                self.assertEqual(workout['owner'], user.pk)

    """ POST """
    def test_unauthorized_user_cant_create_workout(self):
        """Anonymous user should receive 401 trying to create workout."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authorized_user_can_create_workout(self):
        """Authorized user can create workout and its automatically assigned to him."""
        self.authenticate(self.user1)
        response = self.client.post(self.url, self.new_workout)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], self.new_workout['name'])
        self.assertEqual(Workout.objects.get(pk=response.data['id']).owner, self.user1)

    def test_validate_workout_name_length(self):
        """Workout name cant be longer than 30 characters."""
        self.authenticate(self.user1)
        response = self.client.post(self.url, {
            "name": "Workout_Name_Longer_Than_30_Characters"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Workout.objects.filter(name="Workout_Name_Longer_Than_30_Characters").exists())

    def test_validate_empty_workout_name(self):
        workout_count_before = Workout.objects.count()
        self.authenticate(self.user1)
        response = self.client.post(self.url, {"name": ""})
        workout_count_after = Workout.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(workout_count_before, workout_count_after)

class WorkoutDestroyAPITestCase(JWTAuthMixin, APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='userpass')
        self.user2 = User.objects.create_user(username='user2', password='userpass')

        self.workout_user1 = Workout.objects.create(owner=self.user1, name="workout1")
        self.workout_user2 = Workout.objects.create(owner=self.user2, name="workout2")

    def getUrl(self, workout_id):
        return reverse('workout-delete', kwargs={'workout_id': workout_id})


    def test_anonymous_user_cant_delete_workout(self):
        """ Anonymous user gets 401 trying to delete any workout """
        workout = Workout.objects.first()
        response = self.client.delete(self.getUrl(workout.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Workout.objects.filter(pk=workout.pk).exists())

    def test_user_can_delete_his_workout(self):
        """ User can delete workout created by him """
        user = self.user1
        self.authenticate(user)
        workout = Workout.objects.get(owner=user)
        response = self.client.delete(self.getUrl(workout.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Workout.objects.filter(pk=workout.pk).exists())

    def test_user_cant_delete_others_workout(self):
        """ User gets 404 trying to delete workout not assigned to him """
        user = self.user1
        workout = self.workout_user2
        self.authenticate(user)
        response = self.client.delete(self.getUrl(workout.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Workout.objects.filter(pk=workout.pk).exists())


class ExerciseListCreateAPITestCase(JWTAuthMixin, APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='userpass')
        self.user2 = User.objects.create_user(username='user2', password='userpass')

        self.workout1 = Workout.objects.create(owner=self.user1, name='workout1')
        self.workout2 = Workout.objects.create(owner=self.user2, name='workout2')

        self.workout1_exercise1 = Exercise.objects.create(
            name="workout1_exercise1",
            sets=1,
            reps=5,
            weight=5,
            workout=self.workout1
        )

        self.workout1_exercise2 = Exercise.objects.create(
            name="workout1_exercise2",
            sets=1,
            reps=3,
            weight=15,
            workout=self.workout1
        )

        self.workout2_exercise1 = Exercise.objects.create(
            name="workout2_exercise1",
            sets=5,
            reps=10,
            weight=7,
            workout=self.workout2
        )

        self.workout2_exercise2 = Exercise.objects.create(
            name="workout2_exercise2",
            sets=3,
            reps=4,
            weight=5,
            workout=self.workout2
        )

        self.new_exercise = {
            "name": "Test Exercise",
            "sets": 5,
            "reps": 8,
            "weight": 30
        }

    def getUrl(self, workout_id):
        return reverse('exercises', kwargs={'workout_id': workout_id})
    
    """ GET """
    def test_anonymous_user_cannot_list_exercises(self):
        response = self.client.get(self.getUrl(self.workout1.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cant_see_others_exercises(self):
        """ User gets 404 trying to list exercises assigned to workout that is not his """
        self.authenticate(self.user1)
        response = self.client.get(self.getUrl(self.workout2.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_see_his_exercises(self):
        """ User gets back only list of exercises that are assigned to workout that is his """
        self.authenticate(self.user1)
        response = self.client.get(self.getUrl(self.workout1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for exercise in response.data:
            self.assertEqual(Exercise.objects.get(pk=exercise['id']).workout, self.workout1)

    def test_list_returns_empty_if_no_exercises(self):
        """ When a workout has no exercises, an empty list is returned """
        self.authenticate(self.user1)
        Exercise.objects.filter(workout=self.workout1).delete()
        response = self.client.get(self.getUrl(self.workout1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    """ POST """
    def test_anonymous_user_cant_create_exercise(self):
        exercise_count_before = Exercise.objects.count()
        response = self.client.post(self.getUrl(self.workout1.pk), self.new_exercise)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(exercise_count_before, exercise_count_after)

    def test_user_can_create_exercise(self):
        """ User can create exercise in workout that is assigned to him """
        self.authenticate(self.user1)
        response = self.client.post(self.getUrl(self.workout1.pk), self.new_exercise)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Exercise.objects.filter(pk=response.data['id']).exists())

    def test_exercise_gets_assigned_to_workout(self):
        """ When user creates an exercise succesfully it gets assigned to workout """
        self.authenticate(self.user1)
        response = self.client.post(self.getUrl(self.workout1.pk), self.new_exercise)
        self.assertEqual(Exercise.objects.get(pk=response.data['id']).workout, self.workout1)

    def test_user_cannot_create_exercise_for_others_workout(self):
        """ User gets 404 trying to create exercise for workout that is not assigned to him """
        exercise_count_before = Exercise.objects.count()
        self.authenticate(self.user1)
        response = self.client.post(self.getUrl(self.workout2.pk), self.new_exercise)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(exercise_count_before, exercise_count_after)
    
    """ EXERCISE POST VALIDATION """
    def test_name_longer_than_30_characters_returns_400(self):
        exercise_count_before = Exercise.objects.count()
        data = {**self.new_exercise, "name": "Name_Longer_Than_30_Characters_"}
        self.authenticate(self.user1)
        response = self.client.post(self.getUrl(self.workout1.pk), data)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exercise_count_before, exercise_count_after)

    def test_missing_name_returns_400(self):
        exercise_count_before = Exercise.objects.count()
        self.new_exercise.pop('name')
        self.authenticate(self.user1)
        response = self.client.post(self.getUrl(self.workout1.pk), self.new_exercise)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exercise_count_before, exercise_count_after)

    def test_missing_sets_returns_400(self):
        exercise_count_before = Exercise.objects.count()
        self.new_exercise.pop('sets')
        self.authenticate(self.user1)
        response = self.client.post(self.getUrl(self.workout1.pk), self.new_exercise)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exercise_count_before, exercise_count_after)

    def test_missing_reps_returns_400(self):
        exercise_count_before = Exercise.objects.count()
        self.new_exercise.pop('reps')
        self.authenticate(self.user1)
        response = self.client.post(self.getUrl(self.workout1.pk), self.new_exercise)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exercise_count_before, exercise_count_after)

    def test_missing_weight_creates_exercise_and_saves_weight_as_0(self):
        self.new_exercise.pop('weight')
        self.authenticate(self.user1)
        response = self.client.post(self.getUrl(self.workout1.pk), self.new_exercise)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Exercise.objects.get(pk=response.data['id']).weight, Decimal('0.00'))

    def test_negative_sets_returns_400(self):
        exercise_count_before = Exercise.objects.count()
        self.authenticate(self.user1)
        data = {**self.new_exercise, "sets": -1}
        response = self.client.post(self.getUrl(self.workout1.pk), data)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exercise_count_before, exercise_count_after)

    def test_non_integer_sets_returns_400(self):
        exercise_count_before = Exercise.objects.count()
        self.authenticate(self.user1)
        data = {**self.new_exercise, "sets": "abc"}
        response = self.client.post(self.getUrl(self.workout1.pk), data)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exercise_count_before, exercise_count_after)

    def test_sets_cannot_be_zero_returns_400(self):
        exercise_count_before = Exercise.objects.count()
        self.authenticate(self.user1)
        data = {**self.new_exercise, "sets": 0}
        response = self.client.post(self.getUrl(self.workout1.pk), data)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exercise_count_before, exercise_count_after)

    def test_negative_reps_returns_400(self):
        exercise_count_before = Exercise.objects.count()
        self.authenticate(self.user1)
        data = {**self.new_exercise, "reps": -1}
        response = self.client.post(self.getUrl(self.workout1.pk), data)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exercise_count_before, exercise_count_after)

    def test_non_integer_reps_returns_400(self):
        exercise_count_before = Exercise.objects.count()
        self.authenticate(self.user1)
        data = {**self.new_exercise, "reps": "abc"}
        response = self.client.post(self.getUrl(self.workout1.pk), data)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exercise_count_before, exercise_count_after)

    def test_reps_cannot_be_zero_returns_400(self):
        exercise_count_before = Exercise.objects.count()
        self.authenticate(self.user1)
        data = {**self.new_exercise, "reps": 0}
        response = self.client.post(self.getUrl(self.workout1.pk), data)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exercise_count_before, exercise_count_after)

    def test_negatve_weight_returns_400(self):
        exercise_count_before = Exercise.objects.count()
        self.authenticate(self.user1)
        data = {**self.new_exercise, "weight": -1}
        response = self.client.post(self.getUrl(self.workout1.pk), data)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exercise_count_before, exercise_count_after)

    def test_non_integer_weight_returns_400(self):
        exercise_count_before = Exercise.objects.count()
        self.authenticate(self.user1)
        data = {**self.new_exercise, "weight": "abc"}
        response = self.client.post(self.getUrl(self.workout1.pk), data)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exercise_count_before, exercise_count_after)

    def test_weight_accepts_zero(self):
        self.authenticate(self.user1)
        data = {**self.new_exercise, "weight": 0}
        response = self.client.post(self.getUrl(self.workout1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Exercise.objects.filter(pk=response.data['id']).exists())

    def test_sets_bigger_than_99_returns_400(self):
        exercise_count_before = Exercise.objects.count()
        self.authenticate(self.user1)
        data = {**self.new_exercise, "sets": 100}
        response = self.client.post(self.getUrl(self.workout1.pk), data)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exercise_count_before, exercise_count_after)

    def test_reps_bigger_than_99_returns_400(self):
        exercise_count_before = Exercise.objects.count()
        self.authenticate(self.user1)
        data = {**self.new_exercise, "reps": 100}
        response = self.client.post(self.getUrl(self.workout1.pk), data)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exercise_count_before, exercise_count_after)

    def test_weight_bigger_than_999_99_returns_400(self):
        exercise_count_before = Exercise.objects.count()
        self.authenticate(self.user1)
        data = {**self.new_exercise, "weight": 1000}
        response = self.client.post(self.getUrl(self.workout1.pk), data)
        exercise_count_after = Exercise.objects.count()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exercise_count_before, exercise_count_after)


class ExerciseRetrieveUpdateDestroyAPITestCase(JWTAuthMixin, APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='userpass')
        self.user2 = User.objects.create_user(username='user2', password='userpass')

        self.workout = Workout.objects.create(owner=self.user1, name='workout1')

        self.exercise = Exercise.objects.create(
            name="exercise1",
            sets=1,
            reps=5,
            weight=5,
            workout=self.workout
        )

        self.new_weight = {"weight": 45}

    def getUrl(self, exercise):
        return reverse('exercise-detail', kwargs={'workout_id': exercise.workout.pk, 'exercise_id': exercise.pk})

    """ DELETE """
    def test_anonymous_user_cant_delete_exercise(self):
        exercise = Exercise.objects.first()
        response = self.client.delete(self.getUrl(exercise))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Exercise.objects.filter(pk=exercise.pk).exists())

    def test_user_can_delete_his_exercise(self):
        self.authenticate(self.user1)
        response = self.client.delete(self.getUrl(self.exercise))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Exercise.objects.filter(pk=self.exercise.pk).exists())

    def test_user_cant_delete_others_exercise(self):
        """ User gets 404 trying to delete exercise that is not assigned to his workout """
        self.authenticate(self.user2)
        response = self.client.delete(self.getUrl(self.exercise))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Exercise.objects.filter(pk=self.exercise.pk).exists())

    """ PATCH """
    def test_anonymous_user_cant_update_exercise(self):
        exercise = Exercise.objects.first()
        old_weight = exercise.weight
        response = self.client.patch(self.getUrl(exercise), self.new_weight)
        new_weight = exercise.weight
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(old_weight, new_weight)

    def test_user_can_update_his_exercise(self):
        self.authenticate(self.user1)
        response = self.client.patch(self.getUrl(self.exercise), self.new_weight)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.exercise.refresh_from_db()
        self.assertEqual(self.exercise.weight, Decimal(self.new_weight['weight']))

    def test_user_cant_update_others_exercise(self): 
        self.authenticate(self.user2)
        response = self.client.patch(self.getUrl(self.exercise), self.new_weight)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.exercise.refresh_from_db()
        self.assertNotEqual(self.exercise.weight, Decimal(self.new_weight['weight']))

    def test_user_cant_update_name(self):
        new_name = "New Name"
        self.authenticate(self.user1)
        response = self.client.patch(self.getUrl(self.exercise), {"name": new_name})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.exercise.refresh_from_db()
        self.assertNotEqual(self.exercise.name, new_name)

    def test_user_cant_update_sets(self):
        new_sets = 10
        self.authenticate(self.user1)
        response = self.client.patch(self.getUrl(self.exercise), {"sets": new_sets})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.exercise.refresh_from_db()
        self.assertNotEqual(self.exercise.sets, new_sets)

    def test_user_cant_update_reps(self):
        new_reps = 3
        self.authenticate(self.user1)
        response = self.client.patch(self.getUrl(self.exercise), {"reps": new_reps})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.exercise.refresh_from_db()
        self.assertEqual(self.exercise.reps, new_reps)


    """ EXERCISE PATCH VALIDATION """
    def test_negative_weight_update_returns_400(self):
        new_weight = -1
        self.authenticate(self.user1)
        response = self.client.patch(self.getUrl(self.exercise), {"weight": new_weight})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.exercise.refresh_from_db()
        self.assertNotEqual(self.exercise.weight, new_weight)

    def test_non_integer_weight_update_returns_400(self):
        new_weight = "abc"
        self.authenticate(self.user1)
        response = self.client.patch(self.getUrl(self.exercise), {"weight": new_weight})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.exercise.refresh_from_db()
        self.assertNotEqual(self.exercise.weight, new_weight)

    def test_weight_bigger_than_999_99_returns_400(self):
        new_weight = 1000
        self.authenticate(self.user1)
        response = self.client.patch(self.getUrl(self.exercise), {"weight": new_weight})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.exercise.refresh_from_db()
        self.assertNotEqual(self.exercise.weight, new_weight)

    def test_0_weight_update_is_accepted(self):
        new_weight = 0
        self.authenticate(self.user1)
        response = self.client.patch(self.getUrl(self.exercise), {"weight": new_weight})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.exercise.refresh_from_db()
        self.assertEqual(self.exercise.weight, new_weight)

    

class ProteinRetrieveUpdateAPITestCase(JWTAuthMixin, APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='userpass')

        self.url = reverse('protein')

    """ GET """
    def test_user_gets_default_protein_info(self):
        """ User gets assigned default protein info when creating account """
        self.authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['protein_goal'], 150)
        self.assertEqual(response.data['todays_protein'], 0)

    def test_anonymous_user_cant_retrieve_protein_info(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_todays_protein_resets_on_new_day(self):
        """ If last protein update wasn't done today, todays protein counter will reset """
        self.user.protein_last_update = date.today() - timedelta(days=1)
        self.user.todays_protein = 50
        self.user.save()
        self.authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.data['todays_protein'], 0)
        self.assertEqual(User.objects.get(pk=self.user.pk).protein_last_update, date.today())

    """ PATCH """
    def test_user_can_change_his_daily_protein_goal(self):
        new_protein_goal = 200
        self.authenticate(self.user)
        response = self.client.patch(self.url, {'protein_goal': new_protein_goal})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['protein_goal'], new_protein_goal)
        self.assertEqual(User.objects.get(pk=self.user.pk).protein_goal, new_protein_goal)

    def test_protein_goal_above_500_is_rejected(self):
        """ Maximum protein goal is set to 500"""
        self.authenticate(self.user)
        response = self.client.patch(self.url, {'protein_goal': 501})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_protein_goal_cannot_be_0(self):
        self.authenticate(self.user)
        response = self.client.patch(self.url, {'protein_goal': 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_protein_goal_is_rejected(self):
        self.authenticate(self.user)
        response = self.client.patch(self.url, {'protein_goal': -50})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_integer_protein_goal_is_rejected(self):
        self.authenticate(self.user)
        response = self.client.patch(self.url, {'protein_goal': "abc"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anonymous_user_cant_update_protein_goal(self):
        response = self.client.patch(self.url, {'protein_goal': 200})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_todays_protein_updates_when_user_submits_protein(self):
        protein_to_add = 30
        current_protein_count = User.objects.get(pk=self.user.pk).todays_protein
        self.authenticate(self.user)
        response = self.client.patch(self.url, {'protein_to_add': protein_to_add})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['todays_protein'], protein_to_add + current_protein_count)
        self.assertEqual(User.objects.get(pk=self.user.pk).todays_protein, protein_to_add + current_protein_count)

    def test_adding_todays_protein_exceeding_max_returns_400(self):
        """ Maximum todays protein count is set to 500 """
        self.user.todays_protein = 0
        self.user.save()
        self.authenticate(self.user)
        response = self.client.patch(self.url, {'protein_to_add': 510})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adding_0_return_400(self):
        self.authenticate(self.user)
        response = self.client.patch(self.url, {'protein_to_add': 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_adding_negative_protein_returns_400(self):
        self.authenticate(self.user)
        response = self.client.patch(self.url, {'protein_to_add': -10})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adding_non_integer_protein_returns_400(self):
        self.authenticate(self.user)
        response = self.client.patch(self.url, {'protein_to_add': 'abc'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_anonymous_user_cant_add_protein(self):
        response = self.client.patch(self.url, {'protein_to_add': 30})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
