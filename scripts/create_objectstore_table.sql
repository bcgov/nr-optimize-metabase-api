SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_with_oids = false;

CREATE TABLE public.objectstorage (
    bucket text,
    owner text,
    objectcount numeric(12),
    newobjects numeric(12),
    deletedobjects numeric(12),
    size numeric(12,3),
    uploadsize numeric(12,3),
    downloadsize numeric(12,3),
    quota_percent numeric(4,3),
    quota numeric(12),
    ministry text,
    branch text,
    project text,
    environment text,
    reportdate timestamp without time zone
);

COMMENT ON TABLE public.objectstorage IS 'This table is populated with Object Storage metrics from a monthly report provided by OCIO, taken within hours of billing.';
COMMENT ON COLUMN public.objectstorage.bucket IS 'The bucket name in Object Storage';
COMMENT ON COLUMN public.objectstorage.owner IS 'The user name in Object Storage';
COMMENT ON COLUMN public.objectstorage.objectcount IS 'The number of objects in the bucket';
COMMENT ON COLUMN public.objectstorage.newobjects IS 'The number of objects created this period';
COMMENT ON COLUMN public.objectstorage.deletedobjects IS 'The number of objects deleted this period';
COMMENT ON COLUMN public.objectstorage.size IS 'The size of the data in the bucket in GB';
COMMENT ON COLUMN public.objectstorage.uploadsize IS 'The size of the data uploaded to Object Storage in GB';
COMMENT ON COLUMN public.objectstorage.downloadsize IS 'The size of the data downloaded to Object Storage in GB';
COMMENT ON COLUMN public.objectstorage.quota IS 'The block-access quota set on the bucket in GB';
COMMENT ON COLUMN public.objectstorage.ministry IS 'The name of the ministry which owns the bucket, based on bucket tagging';
COMMENT ON COLUMN public.objectstorage.branch IS 'The name of the branch which owns the bucket, based on bucket tagging';
COMMENT ON COLUMN public.objectstorage.project IS 'The name of the project which owns the bucket, based on bucket tagging';
COMMENT ON COLUMN public.objectstorage.environment IS 'The environment for the bucket, determined either by owner name or bucket tagging';
COMMENT ON COLUMN public.objectstorage.reportdate IS 'The 1st of the month that the report was sampled by OCIO.';

ALTER TABLE public.objectstorage OWNER TO postgres;