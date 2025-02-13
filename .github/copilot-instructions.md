# Copilot Instructions

## Suggestions

- for SQLAlchemy use modern style select statements
  - example: `session.scalars(select(Report).where(Report.id == 1)).all()`
  - example: `session.scalar(select(ReportParticipant).where(ReportParticipant.report_id == 1))`

## Testing

- use pytest
- structure the test code with classes and functions
- test for expected failure conditions

## Suggestions

- add docstrings to functions
- offer two alternative solutions
- give detailed explanations on both solutions and their advantages/disadvantages
