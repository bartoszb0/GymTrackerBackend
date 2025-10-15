from datetime import date
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from rest_framework.exceptions import ValidationError


class User(AbstractUser):
    protein_goal = models.PositiveIntegerField(default=150, validators=[MinValueValidator(1), MaxValueValidator(500)])
    todays_protein = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(500)])
    protein_last_update = models.DateField(default=date.today)

    def reset_todays_protein(self):
        """
        Resets user's 'todays_protein' count if it hasn't been updated today.

        This ensures that the daily protein count starts at zero each day, 
        maintaining accurate tracking for daily protein intake.
        """
        today = date.today()
        if self.protein_last_update != today:
            self.todays_protein = 0
            self.protein_last_update = today
            self.save(update_fields=['todays_protein', 'protein_last_update'])

    def add_protein(self, protein_to_add):
        """
        Validates incoming new protein intake and adds it to user's 'todays_protein' count.
        """
        if protein_to_add <= 0:
            raise ValidationError("Protein amount must be greater than 0.")
        if self.todays_protein + protein_to_add > 500:
            raise ValidationError("Todays protein cannot be greater than 500.")
        self.todays_protein += protein_to_add
        self.save(update_fields=['todays_protein'])

    def save(self, *args, **kwargs):
        if self.username:
            self.username = self.username.lower()
        super().save(*args, **kwargs)
    

class Workout(models.Model):
    name = models.CharField(max_length=30)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="workouts")

    def __str__(self):
        return self.name
    
    
class Exercise(models.Model):
    name = models.CharField(max_length=30)
    sets = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(99)])
    reps = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(99)])
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00'),
    )
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)

    def __str__(self):
            return self.name