--
-- PostgreSQL Create Hosting Expense tables for Optimization Metabase Instance
-- Dumped from OCP3 Postgres DB 2021-01-05 CC
--

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

--
-- Name: hostingexpenses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hostingexpenses (
    ownerparty text,
    sdaparty text,
    servicename text,
    fundingmodelcolour text,
    expenseglaccount text,
    reportingcustomer text,
    reportingcustomerno text,
    servicelevel1 text,
    inventoryitemnumber text,
    instancenumber text,
    servicelevel2 text,
    omassettag text,
    ordernumber text,
    quantity numeric(12,3),
    price numeric(12,3),
    expenseamount numeric(12,3),
    recoveryfrequency text,
    recoverystartdate timestamp without time zone,
    recoveryenddate timestamp without time zone,
	recoverytype text,
    recoveryperiod timestamp without time zone,
    comments text,
    glperiod text,
    category text,
    rawdate text
);


ALTER TABLE public.hostingexpenses OWNER TO postgres;

--
-- PostgreSQL Hosting Expense table creation complete
--
