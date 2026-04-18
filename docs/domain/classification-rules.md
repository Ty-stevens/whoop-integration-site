# Classification Rules

Imported workouts are classified into simple buckets for goals and reports. Unknown values are expected and are not bugs.

## Buckets

- `cardio`: endurance-focused sessions.
- `strength`: resistance or strength-focused sessions.
- `other`: known activities that should not count as cardio or strength targets.
- `unknown`: missing, ambiguous, or unsupported sport names.

## Cardio Examples

- running
- cycling
- rowing
- swimming
- hiking
- walking
- elliptical
- stair climber
- treadmill
- trail running
- indoor cycling

## Strength Examples

- weightlifting
- functional fitness
- strength trainer
- resistance training
- pilates
- calisthenics

## Rules

- Ambiguous sports stay `unknown` until reviewed.
- Manual annotations may override classification for display and reporting where allowed.
- Imported WHOOP records remain canonical facts; overrides are overlays.

