GRANT ALL PRIVILEGES ON DATABASE initdatabase TO inituser;
GRANT ALL PRIVILEGES ON SCHEMA public TO inituser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO inituser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO inituser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO inituser;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO inituser;
ALTER SCHEMA public OWNER TO inituser;