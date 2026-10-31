# Backend
FastAPI service. Run with Docker Compose from the repository root. API documentation is available at `/docs`.

Only verified peptide records are returned by public read endpoints. Add managed authentication, curator authorization, rate limiting and audit logging before introducing write operations. Development startup applies the initial SQL schema for convenience; production should use reviewed, versioned migrations executed as a deployment job.
