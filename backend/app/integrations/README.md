## PubMed / NCBI E-utilities
The read-only /api/v1/research/pubmed endpoint uses ESearch followed by ESummary. Configure NCBI_EMAIL (required by NCBI usage guidance) and optionally NCBI_API_KEY as environment variables. Requests are bounded to 20 records and use a 20-second timeout.

Search results are external discovery records with curation_status=not_reviewed. They are not inserted into the curated scientific database and must not be represented as reviewed evidence until a curator checks the source, context and limitations.

NCBI guidance: https://www.ncbi.nlm.nih.gov/books/NBK25499/
