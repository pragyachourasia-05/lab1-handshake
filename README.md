# Lab 1 - Handshake Prototype

Pair 23 backend foundation and student vertical.

## Pair configuration

```text
PAIR=23
PORT_BASE=9230
SEED=23
CITY_SET=San Francisco, Oakland, San Jose
DATABASE_PREFIX=p23
```

## Included in this package

- Shared configuration, MySQL database session, SQLAlchemy models, Pydantic schemas, bcrypt password hashing, and JWT authentication.
- Student signup/login/logout and profile APIs.
- Student job search and job-detail APIs.
- Student PDF resume upload and job application APIs.
- Student application history with Pending, Reviewed, and Declined filters.
- Student event browsing, event details, eligibility checks, and registration.
- Student directory search by name, college, and major.

Company business routes, seed generation, the React UI, and the Part B assistant will be added with the lab partner.

## Run

1. Copy `.env.example` to `.env` and set the MySQL password.
2. Create the MySQL database named `p23_handshake`.
3. Activate the virtual environment and run `pip install -r requirements.txt`.
4. Start with `uvicorn backend.app.main:app --reload --port 9230`.
5. Open `http://127.0.0.1:9230/docs`.
