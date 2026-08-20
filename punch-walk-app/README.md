# NTXP Field Punch Walk

A mobile-first, dependency-free web prototype for performing construction punch walks over an uploaded drawing. It uses browser GPS, device orientation, microphone, camera/file capture, printable reporting, review statuses, and touch signature APIs.

Run locally from the repository root:

```bash
python -m http.server 8000 --directory punch-walk-app
```

Then open `http://localhost:8000`. Sensor and media permissions require HTTPS outside localhost. Data is kept in memory for this front-end prototype; sending email requires connection to an approved mail service in production.
