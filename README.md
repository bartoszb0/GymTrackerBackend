
# GymTracker - Tool for tracking gym progress
[![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)](https://gymtracker-coverage.onrender.com/)


This mobile-friendly app is designed to help users manage and track their fitness progress on the go. Users can create workouts, including exercises, sets, reps, and weights used. The app provides a “Workout Mode,” allowing users to move through each exercise set by set and update their current weights. Additionally, the app includes a daily protein tracking feature, enabling users to record their intake and monitor progress toward personalized protein goals. 

[Frontend Repository](https://github.com/bartoszb0/GymTrackerFrontend)

> Author: Bartosz Bednarczyk  
>  Email: bartoszb2020@gmail.com

https://github.com/user-attachments/assets/2353bd35-9aae-4fe4-9b6f-c6df9a428902

## Demo

https://gymtracker-7lua.onrender.com/


## Key Application Features

* **Workouts and Exercises:** Users can create custom workouts and attach exercises to them, storing their workout plan in one place.

* **Workout Mode:** When Workout Mode is activated users go through each exercise, set by set. At the end of each exercise user has option to update weight accordingly to their progress (if any was made).

* **Workout Continuity:** Since GymTracker is designed to be actively used during your workout, the application ensures users **never lose their place**. Even after a page refresh or navigating away (common when putting a phone down during sets), the user is instantly prompted to **"Continue Workout"** exactly where they left off, providing a seamless and reliable experience.

* **Protein tracker:** Users can set their own daily protein goal and add current protein intake. Today's protein intake resets everyday.


> Use Case:
> 1. User creates a new workout.
> 2. Adds exercises to the workout.
> 3. Starts **Workout Mode** at the gym.
> 4. Tracks each set and updates weights as needed.
> 5. If the page reloads, **Workout Continuity** allows the user to resume exactly where they left off.

## Technologies used

### Backend
- **Python**
- **Django:** backend web framework
- **Django REST Framework:** for building RESTful APIs
- **SQLite** (local) / **PostgreSQL** (production on Render): database management
- **JWT Authentication:** secure token-based user authentication
- **Coverage.py:** for test coverage (**99%**)

### Frontend
- **React (Vite):** core library for building the user interface
- **React Router:** for declarative routing within the single-page application
- **Axios:** API communication
- **Prettier:** code formatting and consistency

### Deployment
- **Render:** hosting for frontend, backend and database
## Endpoints

| Endpoint | Method| Request | Response | Function|
| :------- | :---- | :------ | :------- | :------ | 
| /api/user/register | POST | Username, password | User id, username | Register user |
| /api/token | POST | Username, password | Token | Give user a token |
| /workouts | GET | Token | Workouts | List user's workouts  |
| /workouts | POST | Token | Workout | Create new workout |
| /workouts/{workout_id} | DELETE | Token | None | Delete workout
| /workouts/{workout_id}/exercises | GET | Token | Exercises | List workout exercises
| /workouts/{workout_id}/exercises | POST | Token | Exercise | Create new exercise
| /workouts/{workout_id}/exercises/{exercise_id} | PATCH | Token | Exercise | Update exercise's weight 
| /workouts/{workout_id}/exercises/{exercise_id} | DELETE | Token | None | Delete exercise
| /protein | GET | Token | Protein | Give user his protein data / Reset today's protein
| /protein | PATCH | Token | Protein | Update protein data |

## Tests

The backend is tested using Django's test framework.  
Current test coverage: **99%**.  
[**Coverage report**](https://gymtracker-coverage.onrender.com/)

### How to run tests?

Ensure you are in the project's root directory and have your virtual environment activated.

```
pip install -r requirements.txt
coverage run manage.py test
coverage report
```
## How to run backend locally

1. Clone the repository  
`git clone https://github.com/bartoszb0/GymTrackerBackend.git`  
`cd GymTrackerBackend`

2. Run this in terminal  
`python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- This will print a new random SECRET_KEY string, copy it.

3. Make .env file and paste SECRET_KEY
```
# .env
SECRET_KEY = paste_here
```

4. Create and activate virtual environment  
`python -m venv venv`  
`venv\Scripts\activate`

5. Install requirements  
`pip install -r requirements.txt`

6. Run migrations  
`python manage.py migrate`

7. Run server  
`python manage.py runserver`

## Screenshots

<img width="282" height="609" alt="login" src="https://github.com/user-attachments/assets/76ec240a-c00d-46da-940d-0a40b2ea1713" />
<img width="282" height="609" alt="homescreen" src="https://github.com/user-attachments/assets/e0b8d491-7b24-4d02-9c48-ff6e12e7c5c6" />
<img width="282" height="609" alt="new-workout-form" src="https://github.com/user-attachments/assets/9243e9b6-5391-40e1-8f58-5df4f9fd0f4a" />
<img width="282" height="609" alt="workout-view" src="https://github.com/user-attachments/assets/3ebb737f-6c43-4a75-88b7-698b93ee47af" />
<img width="282" height="609" alt="new-exercise-form" src="https://github.com/user-attachments/assets/b56c3cb3-67b4-47b9-946f-4e03be427fa4" />
<img width="282" height="609" alt="workout-mode" src="https://github.com/user-attachments/assets/54a27acc-df65-4160-9421-03a273af2c39" />
<img width="282" height="609" alt="setting-new-weight" src="https://github.com/user-attachments/assets/d5828695-b933-4c8b-a989-cbdf5e2c2378" />
<img width="282" height="609" alt="protein" src="https://github.com/user-attachments/assets/35e644cf-1264-4826-a20d-4d7430d86782" />
