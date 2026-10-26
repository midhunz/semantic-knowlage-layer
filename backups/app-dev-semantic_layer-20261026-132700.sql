--
-- PostgreSQL database dump
--

\restrict MDOE73xUYp739FUH4lGrV1kj0fwqE0MahM4vswAgAK92MVRtjhTuixFOW80TUkj

-- Dumped from database version 16.15 (Debian 16.15-1.pgdg13+2)
-- Dumped by pg_dump version 16.15 (Debian 16.15-1.pgdg13+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: api_key; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_key (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    key_prefix character varying(24) NOT NULL,
    key_hash character varying(64) NOT NULL,
    scopes json NOT NULL,
    allowed_domains json NOT NULL,
    created_by character varying(200),
    created_at timestamp with time zone NOT NULL,
    expires_at timestamp with time zone,
    last_used_at timestamp with time zone,
    use_count integer NOT NULL,
    revoked_at timestamp with time zone
);


--
-- Name: api_key_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.api_key_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: api_key_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.api_key_id_seq OWNED BY public.api_key.id;


--
-- Name: app_setting; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_setting (
    key character varying(100) NOT NULL,
    value json NOT NULL
);


--
-- Name: app_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_user (
    id integer NOT NULL,
    email character varying(200) NOT NULL,
    name character varying(200) NOT NULL,
    role character varying(20) NOT NULL,
    password_hash character varying(300) NOT NULL,
    is_active boolean NOT NULL,
    must_change_password boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    last_login_at timestamp with time zone
);


--
-- Name: app_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.app_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: app_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.app_user_id_seq OWNED BY public.app_user.id;


--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_log (
    id integer NOT NULL,
    entity character varying(50) NOT NULL,
    entity_id integer NOT NULL,
    field character varying(100) NOT NULL,
    old_value text,
    new_value text,
    actor character varying(200) NOT NULL,
    at timestamp with time zone NOT NULL,
    staged boolean DEFAULT false NOT NULL
);


--
-- Name: audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_log_id_seq OWNED BY public.audit_log.id;


--
-- Name: column; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."column" (
    id integer NOT NULL,
    table_id integer NOT NULL,
    name character varying(200) NOT NULL,
    data_type character varying(100) NOT NULL,
    nullable boolean NOT NULL,
    ordinal integer NOT NULL,
    removed boolean NOT NULL,
    needs_review boolean NOT NULL,
    display_name character varying(200),
    display_name_ar character varying(200),
    description text,
    description_ar text,
    role character varying(30),
    semantic_type character varying(50),
    unit character varying(50),
    default_aggregation character varying(20),
    non_additive boolean NOT NULL,
    allowed_values json NOT NULL,
    example_values json NOT NULL,
    format character varying(100),
    synonyms json NOT NULL,
    synonyms_ar json NOT NULL,
    allowed_values_ar json NOT NULL,
    is_primary_key boolean NOT NULL,
    pii boolean NOT NULL,
    deprecated boolean NOT NULL,
    quarantined boolean DEFAULT false NOT NULL,
    quarantine_reason character varying(200)
);


--
-- Name: column_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.column_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: column_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.column_id_seq OWNED BY public."column".id;


--
-- Name: dimension; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dimension (
    id integer NOT NULL,
    key character varying(64) NOT NULL,
    label character varying(200),
    label_ar character varying(200),
    description text,
    description_ar text,
    synonyms json NOT NULL,
    synonyms_ar json NOT NULL,
    families json NOT NULL,
    applies_to json NOT NULL,
    applies_note text,
    applies_note_ar text,
    status character varying(20) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


--
-- Name: dimension_binding; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dimension_binding (
    id integer NOT NULL,
    dimension_id integer NOT NULL,
    column_id integer NOT NULL,
    created_at timestamp with time zone NOT NULL
);


--
-- Name: dimension_binding_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dimension_binding_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dimension_binding_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dimension_binding_id_seq OWNED BY public.dimension_binding.id;


--
-- Name: dimension_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dimension_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dimension_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dimension_id_seq OWNED BY public.dimension.id;


--
-- Name: dimension_value; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dimension_value (
    id integer NOT NULL,
    dimension_id integer NOT NULL,
    value character varying(200) NOT NULL,
    label character varying(200),
    label_ar character varying(200),
    aliases json NOT NULL,
    "position" integer NOT NULL
);


--
-- Name: dimension_value_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dimension_value_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dimension_value_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dimension_value_id_seq OWNED BY public.dimension_value.id;


--
-- Name: glossary_term; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.glossary_term (
    id integer NOT NULL,
    term character varying(200) NOT NULL,
    term_ar character varying(200),
    definition text NOT NULL,
    definition_ar text,
    synonyms json NOT NULL,
    synonyms_ar json NOT NULL,
    links json NOT NULL
);


--
-- Name: glossary_term_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.glossary_term_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: glossary_term_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.glossary_term_id_seq OWNED BY public.glossary_term.id;


--
-- Name: login_attempt; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.login_attempt (
    id integer NOT NULL,
    email character varying(200) NOT NULL,
    at timestamp with time zone NOT NULL
);


--
-- Name: login_attempt_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.login_attempt_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: login_attempt_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.login_attempt_id_seq OWNED BY public.login_attempt.id;


--
-- Name: metric; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.metric (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    name_ar character varying(200),
    description text,
    description_ar text,
    sql_expression text NOT NULL,
    base_table_id integer,
    filters text,
    allowed_dimensions json NOT NULL,
    synonyms json NOT NULL,
    synonyms_ar json NOT NULL,
    owner character varying(200),
    status character varying(20) NOT NULL
);


--
-- Name: metric_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.metric_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: metric_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.metric_id_seq OWNED BY public.metric.id;


--
-- Name: profile; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.profile (
    id integer NOT NULL,
    column_id integer NOT NULL,
    null_fraction double precision,
    distinct_count integer,
    min_value character varying(500),
    max_value character varying(500),
    top_values json NOT NULL,
    profiled_at timestamp with time zone NOT NULL
);


--
-- Name: profile_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.profile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: profile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.profile_id_seq OWNED BY public.profile.id;


--
-- Name: relationship; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.relationship (
    id integer NOT NULL,
    from_column_id integer NOT NULL,
    to_column_id integer NOT NULL,
    cardinality character varying(20) NOT NULL,
    join_type character varying(20) NOT NULL,
    description text
);


--
-- Name: relationship_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.relationship_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: relationship_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.relationship_id_seq OWNED BY public.relationship.id;


--
-- Name: sample_query; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sample_query (
    id integer NOT NULL,
    question text NOT NULL,
    sql text NOT NULL,
    tables json NOT NULL,
    verified boolean NOT NULL
);


--
-- Name: sample_query_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sample_query_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sample_query_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sample_query_id_seq OWNED BY public.sample_query.id;


--
-- Name: schema_meta; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_meta (
    id integer NOT NULL,
    source_id integer NOT NULL,
    name character varying(200) NOT NULL,
    display_name character varying(200),
    display_name_ar character varying(200),
    description text,
    description_ar text,
    domain character varying(100),
    owner character varying(200)
);


--
-- Name: schema_meta_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.schema_meta_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: schema_meta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.schema_meta_id_seq OWNED BY public.schema_meta.id;


--
-- Name: source; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.source (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    kind character varying(50) NOT NULL,
    config json NOT NULL,
    last_synced_at timestamp with time zone
);


--
-- Name: source_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.source_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: source_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.source_id_seq OWNED BY public.source.id;


--
-- Name: table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."table" (
    id integer NOT NULL,
    source_id integer NOT NULL,
    schema_name character varying(200) NOT NULL,
    name character varying(200) NOT NULL,
    table_format character varying(50),
    location character varying(1000),
    partitioned_by json NOT NULL,
    row_count integer,
    removed boolean NOT NULL,
    needs_review boolean NOT NULL,
    display_name character varying(200),
    description text,
    grain text,
    table_type character varying(30),
    domain character varying(100),
    owner character varying(200),
    refresh_cadence character varying(100),
    usage_notes text,
    caveats text,
    display_name_ar character varying(200),
    description_ar text,
    grain_ar text,
    usage_notes_ar text,
    caveats_ar text,
    pii_level character varying(30),
    certified boolean NOT NULL,
    status character varying(20) NOT NULL,
    version integer DEFAULT 0 NOT NULL
);


--
-- Name: table_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.table_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: table_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.table_id_seq OWNED BY public."table".id;


--
-- Name: table_revision; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.table_revision (
    id integer NOT NULL,
    table_id integer NOT NULL,
    number integer,
    status character varying(20) NOT NULL,
    changes json NOT NULL,
    diff json NOT NULL,
    snapshot json,
    message text,
    created_by character varying(200) NOT NULL,
    contributors json NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    published_by character varying(200),
    published_at timestamp with time zone
);


--
-- Name: table_revision_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.table_revision_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: table_revision_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.table_revision_id_seq OWNED BY public.table_revision.id;


--
-- Name: user_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_session (
    id integer NOT NULL,
    token_hash character varying(64) NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp with time zone NOT NULL,
    expires_at timestamp with time zone NOT NULL
);


--
-- Name: user_session_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_session_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_session_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_session_id_seq OWNED BY public.user_session.id;


--
-- Name: webhook; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.webhook (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    url character varying(1000) NOT NULL,
    secret character varying(100) NOT NULL,
    events json NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone NOT NULL,
    last_delivery_at timestamp with time zone,
    last_status character varying(200)
);


--
-- Name: webhook_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.webhook_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: webhook_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.webhook_id_seq OWNED BY public.webhook.id;


--
-- Name: api_key id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_key ALTER COLUMN id SET DEFAULT nextval('public.api_key_id_seq'::regclass);


--
-- Name: app_user id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_user ALTER COLUMN id SET DEFAULT nextval('public.app_user_id_seq'::regclass);


--
-- Name: audit_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log ALTER COLUMN id SET DEFAULT nextval('public.audit_log_id_seq'::regclass);


--
-- Name: column id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."column" ALTER COLUMN id SET DEFAULT nextval('public.column_id_seq'::regclass);


--
-- Name: dimension id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dimension ALTER COLUMN id SET DEFAULT nextval('public.dimension_id_seq'::regclass);


--
-- Name: dimension_binding id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dimension_binding ALTER COLUMN id SET DEFAULT nextval('public.dimension_binding_id_seq'::regclass);


--
-- Name: dimension_value id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dimension_value ALTER COLUMN id SET DEFAULT nextval('public.dimension_value_id_seq'::regclass);


--
-- Name: glossary_term id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_term ALTER COLUMN id SET DEFAULT nextval('public.glossary_term_id_seq'::regclass);


--
-- Name: login_attempt id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_attempt ALTER COLUMN id SET DEFAULT nextval('public.login_attempt_id_seq'::regclass);


--
-- Name: metric id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metric ALTER COLUMN id SET DEFAULT nextval('public.metric_id_seq'::regclass);


--
-- Name: profile id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profile ALTER COLUMN id SET DEFAULT nextval('public.profile_id_seq'::regclass);


--
-- Name: relationship id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relationship ALTER COLUMN id SET DEFAULT nextval('public.relationship_id_seq'::regclass);


--
-- Name: sample_query id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sample_query ALTER COLUMN id SET DEFAULT nextval('public.sample_query_id_seq'::regclass);


--
-- Name: schema_meta id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_meta ALTER COLUMN id SET DEFAULT nextval('public.schema_meta_id_seq'::regclass);


--
-- Name: source id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source ALTER COLUMN id SET DEFAULT nextval('public.source_id_seq'::regclass);


--
-- Name: table id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."table" ALTER COLUMN id SET DEFAULT nextval('public.table_id_seq'::regclass);


--
-- Name: table_revision id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_revision ALTER COLUMN id SET DEFAULT nextval('public.table_revision_id_seq'::regclass);


--
-- Name: user_session id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_session ALTER COLUMN id SET DEFAULT nextval('public.user_session_id_seq'::regclass);


--
-- Name: webhook id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.webhook ALTER COLUMN id SET DEFAULT nextval('public.webhook_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
0003_dimensions
\.


--
-- Data for Name: api_key; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.api_key (id, name, description, key_prefix, key_hash, scopes, allowed_domains, created_by, created_at, expires_at, last_used_at, use_count, revoked_at) FROM stdin;
\.


--
-- Data for Name: app_setting; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.app_setting (key, value) FROM stdin;
\.


--
-- Data for Name: app_user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.app_user (id, email, name, role, password_hash, is_active, must_change_password, created_at, last_login_at) FROM stdin;
1000	admin@local.dev		admin	scrypt$2f6dbea89e9a8f812f4dc2a263f578d3$d2a0268081e2734565865966ee873d346563673bedafdfbb126d8537f8877bdb	t	f	2026-10-25 18:14:27.746841+00	2026-10-25 18:19:44.670861+00
1	iris009147@gmail.com		admin	scrypt$279d09f52eedbb3f14afd002553727c2$fc733d945aa2daf94ac722f429ae96467e19baf821f0433a9115a909c8649fae	t	f	2026-10-24 06:58:54.030562+00	2026-10-26 09:26:33.689402+00
\.


--
-- Data for Name: audit_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.audit_log (id, entity, entity_id, field, old_value, new_value, actor, at, staged) FROM stdin;
1	table	1	table_type	\N	fact	iris009147@gmail.com	2026-10-24 08:22:50.138379+00	f
2	table	1	domain	\N	demographics	iris009147@gmail.com	2026-10-24 08:23:10.775129+00	f
3	table	1	certified	false	true	iris009147@gmail.com	2026-10-24 08:23:20.288117+00	f
4	table	1	certified	true	false	iris009147@gmail.com	2026-10-24 08:23:21.418082+00	f
5	table	1	certified	false	true	iris009147@gmail.com	2026-10-24 08:23:22.146949+00	f
6	table	1	certified	true	false	iris009147@gmail.com	2026-10-24 08:23:23.122336+00	f
7	table	1	certified	false	true	iris009147@gmail.com	2026-10-24 08:23:23.856084+00	f
8	table	1	needs_review	true	false	iris009147@gmail.com	2026-10-25 12:15:43.745751+00	f
9	table	1	status	draft	published	iris009147@gmail.com	2026-10-25 12:15:43.748919+00	f
10	column	20	synonyms	[]	["category", "Person category"]	import:population.yaml	2026-10-25 14:06:07.464873+00	t
11	column	22	synonyms	[]	["subcategory", "residency type", "visa type", "citizenship type", "Person subcategory"]	import:population.yaml	2026-10-25 14:06:07.468486+00	t
12	column	3	synonyms	[]	["nationality", "nationalities"]	import:population.yaml	2026-10-25 14:06:07.470334+00	t
13	column	5	synonyms	[]	["gender", "sex"]	import:population.yaml	2026-10-25 14:06:07.471573+00	t
14	column	8	synonyms	[]	["age", "age band", "age bracket", "age range", "age group"]	import:population.yaml	2026-10-25 14:06:07.473507+00	t
15	column	9	synonyms	[]	["emirate", "city", "region"]	import:population.yaml	2026-10-25 14:06:07.475114+00	t
16	column	7	synonyms	[]	["birthplace", "place of birth", "born inside", "born outside", "Born inside country"]	import:population.yaml	2026-10-25 14:06:07.47708+00	t
17	column	17	synonyms	[]	["presence", "currently inside", "currently outside", "Currently inside country"]	import:population.yaml	2026-10-25 14:06:07.478545+00	t
18	column	11	synonyms	[]	["job", "occupation", "profession", "job title"]	import:population.yaml	2026-10-25 14:06:07.479914+00	t
19	column	15	synonyms	[]	["job classification", "occupational level", "skill level", "job level", "workforce level"]	import:population.yaml	2026-10-25 14:06:07.480912+00	t
20	column	24	synonyms	[]	["sponsor", "sponsorship", "sponsored", "Sponsor category"]	import:population.yaml	2026-10-25 14:06:07.482426+00	t
21	column	18	synonyms	[]	["destination", "destination country", "Last known destination country"]	import:population.yaml	2026-10-25 14:06:07.483517+00	t
22	column	26	synonyms	[]	["tribe", "family", "clan", "family name"]	import:population.yaml	2026-10-25 14:06:07.484677+00	t
23	column	31	synonyms	[]	["registry area", "area of registration", "place of registration", "area of origin", "khulasat al qaid", "registry district"]	import:population.yaml	2026-10-25 14:06:07.485832+00	t
24	column	28	synonyms	[]	["previous nationality", "former nationality", "original nationality", "naturalized", "naturalised", "naturalization"]	import:population.yaml	2026-10-25 14:06:07.486973+00	t
25	column	1	synonyms	[]	["population", "population count", "headcount", "count"]	import:population.yaml	2026-10-25 14:06:07.487916+00	t
26	table	1	description	\N	Current snapshot of individuals in the UAE population — citizens, residents (expats), GCC nationals and visitors. Each row is a pre-aggregated count of individuals sharing one combination of demographic dimension values within a person category; population_cnt must be SUMmed, never counted with COUNT(*). No time axis — historical questions do not apply.	import:population.yaml	2026-10-25 14:06:07.489791+00	t
27	table	1	grain	\N	One row per unique combination of demographic dimension values (nationality, emirate, gender, age group, job, sponsor, etc.) within one person_category — not one row per person. population_cnt holds the count of individuals in that combination.	import:population.yaml	2026-10-25 14:06:07.489792+00	t
28	table	1	version	v1	v2	import:population.yaml	2026-10-25 14:06:07.497234+00	f
29	column	20	synonyms_ar	[]	["فئة", "الفئة", "فئة الشخص"]	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.901564+00	t
30	column	22	synonyms_ar	[]	["نوع الاقامة", "نوع التأشيرة", "الفئة الفرعية"]	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.905062+00	t
31	column	3	synonyms_ar	[]	["الجنسية", "جنسية", "الجنسيات"]	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.906459+00	t
32	column	5	synonyms_ar	[]	["الجنس", "النوع"]	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.907561+00	t
33	column	8	synonyms_ar	[]	["العمر", "السن", "الأعمار", "الفئة العمرية"]	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.90872+00	t
34	column	9	synonyms_ar	[]	["الإمارة", "إمارة", "المدينة"]	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.909842+00	t
35	column	7	synonyms_ar	[]	["مكان الولادة", "مكان الميلاد"]	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.911182+00	t
36	column	17	synonyms_ar	[]	["التواجد", "الحضور", "التواجد الحالي"]	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.912301+00	t
37	column	11	synonyms_ar	[]	["المهنة", "الوظيفة", "المسمى الوظيفي"]	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.913798+00	t
38	column	15	synonyms_ar	[]	["تصنيف الوظيفة", "المستوى الوظيفي", "مستوى المهارة"]	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.914902+00	t
39	column	24	synonyms_ar	[]	["الكفيل", "الكفالة", "المكفولين", "المكفولون", "فئة الكفيل"]	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.915941+00	t
40	column	18	synonyms_ar	[]	["الوجهة", "بلد الوجهة", "بلد الوجهة الأخيرة"]	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.916793+00	t
41	column	26	synonyms_ar	[]	["القبيلة", "العائلة", "الفخذ"]	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.917777+00	t
42	column	31	synonyms_ar	[]	["خلاصة القيد", "منطقة القيد", "منطقة خلاصة القيد", "منطقة الأصل", "المقيدين", "المقيدون", "مقيد"]	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.91873+00	t
43	column	28	synonyms_ar	[]	["الجنسية السابقة", "الجنسية الأصلية", "المتجنسين", "المتجنسون", "متجنسين", "التجنس"]	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.91976+00	t
44	table	1	version	v2	v3	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.9245+00	f
45	dimension	5	description	The individual's age band.	The individual's age band. fsdf	iris009147@gmail.com	2026-10-25 17:26:19.643857+00	f
46	dimension	5	description	The individual's age band. fsdf	The individual's age band.	iris009147@gmail.com	2026-10-25 17:26:36.88346+00	f
\.


--
-- Data for Name: column; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."column" (id, table_id, name, data_type, nullable, ordinal, removed, needs_review, display_name, display_name_ar, description, description_ar, role, semantic_type, unit, default_aggregation, non_additive, allowed_values, example_values, format, synonyms, synonyms_ar, allowed_values_ar, is_primary_key, pii, deprecated, quarantined, quarantine_reason) FROM stdin;
2	1	nat_iso_code	varchar	t	2	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
4	1	nationality_ar	varchar	t	4	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
6	1	gender_ar	varchar	t	6	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
10	1	emirate_ar	varchar	t	10	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
12	1	prof_base_ar	varchar	t	12	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
29	1	citi_prv_nat_ar	varchar	t	29	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
1	1	population_cnt	bigint	t	1	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	["population", "population count", "headcount", "count"]	[]	{}	f	f	f	f	\N
3	1	nationality_en	varchar	t	3	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	["nationality", "nationalities"]	["\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0629", "\\u062c\\u0646\\u0633\\u064a\\u0629", "\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0627\\u062a"]	{}	f	f	f	f	\N
5	1	gender_en	varchar	t	5	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	["gender", "sex"]	["\\u0627\\u0644\\u062c\\u0646\\u0633", "\\u0627\\u0644\\u0646\\u0648\\u0639"]	{}	f	f	f	f	\N
7	1	is_born_inside	varchar	t	7	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	["birthplace", "place of birth", "born inside", "born outside", "Born inside country"]	["\\u0645\\u0643\\u0627\\u0646 \\u0627\\u0644\\u0648\\u0644\\u0627\\u062f\\u0629", "\\u0645\\u0643\\u0627\\u0646 \\u0627\\u0644\\u0645\\u064a\\u0644\\u0627\\u062f"]	{}	f	f	f	f	\N
8	1	age_group	varchar	t	8	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	["age", "age band", "age bracket", "age range", "age group"]	["\\u0627\\u0644\\u0639\\u0645\\u0631", "\\u0627\\u0644\\u0633\\u0646", "\\u0627\\u0644\\u0623\\u0639\\u0645\\u0627\\u0631", "\\u0627\\u0644\\u0641\\u0626\\u0629 \\u0627\\u0644\\u0639\\u0645\\u0631\\u064a\\u0629"]	{}	f	f	f	f	\N
9	1	emirate_en	varchar	t	9	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	["emirate", "city", "region"]	["\\u0627\\u0644\\u0625\\u0645\\u0627\\u0631\\u0629", "\\u0625\\u0645\\u0627\\u0631\\u0629", "\\u0627\\u0644\\u0645\\u062f\\u064a\\u0646\\u0629"]	{}	f	f	f	f	\N
11	1	prof_base_en	varchar	t	11	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	["job", "occupation", "profession", "job title"]	["\\u0627\\u0644\\u0645\\u0647\\u0646\\u0629", "\\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u0629", "\\u0627\\u0644\\u0645\\u0633\\u0645\\u0649 \\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u064a"]	{}	f	f	f	f	\N
13	1	prof_cat_en	varchar	t	13	t	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
14	1	prof_cat_ar	varchar	t	14	t	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
15	1	job_level_en	varchar	t	13	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	["job classification", "occupational level", "skill level", "job level", "workforce level"]	["\\u062a\\u0635\\u0646\\u064a\\u0641 \\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u0629", "\\u0627\\u0644\\u0645\\u0633\\u062a\\u0648\\u0649 \\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u064a", "\\u0645\\u0633\\u062a\\u0648\\u0649 \\u0627\\u0644\\u0645\\u0647\\u0627\\u0631\\u0629"]	{}	f	f	f	f	\N
16	1	job_level_ar	varchar	t	14	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
17	1	is_cur_inside	varchar	t	15	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	["presence", "currently inside", "currently outside", "Currently inside country"]	["\\u0627\\u0644\\u062a\\u0648\\u0627\\u062c\\u062f", "\\u0627\\u0644\\u062d\\u0636\\u0648\\u0631", "\\u0627\\u0644\\u062a\\u0648\\u0627\\u062c\\u062f \\u0627\\u0644\\u062d\\u0627\\u0644\\u064a"]	{}	f	f	f	f	\N
18	1	last_known_dest_cntry_en	varchar	t	16	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	["destination", "destination country", "Last known destination country"]	["\\u0627\\u0644\\u0648\\u062c\\u0647\\u0629", "\\u0628\\u0644\\u062f \\u0627\\u0644\\u0648\\u062c\\u0647\\u0629", "\\u0628\\u0644\\u062f \\u0627\\u0644\\u0648\\u062c\\u0647\\u0629 \\u0627\\u0644\\u0623\\u062e\\u064a\\u0631\\u0629"]	{}	f	f	f	f	\N
19	1	last_known_dest_cntry_ar	varchar	t	17	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
20	1	prsn_cat_en	varchar	t	18	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	["category", "Person category"]	["\\u0641\\u0626\\u0629", "\\u0627\\u0644\\u0641\\u0626\\u0629", "\\u0641\\u0626\\u0629 \\u0627\\u0644\\u0634\\u062e\\u0635"]	{}	f	f	f	f	\N
21	1	prsn_cat_ar	varchar	t	19	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
22	1	prsn_sub_cat_en	varchar	t	20	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	["subcategory", "residency type", "visa type", "citizenship type", "Person subcategory"]	["\\u0646\\u0648\\u0639 \\u0627\\u0644\\u0627\\u0642\\u0627\\u0645\\u0629", "\\u0646\\u0648\\u0639 \\u0627\\u0644\\u062a\\u0623\\u0634\\u064a\\u0631\\u0629", "\\u0627\\u0644\\u0641\\u0626\\u0629 \\u0627\\u0644\\u0641\\u0631\\u0639\\u064a\\u0629"]	{}	f	f	f	f	\N
23	1	prsn_sub_cat_ar	varchar	t	21	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
25	1	spon_cat_ar	varchar	t	23	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
27	1	citi_tribe_ar	varchar	t	25	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
30	1	cit_desc_ar	varchar	t	27	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
28	1	citi_prv_nat_en	varchar	t	28	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	["previous nationality", "former nationality", "original nationality", "naturalized", "naturalised", "naturalization"]	["\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0629 \\u0627\\u0644\\u0633\\u0627\\u0628\\u0642\\u0629", "\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0629 \\u0627\\u0644\\u0623\\u0635\\u0644\\u064a\\u0629", "\\u0627\\u0644\\u0645\\u062a\\u062c\\u0646\\u0633\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u062a\\u062c\\u0646\\u0633\\u0648\\u0646", "\\u0645\\u062a\\u062c\\u0646\\u0633\\u064a\\u0646", "\\u0627\\u0644\\u062a\\u062c\\u0646\\u0633"]	{}	f	f	f	f	\N
24	1	spon_cat_en	varchar	t	22	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	["sponsor", "sponsorship", "sponsored", "Sponsor category"]	["\\u0627\\u0644\\u0643\\u0641\\u064a\\u0644", "\\u0627\\u0644\\u0643\\u0641\\u0627\\u0644\\u0629", "\\u0627\\u0644\\u0645\\u0643\\u0641\\u0648\\u0644\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u0643\\u0641\\u0648\\u0644\\u0648\\u0646", "\\u0641\\u0626\\u0629 \\u0627\\u0644\\u0643\\u0641\\u064a\\u0644"]	{}	f	f	f	f	\N
26	1	citi_tribe_en	varchar	t	24	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	["tribe", "family", "clan", "family name"]	["\\u0627\\u0644\\u0642\\u0628\\u064a\\u0644\\u0629", "\\u0627\\u0644\\u0639\\u0627\\u0626\\u0644\\u0629", "\\u0627\\u0644\\u0641\\u062e\\u0630"]	{}	f	f	f	f	\N
31	1	cit_desc_en	varchar	t	26	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	["registry area", "area of registration", "place of registration", "area of origin", "khulasat al qaid", "registry district"]	["\\u062e\\u0644\\u0627\\u0635\\u0629 \\u0627\\u0644\\u0642\\u064a\\u062f", "\\u0645\\u0646\\u0637\\u0642\\u0629 \\u0627\\u0644\\u0642\\u064a\\u062f", "\\u0645\\u0646\\u0637\\u0642\\u0629 \\u062e\\u0644\\u0627\\u0635\\u0629 \\u0627\\u0644\\u0642\\u064a\\u062f", "\\u0645\\u0646\\u0637\\u0642\\u0629 \\u0627\\u0644\\u0623\\u0635\\u0644", "\\u0627\\u0644\\u0645\\u0642\\u064a\\u062f\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u0642\\u064a\\u062f\\u0648\\u0646", "\\u0645\\u0642\\u064a\\u062f"]	{}	f	f	f	f	\N
32	2	customer_id	bigint	t	1	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
33	2	email	varchar	t	2	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	t	name looks sensitive (email)
34	2	country_code	varchar	t	3	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
35	2	segment	varchar	t	4	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
36	3	date_key	date	t	1	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
37	3	year	integer	t	2	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
38	3	month	integer	t	3	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
39	3	is_weekend	boolean	t	4	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
40	4	product_id	bigint	t	1	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
41	4	product_name	varchar	t	2	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
42	4	category	varchar	t	3	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
43	4	list_price	double	t	4	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
44	5	order_id	bigint	t	1	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
45	5	order_line	integer	t	2	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
46	5	customer_id	bigint	t	3	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
47	5	product_id	bigint	t	4	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
48	5	order_date	date	t	5	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
49	5	quantity	integer	t	6	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
50	5	gross_amount	double	t	7	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
51	5	discount_amount	double	t	8	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
52	5	net_amount	double	t	9	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
53	5	status	varchar	t	10	f	t	\N	\N	\N	\N	\N	\N	\N	\N	f	{}	[]	\N	[]	[]	{}	f	f	f	f	\N
\.


--
-- Data for Name: dimension; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dimension (id, key, label, label_ar, description, description_ar, synonyms, synonyms_ar, families, applies_to, applies_note, applies_note_ar, status, created_at, updated_at) FROM stdin;
4	gender	Gender	الجنس	The individual's gender — male or female.	جنس الفرد — ذكر أو أنثى.	["gender", "sex"]	["\\u0627\\u0644\\u062c\\u0646\\u0633", "\\u0627\\u0644\\u0646\\u0648\\u0639"]	[]	[]	\N	\N	published	2026-10-25 14:06:05.657312+00	2026-10-25 14:06:05.657315+00
9	profession_base	Job	الوظيفة	The individual's specific job or occupation.	وظيفة الفرد أو مهنته المحددة.	["job", "occupation", "profession", "job title"]	["\\u0627\\u0644\\u0645\\u0647\\u0646\\u0629", "\\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u0629", "\\u0627\\u0644\\u0645\\u0633\\u0645\\u0649 \\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u064a"]	[{"term": "food sector", "term_ar": null, "values": ["Chef", "Food Service Worker", "Food Production Worker"]}, {"term": "food industry", "term_ar": null, "values": ["Chef", "Food Service Worker", "Food Production Worker"]}, {"term": "hospitality", "term_ar": null, "values": ["Chef", "Food Service Worker", "Food Production Worker"]}, {"term": "\\u0645\\u062c\\u0627\\u0644 \\u0627\\u0644\\u0627\\u063a\\u0630\\u064a\\u0629", "term_ar": null, "values": ["Chef", "Food Service Worker", "Food Production Worker"]}, {"term": "\\u0642\\u0637\\u0627\\u0639 \\u0627\\u0644\\u0627\\u063a\\u0630\\u064a\\u0629", "term_ar": null, "values": ["Chef", "Food Service Worker", "Food Production Worker"]}, {"term": "healthcare", "term_ar": null, "values": ["Doctor", "Dentist", "Nurse", "Pharmacist", "Paramedic", "Healthcare Technician", "Healthcare Support Worker", "Veterinarian", "Psychologist"]}, {"term": "health sector", "term_ar": null, "values": ["Doctor", "Dentist", "Nurse", "Pharmacist", "Paramedic", "Healthcare Technician", "Healthcare Support Worker", "Veterinarian", "Psychologist"]}, {"term": "medical field", "term_ar": null, "values": ["Doctor", "Dentist", "Nurse", "Pharmacist", "Paramedic", "Healthcare Technician", "Healthcare Support Worker", "Veterinarian", "Psychologist"]}, {"term": "\\u0627\\u0644\\u0642\\u0637\\u0627\\u0639 \\u0627\\u0644\\u0635\\u062d\\u064a", "term_ar": null, "values": ["Doctor", "Dentist", "Nurse", "Pharmacist", "Paramedic", "Healthcare Technician", "Healthcare Support Worker", "Veterinarian", "Psychologist"]}, {"term": "\\u0627\\u0644\\u0631\\u0639\\u0627\\u064a\\u0629 \\u0627\\u0644\\u0635\\u062d\\u064a\\u0629", "term_ar": null, "values": ["Doctor", "Dentist", "Nurse", "Pharmacist", "Paramedic", "Healthcare Technician", "Healthcare Support Worker", "Veterinarian", "Psychologist"]}, {"term": "\\u0645\\u062c\\u0627\\u0644 \\u0627\\u0644\\u0631\\u0639\\u0627\\u064a\\u0629 \\u0627\\u0644\\u0635\\u062d\\u064a\\u0629", "term_ar": null, "values": ["Doctor", "Dentist", "Nurse", "Pharmacist", "Paramedic", "Healthcare Technician", "Healthcare Support Worker", "Veterinarian", "Psychologist"]}, {"term": "\\u0627\\u0644\\u0645\\u062c\\u0627\\u0644 \\u0627\\u0644\\u0637\\u0628\\u064a", "term_ar": null, "values": ["Doctor", "Dentist", "Nurse", "Pharmacist", "Paramedic", "Healthcare Technician", "Healthcare Support Worker", "Veterinarian", "Psychologist"]}, {"term": "education sector", "term_ar": null, "values": ["Teacher", "Teaching Assistant", "Academic", "Trainer", "Librarian"]}, {"term": "\\u0642\\u0637\\u0627\\u0639 \\u0627\\u0644\\u062a\\u0639\\u0644\\u064a\\u0645", "term_ar": null, "values": ["Teacher", "Teaching Assistant", "Academic", "Trainer", "Librarian"]}, {"term": "\\u0645\\u062c\\u0627\\u0644 \\u0627\\u0644\\u062a\\u0639\\u0644\\u064a\\u0645", "term_ar": null, "values": ["Teacher", "Teaching Assistant", "Academic", "Trainer", "Librarian"]}, {"term": "construction sector", "term_ar": null, "values": ["Construction Worker", "Carpenter", "Electrician", "Plumber", "Welder", "Craft Worker", "Surveyor", "Architect", "Draftsperson"]}, {"term": "\\u0642\\u0637\\u0627\\u0639 \\u0627\\u0644\\u0628\\u0646\\u0627\\u0621", "term_ar": null, "values": ["Construction Worker", "Carpenter", "Electrician", "Plumber", "Welder", "Craft Worker", "Surveyor", "Architect", "Draftsperson"]}, {"term": "\\u0642\\u0637\\u0627\\u0639 \\u0627\\u0644\\u0625\\u0646\\u0634\\u0627\\u0621\\u0627\\u062a", "term_ar": null, "values": ["Construction Worker", "Carpenter", "Electrician", "Plumber", "Welder", "Craft Worker", "Surveyor", "Architect", "Draftsperson"]}, {"term": "technology sector", "term_ar": null, "values": ["Software Developer", "Software Tester", "IT Architect", "IT Infrastructure Specialist", "IT Support Technician", "Cybersecurity Specialist", "Data Specialist", "Systems Analyst", "AI Specialist"]}, {"term": "it sector", "term_ar": null, "values": ["Software Developer", "Software Tester", "IT Architect", "IT Infrastructure Specialist", "IT Support Technician", "Cybersecurity Specialist", "Data Specialist", "Systems Analyst", "AI Specialist"]}, {"term": "\\u0642\\u0637\\u0627\\u0639 \\u0627\\u0644\\u062a\\u0642\\u0646\\u064a\\u0629", "term_ar": null, "values": ["Software Developer", "Software Tester", "IT Architect", "IT Infrastructure Specialist", "IT Support Technician", "Cybersecurity Specialist", "Data Specialist", "Systems Analyst", "AI Specialist"]}, {"term": "security sector", "term_ar": null, "values": ["Police and Border Officer", "Security Officer", "Military Personnel", "Firefighter", "Rescue Worker"]}, {"term": "\\u0627\\u0644\\u0642\\u0637\\u0627\\u0639 \\u0627\\u0644\\u0623\\u0645\\u0646\\u064a", "term_ar": null, "values": ["Police and Border Officer", "Security Officer", "Military Personnel", "Firefighter", "Rescue Worker"]}, {"term": "finance sector", "term_ar": null, "values": ["Accountant", "Auditor", "Financial Adviser", "Actuary", "Risk and Compliance Specialist"]}, {"term": "\\u0627\\u0644\\u0642\\u0637\\u0627\\u0639 \\u0627\\u0644\\u0645\\u0627\\u0644\\u064a", "term_ar": null, "values": ["Accountant", "Auditor", "Financial Adviser", "Actuary", "Risk and Compliance Specialist"]}, {"term": "legal sector", "term_ar": null, "values": ["Lawyer", "Judge", "Legal Assistant"]}, {"term": "\\u0627\\u0644\\u0642\\u0637\\u0627\\u0639 \\u0627\\u0644\\u0642\\u0627\\u0646\\u0648\\u0646\\u064a", "term_ar": null, "values": ["Lawyer", "Judge", "Legal Assistant"]}, {"term": "transport sector", "term_ar": null, "values": ["Driver", "Pilot", "Flight Attendant", "Seafarer", "Delivery Worker", "Air Traffic Controller", "Logistics Specialist", "Warehouse Worker"]}, {"term": "\\u0642\\u0637\\u0627\\u0639 \\u0627\\u0644\\u0646\\u0642\\u0644", "term_ar": null, "values": ["Driver", "Pilot", "Flight Attendant", "Seafarer", "Delivery Worker", "Air Traffic Controller", "Logistics Specialist", "Warehouse Worker"]}]	[{"dimension": "person_category", "values": ["EXPAT"]}]	\N	\N	published	2026-10-25 14:06:05.97943+00	2026-10-25 14:06:05.979431+00
1	person_category	Person category	فئة الشخص	Which population group the record belongs to: citizen, resident (expatriate), GCC national, or visitor.	الفئة السكانية التي يندرج ضمنها السجل: مواطن، مقيم (وافد)، مواطن خليجي، أو زائر.	["category"]	["\\u0641\\u0626\\u0629", "\\u0627\\u0644\\u0641\\u0626\\u0629"]	[]	[]	\N	\N	published	2026-10-25 14:06:04.636656+00	2026-10-25 14:06:04.63666+00
2	person_subcategory	Person subcategory	الفئة الفرعية	A finer breakdown within each person category, such as citizenship type, residency type, or visa type.	تصنيف أدق ضمن كل فئة سكانية، مثل نوع المواطنة أو نوع الإقامة أو نوع التأشيرة.	["subcategory", "residency type", "visa type", "citizenship type"]	["\\u0646\\u0648\\u0639 \\u0627\\u0644\\u0627\\u0642\\u0627\\u0645\\u0629", "\\u0646\\u0648\\u0639 \\u0627\\u0644\\u062a\\u0623\\u0634\\u064a\\u0631\\u0629"]	[]	[{"dimension": "person_category", "values": ["CITIZEN", "EXPAT", "VISITOR"]}]	\N	\N	published	2026-10-25 14:06:04.955354+00	2026-10-25 14:06:04.955358+00
3	nationality	Nationality	الجنسية	The individual's nationality (country of citizenship).	جنسية الفرد (بلد الجنسية).	["nationality", "nationalities"]	["\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0629", "\\u062c\\u0646\\u0633\\u064a\\u0629", "\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0627\\u062a"]	[]	[]	\N	\N	published	2026-10-25 14:06:05.300759+00	2026-10-25 14:06:05.300763+00
5	age_group	Age group	الفئة العمرية	The individual's age band.	الفئة العمرية للفرد.	["age", "age band", "age bracket", "age range", "age group"]	["\\u0627\\u0644\\u0639\\u0645\\u0631", "\\u0627\\u0644\\u0633\\u0646", "\\u0627\\u0644\\u0623\\u0639\\u0645\\u0627\\u0631"]	[]	[]	\N	\N	published	2026-10-25 14:06:05.769017+00	2026-10-25 17:26:36.888517+00
6	emirate	Emirate	الإمارة	The emirate associated with the individual's residency, visa, or registration.	الإمارة المرتبطة بإقامة الفرد أو تأشيرته أو تسجيله.	["emirate", "city", "region"]	["\\u0627\\u0644\\u0625\\u0645\\u0627\\u0631\\u0629", "\\u0625\\u0645\\u0627\\u0631\\u0629", "\\u0627\\u0644\\u0645\\u062f\\u064a\\u0646\\u0629"]	[]	[]	\N	\N	published	2026-10-25 14:06:05.773332+00	2026-10-25 14:06:05.773334+00
7	is_born_inside	Born inside country	مكان الولادة	Whether the individual was born inside or outside the country.	هل وُلد الفرد داخل الدولة أم خارجها.	["birthplace", "place of birth", "born inside", "born outside"]	["\\u0645\\u0643\\u0627\\u0646 \\u0627\\u0644\\u0648\\u0644\\u0627\\u062f\\u0629", "\\u0645\\u0643\\u0627\\u0646 \\u0627\\u0644\\u0645\\u064a\\u0644\\u0627\\u062f"]	[]	[]	\N	\N	published	2026-10-25 14:06:05.972233+00	2026-10-25 14:06:05.972236+00
8	is_currently_inside	Currently inside country	التواجد الحالي	Whether the individual is currently located inside or outside the country.	هل الفرد متواجد حالياً داخل الدولة أم خارجها.	["presence", "currently inside", "currently outside"]	["\\u0627\\u0644\\u062a\\u0648\\u0627\\u062c\\u062f", "\\u0627\\u0644\\u062d\\u0636\\u0648\\u0631"]	[]	[]	\N	\N	published	2026-10-25 14:06:05.976053+00	2026-10-25 14:06:05.976055+00
10	job_classification	Job classification	تصنيف الوظيفة	The seniority or skill level of the individual's job.	مستوى وظيفة الفرد من حيث المهارة أو المسؤولية.	["job classification", "occupational level", "skill level", "job level", "workforce level"]	["\\u062a\\u0635\\u0646\\u064a\\u0641 \\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u0629", "\\u0627\\u0644\\u0645\\u0633\\u062a\\u0648\\u0649 \\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u064a", "\\u0645\\u0633\\u062a\\u0648\\u0649 \\u0627\\u0644\\u0645\\u0647\\u0627\\u0631\\u0629"]	[]	[{"dimension": "person_category", "values": ["EXPAT"]}]	\N	\N	published	2026-10-25 14:06:06.209286+00	2026-10-25 14:06:06.209289+00
11	sponsor_category	Sponsor category	فئة الكفيل	The type of sponsor for the individual's visa or residency.	نوع كفيل تأشيرة الفرد أو إقامته.	["sponsor", "sponsorship", "sponsored"]	["\\u0627\\u0644\\u0643\\u0641\\u064a\\u0644", "\\u0627\\u0644\\u0643\\u0641\\u0627\\u0644\\u0629", "\\u0627\\u0644\\u0645\\u0643\\u0641\\u0648\\u0644\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u0643\\u0641\\u0648\\u0644\\u0648\\u0646"]	[]	[{"dimension": "person_category", "values": ["EXPAT", "VISITOR"]}]	\N	\N	published	2026-10-25 14:06:06.315139+00	2026-10-25 14:06:06.315143+00
12	destination_country	Last known destination country	بلد الوجهة الأخيرة	The country the individual is currently located in, for those outside their home country.	البلد الذي يتواجد فيه الفرد حالياً، لمن هم خارج بلدهم الأصلي.	["destination", "destination country"]	["\\u0627\\u0644\\u0648\\u062c\\u0647\\u0629", "\\u0628\\u0644\\u062f \\u0627\\u0644\\u0648\\u062c\\u0647\\u0629"]	[]	[{"dimension": "person_category", "values": ["CITIZEN"]}, {"dimension": "is_currently_inside", "values": ["Outside"]}]	\N	\N	published	2026-10-25 14:06:06.571656+00	2026-10-25 14:06:06.57166+00
13	tribe	Tribe	القبيلة	The family tribe the individual belongs to, where applicable.	القبيلة التي ينتمي إليها الفرد، عند الانطباق.	["tribe", "family", "clan", "family name"]	["\\u0627\\u0644\\u0642\\u0628\\u064a\\u0644\\u0629", "\\u0627\\u0644\\u0639\\u0627\\u0626\\u0644\\u0629", "\\u0627\\u0644\\u0641\\u062e\\u0630"]	[]	[{"dimension": "person_category", "values": ["CITIZEN"]}]	\N	\N	published	2026-10-25 14:06:06.782396+00	2026-10-25 14:06:06.782401+00
14	citizen_area	Registry area	منطقة خلاصة القيد	The administrative area the individual is registered under.	المنطقة الإدارية المسجل الفرد تحتها.	["registry area", "area of registration", "place of registration", "area of origin", "khulasat al qaid", "registry district"]	["\\u062e\\u0644\\u0627\\u0635\\u0629 \\u0627\\u0644\\u0642\\u064a\\u062f", "\\u0645\\u0646\\u0637\\u0642\\u0629 \\u0627\\u0644\\u0642\\u064a\\u062f", "\\u0645\\u0646\\u0637\\u0642\\u0629 \\u062e\\u0644\\u0627\\u0635\\u0629 \\u0627\\u0644\\u0642\\u064a\\u062f", "\\u0645\\u0646\\u0637\\u0642\\u0629 \\u0627\\u0644\\u0623\\u0635\\u0644", "\\u0627\\u0644\\u0645\\u0642\\u064a\\u062f\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u0642\\u064a\\u062f\\u0648\\u0646", "\\u0645\\u0642\\u064a\\u062f"]	[]	[{"dimension": "person_category", "values": ["CITIZEN"]}]	\N	\N	published	2026-10-25 14:06:06.989586+00	2026-10-25 14:06:06.98959+00
15	previous_nationality	Previous nationality	الجنسية السابقة	The nationality the individual held before their current one, where applicable.	الجنسية التي كان يحملها الفرد قبل جنسيته الحالية، عند الانطباق.	["previous nationality", "former nationality", "original nationality", "naturalized", "naturalised", "naturalization"]	["\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0629 \\u0627\\u0644\\u0633\\u0627\\u0628\\u0642\\u0629", "\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0629 \\u0627\\u0644\\u0623\\u0635\\u0644\\u064a\\u0629", "\\u0627\\u0644\\u0645\\u062a\\u062c\\u0646\\u0633\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u062a\\u062c\\u0646\\u0633\\u0648\\u0646", "\\u0645\\u062a\\u062c\\u0646\\u0633\\u064a\\u0646", "\\u0627\\u0644\\u062a\\u062c\\u0646\\u0633"]	[]	[{"dimension": "person_category", "values": ["CITIZEN"]}]	\N	\N	published	2026-10-25 14:06:07.21338+00	2026-10-25 14:06:07.213383+00
\.


--
-- Data for Name: dimension_binding; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dimension_binding (id, dimension_id, column_id, created_at) FROM stdin;
1	1	20	2026-10-25 14:06:04.643009+00
2	2	22	2026-10-25 14:06:04.95706+00
3	3	3	2026-10-25 14:06:05.302477+00
4	4	5	2026-10-25 14:06:05.658889+00
5	5	8	2026-10-25 14:06:05.770308+00
6	6	9	2026-10-25 14:06:05.774744+00
7	7	7	2026-10-25 14:06:05.973513+00
8	8	17	2026-10-25 14:06:05.977123+00
9	9	11	2026-10-25 14:06:05.98079+00
10	10	15	2026-10-25 14:06:06.210551+00
11	11	24	2026-10-25 14:06:06.316354+00
12	12	18	2026-10-25 14:06:06.573109+00
13	13	26	2026-10-25 14:06:06.784052+00
14	14	31	2026-10-25 14:06:06.992018+00
15	15	28	2026-10-25 14:06:07.214447+00
\.


--
-- Data for Name: dimension_value; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dimension_value (id, dimension_id, value, label, label_ar, aliases, "position") FROM stdin;
1	1	CITIZEN	CITIZEN	مواطن	["citizens", "citizen", "nationals", "emiratis", "\\u0645\\u0648\\u0627\\u0637\\u0646", "\\u0645\\u0648\\u0627\\u0637\\u0646\\u0648\\u0646", "\\u0645\\u0648\\u0627\\u0637\\u0646\\u064a\\u0646"]	0
2	1	EXPAT	EXPAT	مقيم	["resident", "residents", "expat", "expats", "expatriates", "\\u0645\\u0642\\u064a\\u0645", "\\u0645\\u0642\\u064a\\u0645\\u0648\\u0646", "\\u0645\\u0642\\u064a\\u0645\\u064a\\u0646", "\\u0648\\u0627\\u0641\\u062f", "\\u0648\\u0627\\u0641\\u062f\\u0648\\u0646"]	1
3	1	GCC	GCC	مجلس دول التعاون الخليجي	["gulf nationals", "gcc nationals", "\\u062e\\u0644\\u064a\\u062c\\u064a", "\\u062e\\u0644\\u064a\\u062c\\u064a\\u0648\\u0646", "\\u0645\\u062c\\u0644\\u0633 \\u062f\\u0648\\u0644 \\u0627\\u0644\\u062a\\u0639\\u0627\\u0648\\u0646 \\u0627\\u0644\\u062e\\u0644\\u064a\\u062c\\u064a"]	2
4	1	VISITOR	VISITOR	زائر	["visitor", "visitors", "tourists", "\\u0632\\u0627\\u0626\\u0631", "\\u0632\\u0648\\u0627\\u0631", "\\u0633\\u0627\\u0626\\u062d", "\\u0633\\u064a\\u0627\\u062d"]	3
5	2	Labor Residencies	Labor Residencies	اقامات العمل	["work residency", "work visa", "labor visa", "\\u0627\\u0642\\u0627\\u0645\\u0629 \\u0639\\u0645\\u0644", "\\u062a\\u0623\\u0634\\u064a\\u0631\\u0629 \\u0639\\u0645\\u0644"]	0
6	2	Family and Dependent Residencies	Family and Dependent Residencies	اقامات الاسرة والمعالين	["family visa", "\\u0627\\u0642\\u0627\\u0645\\u0629 \\u0639\\u0627\\u0626\\u0644\\u064a\\u0629"]	1
7	2	Native Citizen	Native Citizen	مواطن من الاصل	["native"]	2
8	2	Long Term Residencies - Golden Residency	Long Term Residencies - Golden Residency	اقامات طويلة المدة - اقاماة ذهبية	["golden visa", "golden residency", "\\u0627\\u0644\\u062a\\u0623\\u0634\\u064a\\u0631\\u0629 \\u0627\\u0644\\u0630\\u0647\\u0628\\u064a\\u0629", "\\u0627\\u0644\\u0627\\u0642\\u0627\\u0645\\u0629 \\u0627\\u0644\\u0630\\u0647\\u0628\\u064a\\u0629"]	3
9	2	Visit Entry Permit	Visit Entry Permit	إذن دخول للزيارة	["visit visa", "visit permit", "tourist visa", "\\u062a\\u0623\\u0634\\u064a\\u0631\\u0629 \\u0632\\u064a\\u0627\\u0631\\u0629", "\\u0625\\u0630\\u0646 \\u062f\\u062e\\u0648\\u0644 \\u0632\\u064a\\u0627\\u0631\\u0629"]	4
10	2	General Residencies	General Residencies	اقامات عامه	[]	5
11	2	Government and Semi Government Residencies	Government and Semi Government Residencies	الاقامات الحكومية وشبه الحكومية	[]	6
12	2	Invetment and Business Residencies	Invetment and Business Residencies	اقامات الاستثمار والاعمال	["investor visa", "\\u0627\\u0642\\u0627\\u0645\\u0629 \\u0645\\u0633\\u062a\\u062b\\u0645\\u0631", "investors", "\\u0645\\u0633\\u062a\\u062b\\u0645\\u0631\\u0648\\u0646", "\\u0645\\u0633\\u062a\\u062b\\u0645\\u0631\\u064a\\u0646"]	7
13	2	Other Visa	Other Visa	تأشيرة أخرى	[]	8
14	2	Long Term Residencies - Others	Long Term Residencies - Others	اقامات طويلة المدة - اخرى	[]	9
15	2	Education Visa	Education Visa	تأشيرات تعليمية	["student visa", "\\u062a\\u0623\\u0634\\u064a\\u0631\\u0629 \\u062f\\u0631\\u0627\\u0633\\u064a\\u0629", "students", "\\u0637\\u0644\\u0627\\u0628", "\\u0627\\u0644\\u0637\\u0644\\u0627\\u0628"]	10
16	2	Long Term Residencies - Green Residency	Long Term Residencies - Green Residency	اقامات طويلة المدة - اقاماة خضراء	["green visa", "green residency", "green residence", "\\u0627\\u0644\\u062a\\u0623\\u0634\\u064a\\u0631\\u0629 \\u0627\\u0644\\u062e\\u0636\\u0631\\u0627\\u0621", "\\u0627\\u0644\\u0627\\u0642\\u0627\\u0645\\u0629 \\u0627\\u0644\\u062e\\u0636\\u0631\\u0627\\u0621"]	11
17	2	Acquired Citizenship	Acquired Citizenship	مواطن عن طريق التجنس	["naturalized", "naturalised", "\\u0645\\u062a\\u062c\\u0646\\u0633"]	12
18	2	Work Entry Permit	Work Entry Permit	إذن دخول بغرض العمل	["work entry permit", "\\u0625\\u0630\\u0646 \\u062f\\u062e\\u0648\\u0644 \\u0639\\u0645\\u0644"]	13
19	2	Family Members Entry Permit	Family Members Entry Permit	إذن دخول أفراد الأسرة	["family entry permit", "\\u0625\\u0630\\u0646 \\u062f\\u062e\\u0648\\u0644 \\u0623\\u0641\\u0631\\u0627\\u062f \\u0627\\u0644\\u0623\\u0633\\u0631\\u0629"]	14
20	2	Non-Work Entry Permit	Non-Work Entry Permit	إذن دخول غير مرتبط بالعمل	[]	15
21	2	Medical Visa	Medical Visa	تاشيرات علاجية	[]	16
22	2	Long Term Residencies - Blue Residency	Long Term Residencies - Blue Residency	اقامات طويلة المدة - اقاماة زرقاء	["blue visa", "blue residency", "blue residence", "\\u0627\\u0644\\u062a\\u0623\\u0634\\u064a\\u0631\\u0629 \\u0627\\u0644\\u0632\\u0631\\u0642\\u0627\\u0621", "\\u0627\\u0644\\u0627\\u0642\\u0627\\u0645\\u0629 \\u0627\\u0644\\u0632\\u0631\\u0642\\u0627\\u0621"]	17
23	2	Long Term Entry Permit	Long Term Entry Permit	إذن دخول طويل الأجل	["long term entry permit", "\\u0625\\u0630\\u0646 \\u062f\\u062e\\u0648\\u0644 \\u0637\\u0648\\u064a\\u0644 \\u0627\\u0644\\u0623\\u062c\\u0644"]	18
24	2	Long Term Family Members Entry Permit	Long Term Family Members Entry Permit	إذن دخول أفراد أسرة طويل الأجل	[]	19
25	2	Investor or Partner Entry Permit	Investor or Partner Entry Permit	إذن دخول مستثمر أو شريك	["investor entry permit", "partner entry permit", "\\u0625\\u0630\\u0646 \\u062f\\u062e\\u0648\\u0644 \\u0645\\u0633\\u062a\\u062b\\u0645\\u0631"]	20
26	3	India	India	الهند	["\\u0647\\u0646\\u0648\\u062f", "\\u0627\\u0644\\u0647\\u0646\\u0648\\u062f", "indians"]	0
27	3	United Arab Emirates	United Arab Emirates	الإمارات العربية المتحدة	["uae nationals", "\\u0625\\u0645\\u0627\\u0631\\u0627\\u062a\\u064a\\u0648\\u0646", "\\u0625\\u0645\\u0627\\u0631\\u0627\\u062a\\u064a\\u064a\\u0646"]	1
28	3	Pakistan	Pakistan	باكستان	["\\u0628\\u0627\\u0643\\u0633\\u062a\\u0627\\u0646\\u064a\\u0648\\u0646", "\\u0628\\u0627\\u0643\\u0633\\u062a\\u0627\\u0646\\u064a\\u064a\\u0646", "pakistanis"]	2
29	3	Bangladesh	Bangladesh	بنغلاديش	["\\u0628\\u0646\\u063a\\u0627\\u0644\\u064a\\u0648\\u0646", "\\u0628\\u0646\\u063a\\u0627\\u0644\\u064a\\u064a\\u0646", "\\u0628\\u0646\\u063a\\u0644\\u0627\\u062f\\u064a\\u0634\\u064a\\u0648\\u0646", "bangladeshis"]	3
30	3	Philippines	Philippines	الفلبين	["\\u0641\\u0644\\u0628\\u064a\\u0646\\u064a\\u0648\\u0646", "\\u0641\\u0644\\u0628\\u064a\\u0646\\u064a\\u064a\\u0646", "filipinos"]	4
31	3	Egypt	Egypt	مصر	["\\u0645\\u0635\\u0631\\u064a\\u0648\\u0646", "\\u0645\\u0635\\u0631\\u064a\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u0635\\u0631\\u064a\\u064a\\u0646", "egyptians"]	5
32	3	SRILANKAN	SRILANKAN	سيرلانكا	["sri lanka", "sri lankan", "sri lankans", "\\u0633\\u0631\\u064a\\u0644\\u0627\\u0646\\u0643\\u0627", "\\u0633\\u0631\\u064a\\u0644\\u0627\\u0646\\u0643\\u064a\\u0648\\u0646", "\\u0633\\u0631\\u064a\\u0644\\u0627\\u0646\\u0643\\u064a\\u064a\\u0646"]	6
33	3	Nepal	Nepal	نيبال	["\\u0646\\u064a\\u0628\\u0627\\u0644\\u064a\\u0648\\u0646", "\\u0646\\u064a\\u0628\\u0627\\u0644\\u064a\\u064a\\u0646", "nepalese"]	7
34	3	China	China	الصين	["\\u0635\\u064a\\u0646\\u064a\\u0648\\u0646", "\\u0635\\u064a\\u0646\\u064a\\u064a\\u0646", "chinese"]	8
35	3	United Kingdom	United Kingdom	المملكة المتحدة	["uk", "britain", "british", "\\u0628\\u0631\\u0637\\u0627\\u0646\\u064a\\u0648\\u0646", "\\u0628\\u0631\\u064a\\u0637\\u0627\\u0646\\u064a\\u064a\\u0646", "\\u0628\\u0631\\u064a\\u0637\\u0627\\u0646\\u064a\\u0627", "\\u0628\\u0631\\u064a\\u0637\\u0627\\u0646\\u064a\\u0648\\u0646"]	9
36	3	Syrian Arab Republic	Syrian Arab Republic	الجمهورية العربية السورية	["syria", "syrians", "\\u0633\\u0648\\u0631\\u064a\\u0627", "\\u0633\\u0648\\u0631\\u064a\\u0648\\u0646", "\\u0633\\u0648\\u0631\\u064a\\u064a\\u0646"]	10
37	3	Jordan	Jordan	الأردن	["\\u0623\\u0631\\u062f\\u0646\\u064a\\u0648\\u0646", "\\u0623\\u0631\\u062f\\u0646\\u064a\\u064a\\u0646", "jordanians"]	11
38	3	Indonesia	Indonesia	إندونيسيا	["\\u0625\\u0646\\u062f\\u0648\\u0646\\u064a\\u0633\\u064a\\u0648\\u0646", "\\u0625\\u0646\\u062f\\u0648\\u0646\\u064a\\u0633\\u064a\\u064a\\u0646", "indonesians"]	12
39	3	United States of America	United States of America	الولايات المتحدة	["usa", "us", "america", "americans", "\\u0623\\u0645\\u0631\\u064a\\u0643\\u064a\\u0648\\u0646", "\\u0623\\u0645\\u0631\\u064a\\u0643\\u064a\\u064a\\u0646", "\\u0623\\u0645\\u0631\\u064a\\u0643\\u0627\\u0646"]	13
40	3	Nigeria	Nigeria	نيجيريا	["\\u0646\\u064a\\u062c\\u064a\\u0631\\u064a\\u0648\\u0646", "nigerians"]	14
41	3	Sudan	Sudan	السودان	["\\u0633\\u0648\\u062f\\u0627\\u0646\\u064a\\u0648\\u0646", "\\u0633\\u0648\\u062f\\u0627\\u0646\\u064a\\u064a\\u0646", "sudanese"]	15
42	3	Ethiopia	Ethiopia	إثيوبيا	["\\u0625\\u062b\\u064a\\u0648\\u0628\\u064a\\u0648\\u0646", "\\u0625\\u062b\\u064a\\u0648\\u0628\\u064a\\u064a\\u0646", "ethiopians"]	16
43	3	Yemen	Yemen	اليمن	["\\u064a\\u0645\\u0646\\u064a\\u0648\\u0646", "\\u064a\\u0645\\u0646\\u064a\\u064a\\u0646", "yemenis"]	17
44	3	Lebanon	Lebanon	لبنان	["\\u0644\\u0628\\u0646\\u0627\\u0646\\u064a\\u0648\\u0646", "\\u0644\\u0628\\u0646\\u0627\\u0646\\u064a\\u064a\\u0646", "lebanese"]	18
45	3	Morocco	Morocco	المغرب	["\\u0645\\u063a\\u0627\\u0631\\u0628\\u0629", "moroccans"]	19
46	3	Kenya	Kenya	كينيا	["\\u0643\\u064a\\u0646\\u064a\\u0648\\u0646", "kenyans"]	20
47	3	Russian Federation	Russian Federation	الاتحاد الروسي	["russia", "russians", "\\u0631\\u0648\\u0633\\u064a\\u0627", "\\u0631\\u0648\\u0633"]	21
48	3	Germany	Germany	المانيا	["\\u0623\\u0644\\u0645\\u0627\\u0646", "germans"]	22
49	3	Italy	Italy	ايطاليا	[]	23
50	3	France	France	فرنسا	["\\u0641\\u0631\\u0646\\u0633\\u064a\\u0648\\u0646", "\\u0641\\u0631\\u0646\\u0633\\u064a\\u064a\\u0646"]	24
51	3	Uzbekistan	Uzbekistan	أوزبكستان	[]	25
52	3	Kazakhstan	Kazakhstan	كازاخستان	[]	26
53	3	Saudi Arabia	Saudi Arabia	السعوديه	["ksa", "saudi", "saudis", "\\u0633\\u0639\\u0648\\u062f\\u064a\\u0648\\u0646", "\\u0633\\u0639\\u0648\\u062f\\u064a\\u064a\\u0646"]	27
54	3	Oman	Oman	سلطنة عمان	[]	28
55	3	Rwanda	Rwanda	رواندا	[]	29
56	3	Croatia	Croatia	كرواتيا	[]	30
57	3	Madagascar	Madagascar	مدغشقر	[]	31
58	3	Brunei Darussalam	Brunei Darussalam	بروناي دار السلام	[]	32
59	3	Mozambique	Mozambique	موزمبيق	[]	33
60	3	Tajikistan	Tajikistan	طاجكستان	[]	34
61	3	Congo	Congo	الكونغو	[]	35
62	3	Japan	Japan	اليابان	[]	36
63	3	French Guiana	French Guiana	غيانا الفرنسية	[]	37
64	3	Haiti	Haiti	هايتي	[]	38
65	3	Mali	Mali	مالي	[]	39
66	3	Bahamas	Bahamas	جزر البهاما	[]	40
67	3	Saint Kitts and Nevis	Saint Kitts and Nevis	سانت كيتس ونيفيس	[]	41
68	3	Slovakia	Slovakia	سلوفاكيا	[]	42
69	3	Costa Rica	Costa Rica	كوستاريكا	[]	43
70	3	Iceland	Iceland	ايسلندا	[]	44
71	3	Republic of Somaliland	Republic of Somaliland	جمهورية أرض الصومال	[]	45
72	3	Hong Kong	Hong Kong	هونغ كونغ	[]	46
73	3	Tanzania United Republic	Tanzania United Republic	جمهورية تنزانيا المتحدة	[]	47
74	3	Cyprus	Cyprus	قبرص	[]	48
75	3	Finland	Finland	فنلندا	[]	49
76	3	Malaysia	Malaysia	ماليزيا	[]	50
77	3	Libya	Libya	ليبيا	[]	51
78	3	New Zealand	New Zealand	نيوزيلاندا	[]	52
79	3	Swaziland	Swaziland	سوازيلاند	[]	53
80	3	Bermuda	Bermuda	برمودا	[]	54
81	3	Central African Republic	Central African Republic	جمهورية أفريقيا الوسطى	[]	55
82	3	Democratic Rep. of Congo	Democratic Rep. of Congo	جمهورية كونغوالديمقراطية	[]	56
83	3	Malawi	Malawi	ملاوي	[]	57
84	3	Singapore	Singapore	سنغافورة	[]	58
85	3	Switzerland	Switzerland	سويسرا	[]	59
86	3	Cambodia	Cambodia	كمبوديا	[]	60
87	3	Chile	Chile	تشيلي	[]	61
88	3	Hungary	Hungary	هنغاريا	[]	62
89	3	Kuwait	Kuwait	الكويت	[]	63
90	3	Maldives	Maldives	المالديف	[]	64
91	3	Moldova  Republic of	Moldova  Republic of	جمهورية مولدوفا	[]	65
92	3	Brazil	Brazil	البرازيل	[]	66
93	3	DOMINICAN	DOMINICAN	الدومنيكان	[]	67
94	3	Fiji	Fiji	فيجي	[]	68
95	3	Georgia	Georgia	جورجيا	[]	69
96	3	Ireland	Ireland	ايرلندا	[]	70
97	3	Lesotho	Lesotho	ليسوتو	[]	71
98	3	Macau	Macau	ماكاو	[]	72
99	3	Portugal	Portugal	البرتغال	[]	73
100	3	Solomon Islands	Solomon Islands	جزر سولومون	[]	74
101	3	Barbados	Barbados	بربادوس	[]	75
102	3	Eritrea	Eritrea	إريتريا	[]	76
103	3	Niger	Niger	النيجر	[]	77
104	3	Togo	Togo	توغو	[]	78
105	3	Bolivia Plurinational St.	Bolivia Plurinational St.	بوليفيا،المتعددة القوميات	[]	79
106	3	New Caledonia	New Caledonia	كاليدونيا الجديدة	[]	80
107	3	Austria	Austria	النمسا	[]	81
108	3	Canada	Canada	كندا	[]	82
109	3	Colombia	Colombia	كولومبيا	[]	83
110	3	Comoros	Comoros	جزر القمر	[]	84
111	3	Guatemala	Guatemala	غواتيمالا	[]	85
112	3	Holy See (Vatican)	Holy See (Vatican)	الفاتيكان	[]	86
113	3	Micronesia  Federated St.	Micronesia  Federated St.	ولايات ميكرونيزيا الموحدة	[]	87
114	3	Papua New Guinea	Papua New Guinea	بابوا غينيا الجديدة	[]	88
115	3	Poland	Poland	بولندا	[]	89
116	3	Thailand	Thailand	تايلاند	[]	90
117	3	Uganda	Uganda	أوغندا	[]	91
118	3	Botswana	Botswana	بوتسوانا	[]	92
119	3	Greenland	Greenland	جرينلاند	[]	93
120	3	Mauritius	Mauritius	موريشيوس	[]	94
121	3	Montenegro	Montenegro	مونتينيجرو	[]	95
122	3	Netherlands	Netherlands	هولندا	["\\u0647\\u0648\\u0644\\u0646\\u062f\\u064a\\u0648\\u0646", "\\u0647\\u0648\\u0644\\u0646\\u062f\\u064a\\u064a\\u0646", "dutch"]	96
123	3	Tuvalu	Tuvalu	توفالو	[]	97
124	3	Bulgaria	Bulgaria	بلغاريا	[]	98
125	3	Liberia	Liberia	ليبيريا	[]	99
126	3	Antigua and Barbuda	Antigua and Barbuda	أنتيغوا وبربودا	[]	100
127	3	Lithuania	Lithuania	ليتوانيا	[]	101
128	3	North Korea Democratic R.	North Korea Democratic R.	جمهورية كوريا الشمالية	["north korea", "\\u0643\\u0648\\u0631\\u064a\\u0627 \\u0627\\u0644\\u0634\\u0645\\u0627\\u0644\\u064a\\u0629"]	102
129	3	Palau	Palau	بالاو	[]	103
130	3	Vanuatu	Vanuatu	فانواتو	[]	104
131	3	Zambia	Zambia	زامبيا	[]	105
132	3	"Palestine, State of"	"Palestine, State of"	فلسطين	[]	106
133	3	Belize	Belize	بليز	[]	107
134	3	Monaco	Monaco	موناكو	[]	108
135	3	Norway	Norway	النرويج	[]	109
136	3	Saint Helena	Saint Helena	سانت هيلينا	[]	110
137	3	South Africa	South Africa	جنوب أفريقيا	[]	111
138	3	Suriname	Suriname	سورينام	[]	112
139	3	Afghanistan	Afghanistan	افغانستان	[]	113
140	3	Angola	Angola	انجوليا	[]	114
141	3	Armenia	Armenia	أرمينيا	[]	115
142	3	Belgium	Belgium	بلجيكا	[]	116
143	3	Ecuador	Ecuador	الاكوادور	[]	117
144	3	Iraq	Iraq	العراق	[]	118
145	3	Israel	Israel	إسرائيل	[]	119
146	3	Bosnia and Herzegovina	Bosnia and Herzegovina	البوسنه والهرسك	[]	120
147	3	Chad	Chad	تشاد	[]	121
148	3	Equatorial Guinea	Equatorial Guinea	غينيا الاستوائية	[]	122
149	3	Faroe Islands	Faroe Islands	جزر الفارو	[]	123
150	3	Latvia	Latvia	لاتفيا	[]	124
151	3	South Sudan	South Sudan	جنوب السودان	[]	125
152	3	Trinidad and Tobago	Trinidad and Tobago	ترينيداد وتوباغو	[]	126
153	3	Algeria	Algeria	الجزائر	[]	127
154	3	Malta	Malta	مالطا	[]	128
155	3	Nauru	Nauru	ناورو	[]	129
156	3	Nicaragua	Nicaragua	نيكاراغوا	[]	130
157	3	Somalia	Somalia	الصومال	[]	131
158	3	Viet Nam	Viet Nam	فيتنام	["vietnam", "\\u0641\\u064a\\u062a\\u0646\\u0627\\u0645"]	132
159	3	Burkina Faso	Burkina Faso	بوركينا فاسو	[]	133
160	3	Czech Republic	Czech Republic	جمهورية التشيك	[]	134
161	3	Liechtenstein	Liechtenstein	ليختنشتاين	[]	135
162	3	Mongolia	Mongolia	منغوليا	[]	136
163	3	Panama	Panama	بنما	[]	137
164	3	Sierra Leone	Sierra Leone	سيراليون	[]	138
165	3	Ukraine	Ukraine	أوكرانيا	[]	139
166	3	Djibouti	Djibouti	جيبوتي	[]	140
167	3	Guinea	Guinea	غينيا	[]	141
168	3	Macedonia	Macedonia	مقدونيا	[]	142
169	3	Marshall Islands	Marshall Islands	جزر مارشال	[]	143
170	3	Martinique	Martinique	مارتينيك	[]	144
171	3	Peru	Peru	بيرو	[]	145
172	3	Romania	Romania	رومانيا	[]	146
173	3	Samoa	Samoa	ساموا	[]	147
174	3	South Korea  Republic of	South Korea  Republic of	جمهورية كوريا الجنوبية	["south korea", "south koreans", "\\u0643\\u0648\\u0631\\u064a\\u0627 \\u0627\\u0644\\u062c\\u0646\\u0648\\u0628\\u064a\\u0629"]	148
175	3	Taiwan	Taiwan	تايوان	[]	149
176	3	Azerbaijan	Azerbaijan	أذربيجان	[]	150
177	3	Cuba	Cuba	كوبا	[]	151
178	3	Gambia	Gambia	غامبيا	[]	152
179	3	Lao People's Democratic	Lao People's Democratic	جمهورية لاو الديمقراطية	[]	153
180	3	Namibia	Namibia	ناميبيا	[]	154
181	3	Uruguay	Uruguay	أوروغواي	[]	155
182	3	Argentina	Argentina	الأرجنتين	[]	156
183	3	Burundi	Burundi	بوروندي	[]	157
184	3	COMMONWEALTH OF DOMINICA	COMMONWEALTH OF DOMINICA	كمنولث دومينكا	[]	158
185	3	Greece	Greece	اليونان	[]	159
186	3	Grenada	Grenada	غرينادا	[]	160
187	3	Iran  Islamic Republic of	Iran  Islamic Republic of	جمهورية ايران الإسلامية	["iran", "iranians", "\\u0625\\u064a\\u0631\\u0627\\u0646", "\\u0625\\u064a\\u0631\\u0627\\u0646\\u064a\\u0648\\u0646", "\\u0625\\u064a\\u0631\\u0627\\u0646\\u064a\\u064a\\u0646"]	161
188	3	Saint Lucia	Saint Lucia	سانت لوسيا	[]	162
189	3	San Marino	San Marino	سان مارينو	[]	163
190	3	Sao Tome and Principe	Sao Tome and Principe	ساو تومي وبرينسيبي	[]	164
191	3	Turkey	Turkey	تركيا	["\\u0623\\u062a\\u0631\\u0627\\u0643", "turks", "turkish"]	165
192	3	Belarus	Belarus	بيلاروس	[]	166
193	3	Cameroon	Cameroon	الكاميرون	[]	167
194	3	Jamaica	Jamaica	جامايكا	[]	168
195	3	Kiribati	Kiribati	كيريباتي	[]	169
196	3	Kosovo	Kosovo	كوسوفو	[]	170
197	3	Mauritania	Mauritania	موريتانيا	[]	171
198	3	Tonga	Tonga	تونغا	[]	172
199	3	Honduras	Honduras	هندوراس	[]	173
200	3	Paraguay	Paraguay	باراغواي	[]	174
201	3	Seychelles	Seychelles	سيشيل	[]	175
202	3	Slovenia	Slovenia	سلوفينيا	[]	176
203	3	St Vincent and Grenadines	St Vincent and Grenadines	سانت فنسنت والجرينادينز	[]	177
204	3	Cote d'lvoire	Cote d'lvoire	كوت ديفوار(ساحل العاج)	[]	178
205	3	Puerto Rico	Puerto Rico	بورتوريكو	[]	179
206	3	Venezuela	Venezuela	فنزويلا	[]	180
207	3	Australia	Australia	أستراليا	[]	181
208	3	Bhutan	Bhutan	بوتان	[]	182
209	3	Spain	Spain	اسبانيا	[]	183
210	3	Unspecified Nationality	Unspecified Nationality	غير محددة	[]	184
211	3	Cayman Islands	Cayman Islands	جزر كايمن	[]	185
212	3	Guinea-Bissau	Guinea-Bissau	غينيا بيساو	[]	186
213	3	Guyana	Guyana	غيانا	[]	187
214	3	Cabo Verde	Cabo Verde	كابو فيردي	[]	188
215	3	Ghana	Ghana	غانا	[]	189
216	3	Northern Mariana Islands	Northern Mariana Islands	جزر ماريانا الشمالية	[]	190
217	3	Serbia	Serbia	صربيا	[]	191
218	3	Tunisia	Tunisia	تونس	[]	192
219	3	Zimbabwe	Zimbabwe	زيمبابوي	[]	193
220	3	Andorra	Andorra	اندورا	[]	194
221	3	Gabon	Gabon	غابون	[]	195
222	3	Myanmar	Myanmar	ميانمار	[]	196
223	3	Sweden	Sweden	السويد	[]	197
224	3	Timor-Leste	Timor-Leste	تيمور - ليشتي	[]	198
225	3	Benin	Benin	بنن	[]	199
226	3	Mexico	Mexico	المكسيك	[]	200
227	3	Moldova-	Moldova-	مولدوفا-	[]	201
228	3	Albania	Albania	البانيا	[]	202
229	3	El Salvador	El Salvador	السلفادور	[]	203
230	3	Kyrgyzstan	Kyrgyzstan	قيرغيزستان	[]	204
231	3	Luxembourg	Luxembourg	لوكسمبورج	[]	205
232	3	Turkmenistan	Turkmenistan	تركمانستان	[]	206
233	3	Denmark	Denmark	الدنمارك	[]	207
234	3	Estonia	Estonia	إستونيا	[]	208
235	3	Senegal	Senegal	السنغال	[]	209
236	3	Bahrain	Bahrain	البحرين	[]	210
237	3	Qatar	Qatar	قطر	[]	211
238	4	male	male	ذكر	["men", "man", "males", "\\u0630\\u0643\\u0631", "\\u0630\\u0643\\u0648\\u0631", "\\u0631\\u062c\\u0627\\u0644"]	0
239	4	female	female	انثي	["women", "woman", "females", "\\u0627\\u0646\\u062b\\u0649", "\\u0627\\u0646\\u0627\\u062b", "\\u0646\\u0633\\u0627\\u0621"]	1
240	5	0-18	0-18	\N	["minors", "children", "\\u0623\\u0637\\u0641\\u0627\\u0644", "\\u0642\\u0627\\u0635\\u0631\\u0648\\u0646"]	0
241	5	19-21	19-21	\N	[]	1
242	5	22-29	22-29	\N	[]	2
243	5	30-39	30-39	\N	[]	3
244	5	40-49	40-49	\N	[]	4
245	5	50-59	50-59	\N	[]	5
246	5	60+	60+	\N	["seniors", "elderly", "\\u0643\\u0628\\u0627\\u0631 \\u0627\\u0644\\u0633\\u0646", "\\u0645\\u0633\\u0646\\u0648\\u0646"]	6
247	6	Dubai	Dubai	دبي	["dxb"]	0
248	6	Abu Dhabi	Abu Dhabi	ابو ظبي	["auh", "the capital", "\\u0627\\u0644\\u0639\\u0627\\u0635\\u0645\\u0629", "\\u0628\\u0648\\u0638\\u0628\\u064a"]	1
249	6	Sharjah	Sharjah	الشارقه	["shj"]	2
250	6	Ajman	Ajman	عجـمان	["ajm"]	3
251	6	Ras Al Khaimah	Ras Al Khaimah	راس الخيمه	["rak", "\\u0631\\u0623\\u0633 \\u0627\\u0644\\u062e\\u064a\\u0645\\u0629"]	4
252	6	Fujairah	Fujairah	الفجيره	["fjr"]	5
253	6	Fediral	Fediral	الاتحاديه	["federal", "\\u0627\\u0644\\u0627\\u062a\\u062d\\u0627\\u062f\\u064a\\u0629"]	6
254	6	Umm Al Quwain	Umm Al Quwain	ام القيوين	["uaq", "\\u0623\\u0645 \\u0627\\u0644\\u0642\\u064a\\u0648\\u064a\\u0646"]	7
255	7	Inside	Inside	داخل الدولة	["born inside", "born in uae", "locally born", "\\u062f\\u0627\\u062e\\u0644 \\u0627\\u0644\\u062f\\u0648\\u0644\\u0629", "\\u0645\\u0648\\u0627\\u0644\\u064a\\u062f \\u0627\\u0644\\u062f\\u0648\\u0644\\u0629"]	0
256	7	Outside	Outside	خارج الدولة	["born outside", "born abroad", "\\u062e\\u0627\\u0631\\u062c \\u0627\\u0644\\u062f\\u0648\\u0644\\u0629", "\\u0645\\u0648\\u0627\\u0644\\u064a\\u062f \\u0627\\u0644\\u062e\\u0627\\u0631\\u062c"]	1
257	8	Inside	Inside	داخل الدولة	["in the country", "currently inside", "\\u062f\\u0627\\u062e\\u0644 \\u0627\\u0644\\u062f\\u0648\\u0644\\u0629 \\u062d\\u0627\\u0644\\u064a\\u0627", "\\u0645\\u062a\\u0648\\u0627\\u062c\\u062f"]	0
258	8	Outside	Outside	خارج الدولة	["abroad", "currently outside", "\\u062e\\u0627\\u0631\\u062c \\u0627\\u0644\\u062f\\u0648\\u0644\\u0629 \\u062d\\u0627\\u0644\\u064a\\u0627", "\\u0628\\u0627\\u0644\\u062e\\u0627\\u0631\\u062c"]	1
259	9	Manager	Manager	مدير	["managers", "\\u0645\\u062f\\u0631\\u0627\\u0621"]	0
260	9	Not in Workforce	Not in Workforce	خارج القوى العاملة	["unemployed", "not working", "housewives", "\\u0627\\u0644\\u0639\\u0627\\u0637\\u0644\\u064a\\u0646 \\u0639\\u0646 \\u0627\\u0644\\u0639\\u0645\\u0644"]	1
261	9	Administrator	Administrator	إداري	[]	2
262	9	Engineer	Engineer	مهندس	["engineers", "\\u0645\\u0647\\u0646\\u062f\\u0633\\u064a\\u0646", "\\u0645\\u0647\\u0646\\u062f\\u0633\\u0648\\u0646"]	3
263	9	Engineering Technician	Engineering Technician	فني هندسي	[]	4
264	9	Analyst	Analyst	محلل	["analysts", "\\u0645\\u062d\\u0644\\u0644\\u064a\\u0646"]	5
265	9	Machine Operator	Machine Operator	مشغل آلات	[]	6
266	9	Clerk	Clerk	كاتب	[]	7
267	9	General Labourer	General Labourer	عامل عام	[]	8
268	9	Mechanic	Mechanic	ميكانيكي	[]	9
269	9	Consultant	Consultant	مستشار	["consultants", "\\u0645\\u0633\\u062a\\u0634\\u0627\\u0631\\u064a\\u0646"]	10
270	9	Risk and Compliance Specialist	Risk and Compliance Specialist	أخصائي مخاطر وامتثال	[]	11
271	9	Salesperson	Salesperson	بائع	["salespeople", "shop assistants", "\\u0628\\u0627\\u0626\\u0639\\u064a\\u0646"]	12
272	9	HR Specialist	HR Specialist	أخصائي موارد بشرية	[]	13
273	9	Craft Worker	Craft Worker	عامل حرفي	[]	14
274	9	Marketing and Communications Specialist	Marketing and Communications Specialist	أخصائي تسويق واتصال	[]	15
275	9	Inspector	Inspector	مفتش	[]	16
276	9	Scientist	Scientist	عالم	["scientists", "\\u0639\\u0644\\u0645\\u0627\\u0621"]	17
277	9	Planner	Planner	مخطط	[]	18
278	9	Accountant	Accountant	محاسب	["accountants", "\\u0645\\u062d\\u0627\\u0633\\u0628\\u064a\\u0646"]	19
279	9	Healthcare Technician	Healthcare Technician	فني رعاية صحية	[]	20
280	9	Doctor	Doctor	طبيب	["doctors", "physicians", "\\u0623\\u0637\\u0628\\u0627\\u0621", "paediatricians", "pediatricians", "surgeons", "\\u062c\\u0631\\u0627\\u062d\\u064a\\u0646", "\\u0623\\u0637\\u0628\\u0627\\u0621 \\u0623\\u0637\\u0641\\u0627\\u0644"]	21
281	9	Procurement Specialist	Procurement Specialist	أخصائي مشتريات	[]	22
282	9	Quality Specialist	Quality Specialist	أخصائي جودة	[]	23
283	9	Teacher	Teacher	معلم	["teachers", "\\u0645\\u0639\\u0644\\u0645\\u064a\\u0646", "\\u0645\\u0639\\u0644\\u0645\\u0648\\u0646", "\\u0645\\u062f\\u0631\\u0633\\u064a\\u0646"]	24
284	9	Logistics Specialist	Logistics Specialist	أخصائي لوجستيات	[]	25
285	9	Driver	Driver	سائق	["drivers", "\\u0633\\u0627\\u0626\\u0642\\u064a\\u0646", "\\u0633\\u0627\\u0626\\u0642\\u0648\\u0646"]	26
286	9	Customer Service Representative	Customer Service Representative	ممثل خدمة عملاء	[]	27
287	9	IT Infrastructure Specialist	IT Infrastructure Specialist	أخصائي بنية تحتية لتقنية المعلومات	[]	28
288	9	Electrician	Electrician	كهربائي	["electricians", "\\u0643\\u0647\\u0631\\u0628\\u0627\\u0626\\u064a\\u064a\\u0646"]	29
289	9	Academic	Academic	أكاديمي	[]	30
290	9	Agricultural Worker	Agricultural Worker	عامل زراعي	["farmers", "\\u0645\\u0632\\u0627\\u0631\\u0639\\u064a\\u0646"]	31
291	9	Construction Worker	Construction Worker	عامل إنشاءات	["builders", "construction workers", "\\u0639\\u0645\\u0627\\u0644 \\u0628\\u0646\\u0627\\u0621", "\\u0639\\u0645\\u0627\\u0644 \\u0625\\u0646\\u0634\\u0627\\u0621\\u0627\\u062a"]	32
292	9	Trainer	Trainer	مدرب	[]	33
293	9	IT Support Technician	IT Support Technician	فني دعم تقني	[]	34
294	9	Administrative Assistant	Administrative Assistant	مساعد إداري	[]	35
295	9	Designer	Designer	مصمم	[]	36
296	9	Software Developer	Software Developer	مطور برمجيات	["programmers", "software developers", "software engineers", "developers", "\\u0645\\u0628\\u0631\\u0645\\u062c\\u064a\\u0646", "\\u0645\\u0637\\u0648\\u0631\\u064a\\u0646"]	37
297	9	Data Specialist	Data Specialist	أخصائي بيانات	[]	38
298	9	Researcher	Researcher	باحث	["researchers", "\\u0628\\u0627\\u062d\\u062b\\u064a\\u0646"]	39
299	9	Others	Others	أخرى	[]	40
300	9	Warehouse Worker	Warehouse Worker	عامل مستودع	[]	41
301	9	Food Production Worker	Food Production Worker	عامل إنتاج الأغذية	[]	42
302	9	Nurse	Nurse	ممرض	["nurses", "\\u0645\\u0645\\u0631\\u0636\\u064a\\u0646", "\\u0645\\u0645\\u0631\\u0636\\u0627\\u062a"]	43
303	9	Auditor	Auditor	مدقق حسابات	["auditors", "\\u0645\\u062f\\u0642\\u0642\\u064a\\u0646"]	44
304	9	Welder	Welder	لحّام	["welders", "\\u0644\\u062d\\u0627\\u0645\\u064a\\u0646"]	45
305	9	Seafarer	Seafarer	بحّار	["sailors", "\\u0628\\u062d\\u0627\\u0631\\u0629"]	46
306	9	Chef	Chef	طاهٍ	["chefs", "cooks", "\\u0637\\u0628\\u0627\\u062e\\u064a\\u0646", "\\u0637\\u0647\\u0627\\u0629"]	47
307	9	Equipment Operator	Equipment Operator	مشغل معدات	[]	48
308	9	Surveyor	Surveyor	مسّاح	[]	49
309	9	Cleaner	Cleaner	عامل نظافة	["cleaners", "\\u0639\\u0645\\u0627\\u0644 \\u0646\\u0638\\u0627\\u0641\\u0629"]	50
310	9	Carpenter	Carpenter	نجار	["carpenters", "\\u0646\\u062c\\u0627\\u0631\\u064a\\u0646"]	51
311	9	Artist	Artist	فنان	[]	52
312	9	Plumber	Plumber	سباك	["plumbers", "\\u0633\\u0628\\u0627\\u0643\\u064a\\u0646"]	53
313	9	Police and Border Officer	Police and Border Officer	ضابط شرطة وحدود	["police", "policemen", "police officers", "\\u0634\\u0631\\u0637\\u0629", "\\u0631\\u062c\\u0627\\u0644 \\u0634\\u0631\\u0637\\u0629"]	54
314	9	Military Personnel	Military Personnel	عسكري	["soldiers", "army", "military", "\\u0639\\u0633\\u0643\\u0631\\u064a\\u064a\\u0646"]	55
315	9	Security Officer	Security Officer	ضابط أمن	["security guards", "guards", "\\u062d\\u0631\\u0627\\u0633 \\u0623\\u0645\\u0646"]	56
316	9	Digital Content Specialist	Digital Content Specialist	أخصائي محتوى رقمي	[]	57
317	9	Systems Analyst	Systems Analyst	محلل نظم	[]	58
318	9	Journalist	Journalist	صحفي	["journalists", "\\u0635\\u062d\\u0641\\u064a\\u064a\\u0646"]	59
319	9	Pharmacist	Pharmacist	صيدلي	["pharmacists", "\\u0635\\u064a\\u0627\\u062f\\u0644\\u0629"]	60
320	9	Religious Official	Religious Official	مختص شؤون دينية	[]	61
321	9	Project Manager	Project Manager	مدير مشاريع	[]	62
322	9	Animal Care Worker	Animal Care Worker	عامل رعاية الحيوانات	[]	63
323	9	Draftsperson	Draftsperson	رسام هندسي	[]	64
324	9	Librarian	Librarian	أمين مكتبة	[]	65
325	9	Receptionist	Receptionist	موظف استقبال	["receptionists", "\\u0645\\u0648\\u0638\\u0641\\u064a \\u0627\\u0633\\u062a\\u0642\\u0628\\u0627\\u0644"]	66
326	9	Lawyer	Lawyer	محامٍ	["lawyers", "attorneys", "\\u0645\\u062d\\u0627\\u0645\\u064a\\u0646"]	67
327	9	Public Official	Public Official	مسؤول حكومي	[]	68
328	9	Cybersecurity Specialist	Cybersecurity Specialist	أخصائي أمن سيبراني	[]	69
329	9	Diplomat	Diplomat	دبلوماسي	[]	70
330	9	Food Service Worker	Food Service Worker	عامل خدمة أغذية	["waiters", "waitresses", "\\u0646\\u0627\\u062f\\u0644\\u064a\\u0646"]	71
331	9	Photographer	Photographer	مصور	[]	72
332	9	Pilot	Pilot	طيار	["pilots", "\\u0637\\u064a\\u0627\\u0631\\u064a\\u0646"]	73
333	9	Personal Care Worker	Personal Care Worker	عامل عناية شخصية	[]	74
334	9	Sports Professional	Sports Professional	محترف رياضي	[]	75
335	9	Air Traffic Controller	Air Traffic Controller	مراقب حركة جوية	[]	76
336	9	Firefighter	Firefighter	إطفائي	["firefighters", "\\u0625\\u0637\\u0641\\u0627\\u0626\\u064a\\u064a\\u0646"]	77
337	9	Healthcare Support Worker	Healthcare Support Worker	عامل دعم رعاية صحية	[]	78
338	9	Cashier	Cashier	أمين صندوق	["cashiers", "\\u0623\\u0645\\u0646\\u0627\\u0621 \\u0635\\u0646\\u062f\\u0648\\u0642"]	79
339	9	Social Worker	Social Worker	أخصائي اجتماعي	[]	80
340	9	Veterinarian	Veterinarian	طبيب بيطري	["vets", "\\u0623\\u0637\\u0628\\u0627\\u0621 \\u0628\\u064a\\u0637\\u0631\\u064a\\u064a\\u0646"]	81
341	9	Business Owner / Entrepreneur	Business Owner / Entrepreneur	صاحب أعمال / رائد أعمال	[]	82
342	9	Architect	Architect	مهندس معماري	["architects", "\\u0645\\u0639\\u0645\\u0627\\u0631\\u064a\\u064a\\u0646"]	83
343	9	Psychologist	Psychologist	أخصائي نفسي	[]	84
344	9	Translator and Interpreter	Translator and Interpreter	مترجم تحريري وفوري	["translators", "\\u0645\\u062a\\u0631\\u062c\\u0645\\u064a\\u0646"]	85
345	9	Delivery Worker	Delivery Worker	عامل توصيل	[]	86
346	9	Counsellor	Counsellor	مرشد	[]	87
347	9	Travel Agent	Travel Agent	وكيل سفر	[]	88
348	9	Fishing Worker	Fishing Worker	عامل صيد الأسماك	[]	89
349	9	Domestic Worker	Domestic Worker	عامل منزلي	["maids", "housemaids", "domestic workers", "\\u062e\\u062f\\u0645", "\\u0639\\u0645\\u0627\\u0644\\u0629 \\u0645\\u0646\\u0632\\u0644\\u064a\\u0629", "\\u0627\\u0644\\u0639\\u0645\\u0627\\u0644\\u0629 \\u0627\\u0644\\u0645\\u0646\\u0632\\u0644\\u064a\\u0629"]	90
350	9	Dentist	Dentist	طبيب أسنان	["dentists", "\\u0623\\u0637\\u0628\\u0627\\u0621 \\u0623\\u0633\\u0646\\u0627\\u0646"]	91
351	9	Tour Guide	Tour Guide	مرشد سياحي	[]	92
352	9	Trader	Trader	متداول	[]	93
353	9	Flight Attendant	Flight Attendant	مضيف طيران	["cabin crew", "\\u0645\\u0636\\u064a\\u0641\\u064a\\u0646", "\\u0645\\u0636\\u064a\\u0641\\u0627\\u062a"]	94
354	9	Financial Adviser	Financial Adviser	مستشار مالي	[]	95
355	9	Real Estate Agent	Real Estate Agent	وسيط عقاري	[]	96
356	9	Teaching Assistant	Teaching Assistant	مساعد تدريس	[]	97
357	9	Account Manager	Account Manager	مدير حسابات عملاء	[]	98
358	9	Executive Assistant	Executive Assistant	مساعد تنفيذي	[]	99
359	9	Judge	Judge	قاضٍ	["judges", "\\u0642\\u0636\\u0627\\u0629"]	100
360	9	Legal Assistant	Legal Assistant	مساعد قانوني	[]	101
361	9	Paramedic	Paramedic	مسعف	[]	102
362	9	Rescue Worker	Rescue Worker	عامل إنقاذ	[]	103
363	9	Funeral Services Worker	Funeral Services Worker	عامل خدمات جنائزية	[]	104
364	9	Business Analyst	Business Analyst	محلل أعمال	[]	105
365	9	Royal and Ruling Official	Royal and Ruling Official	مسؤول ملكي وحاكم	[]	106
366	9	Childcare Worker	Childcare Worker	عامل رعاية أطفال	[]	107
367	9	AI Specialist	AI Specialist	أخصائي ذكاء اصطناعي	[]	108
368	9	Mining Worker	Mining Worker	عامل تعدين	[]	109
369	9	IT Architect	IT Architect	معماري تقنية المعلومات	[]	110
370	9	Waste Management Worker	Waste Management Worker	عامل إدارة النفايات	[]	111
371	9	Software Tester	Software Tester	مختبِر برمجيات	[]	112
372	9	Product Manager	Product Manager	مدير منتجات	[]	113
373	9	Hunting Worker	Hunting Worker	عامل صيد بري	[]	114
374	9	Actuary	Actuary	خبير اكتواري	[]	115
375	10	Leadership & Governance	Leadership & Governance	القيادة والحوكمة	["leadership", "leaders", "executives", "senior management", "governance", "\\u0642\\u064a\\u0627\\u062f\\u0627\\u062a", "\\u0627\\u0644\\u0642\\u064a\\u0627\\u062f\\u0629", "\\u0642\\u064a\\u0627\\u062f\\u064a\\u064a\\u0646"]	0
376	10	Professional / Higher Education	Professional / Higher Education	مهني / تعليم عالٍ	["professionals", "higher education", "professional level", "\\u0645\\u0647\\u0646\\u064a\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u0647\\u0646\\u064a\\u064a\\u0646"]	1
377	10	Administrative / Clerical	Administrative / Clerical	إداري / كتابي	["administrative", "clerical", "clerks", "office staff", "\\u0625\\u062f\\u0627\\u0631\\u064a\\u064a\\u0646", "\\u0643\\u062a\\u0627\\u0628\\u064a\\u064a\\u0646"]	2
378	10	Technical / Skilled	Technical / Skilled	فني / ماهر	["technical", "technicians", "skilled workers", "\\u0641\\u0646\\u064a\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u0647\\u0631\\u0629"]	3
379	10	Frontline / Service	Frontline / Service	خدمي / صفوف أمامية	["frontline", "service workers", "\\u062e\\u062f\\u0645\\u064a\\u064a\\u0646", "\\u0627\\u0644\\u0635\\u0641\\u0648\\u0641 \\u0627\\u0644\\u0623\\u0645\\u0627\\u0645\\u064a\\u0629"]	4
380	10	Manual / Elementary	Manual / Elementary	يدوي / أعمال بسيطة	["manual", "labourers", "laborers", "elementary", "\\u0639\\u0645\\u0627\\u0644 \\u064a\\u062f\\u0648\\u064a\\u064a\\u0646"]	5
381	10	Not in Workforce	Not in Workforce	خارج القوى العاملة	["unemployed", "not working", "\\u0627\\u0644\\u0639\\u0627\\u0637\\u0644\\u064a\\u0646 \\u0639\\u0646 \\u0627\\u0644\\u0639\\u0645\\u0644"]	6
382	10	Others	Others	أخرى	[]	7
383	11	Company Sponsor	Company Sponsor	كفيل شركات	["companies", "\\u0643\\u0641\\u064a\\u0644 \\u0634\\u0631\\u0643\\u0629", "\\u0643\\u0641\\u064a\\u0644 \\u0634\\u0631\\u0643\\u0627\\u062a"]	0
384	11	Citizen Sponsor	Citizen Sponsor	كفيل مواطن	["\\u0643\\u0641\\u064a\\u0644 \\u0645\\u0648\\u0627\\u0637\\u0646"]	1
385	11	Free Zone	Free Zone	منطقة حرة	["free zones", "\\u0645\\u0646\\u0637\\u0642\\u0629 \\u062d\\u0631\\u0629", "\\u0627\\u0644\\u0645\\u0646\\u0627\\u0637\\u0642 \\u0627\\u0644\\u062d\\u0631\\u0629"]	2
386	11	Resident Sponsor	Resident Sponsor	كفيل مقيم	[]	3
387	11	Investor Sponsor	Investor Sponsor	كفيل مستثمر	["\\u0643\\u0641\\u064a\\u0644 \\u0645\\u0633\\u062a\\u062b\\u0645\\u0631"]	4
388	11	Federal Government Sponsor	Federal Government Sponsor	كفيل حكومة / اتحادية	[]	5
389	11	Local Government Sponsor	Local Government Sponsor	كفيل حكومة / محلية	[]	6
390	11	Other	Other	اخرى	[]	7
391	11	Semi-Government Sponsor	Semi-Government Sponsor	كفيل حكومة / شبه حكومة	[]	8
392	11	Farm Sponsor	Farm Sponsor	كفيل مزرعة	[]	9
393	11	International Organizations	International Organizations	منظمات دولية	[]	10
394	11	GCC National Sponsor	GCC National Sponsor	كفيل خليجي	["\\u0643\\u0641\\u064a\\u0644 \\u062e\\u0644\\u064a\\u062c\\u064a"]	11
395	11	Livestock Facility	Livestock Facility	منشأه حيوانيه	[]	12
396	11	Ranch Sponsor	Ranch Sponsor	كفيل عزبة	[]	13
397	11	Agricultural Facility	Agricultural Facility	منشأه زراعيه	[]	14
398	11	Diplomatic Sponsor	Diplomatic Sponsor	كفيل دبلوماسي	[]	15
399	11	Heirs' Guardian	Heirs' Guardian	وصي الورثة	[]	16
400	11	Heirs	Heirs	ورثة	[]	17
401	11	Sheikh Sponsor	Sheikh Sponsor	كفيل شيخ	[]	18
402	11	Fishing Boats	Fishing Boats	قوارب صيد	[]	19
403	12	Saudi Arabia	Saudi Arabia	المملكة العربية السعودية	["ksa", "saudi", "\\u0627\\u0644\\u0633\\u0639\\u0648\\u062f\\u064a\\u0629"]	0
404	12	United Kingdom	United Kingdom	المملكة المتحدة	["uk", "britain", "great britain", "england", "\\u0628\\u0631\\u064a\\u0637\\u0627\\u0646\\u064a\\u0627", "\\u0628\\u0631\\u064a\\u0637\\u0627\\u0646\\u064a\\u0629", "\\u0625\\u0646\\u062c\\u0644\\u062a\\u0631\\u0627"]	1
405	12	Kuwait	Kuwait	الكويت	[]	2
406	12	United States Of America	United States Of America	الولايات المتحدة الأمريكية	["usa", "america", "the states", "united states", "\\u0623\\u0645\\u0631\\u064a\\u0643\\u0627", "\\u0627\\u0644\\u0648\\u0644\\u0627\\u064a\\u0627\\u062a \\u0627\\u0644\\u0645\\u062a\\u062d\\u062f\\u0629"]	3
407	12	Oman	Oman	عمان	[]	4
408	12	Egypt	Egypt	مصر	[]	5
409	12	Qatar	Qatar	قطر	[]	6
410	12	Bahrain	Bahrain	البحرين	[]	7
411	12	France	France	فرنسا	[]	8
412	12	Germany	Germany	ألمانيا	[]	9
413	12	Thailand	Thailand	تايلاند	[]	10
414	12	Japan	Japan	اليابان	[]	11
415	12	Switzerland	Switzerland	سويسرا	[]	12
416	12	Turkey	Turkey	تركيا	["t\\u00fcrkiye", "turkiye"]	13
417	12	Singapore	Singapore	سنغافورة	[]	14
418	12	Morocco	Morocco	المغرب	[]	15
419	12	India	India	الهند	[]	16
420	12	Jordan	Jordan	الأردن	[]	17
421	13	ALSEQETRI	ALSEQETRI	السقطري	["Al Seqetri"]	0
422	13	ALHAMELI	ALHAMELI	الهاملي	["Al Hameli"]	1
423	13	ALASHKHARI	ALASHKHARI	الأشخري	["Al Ashkhari"]	2
424	13	Non Confirmed Tribes	Non Confirmed Tribes	قبائل غير مؤكدة	[]	3
425	13	ALABDOULI	ALABDOULI	العبدولي	["Al Abdouli"]	4
426	13	ALBASTAKI	ALBASTAKI	البستكي	["Al Bastaki"]	5
427	13	No Tribe	No Tribe	بدون قبيلة	["without a tribe", "without tribe"]	6
428	13	ALDOSARI	ALDOSARI	الدوسري	["Al Dosari"]	7
429	13	ALHINDAASSI	ALHINDAASSI	الهنداسي	["Al Hindaassi"]	8
430	13	ALFALAHI	ALFALAHI	الفلاحي	["Al Falahi"]	9
431	13	ALHANAEE	ALHANAEE	الهنائي	["Al Hanaee"]	10
432	13	ALKOKHARDI	ALKOKHARDI	الكوخردي	["Al Kokhardi"]	11
433	13	ALOTBI	ALOTBI	العتبي	["Al Otbi"]	12
434	13	Unknown	Unknown	غير معرفة	["\\u063a\\u064a\\u0631 \\u0645\\u0639\\u0631\\u0648\\u0641\\u0629", "\\u063a\\u064a\\u0631 \\u0645\\u0639\\u0631\\u0648\\u0641"]	13
435	13	ALHEFEITI	ALHEFEITI	الحفيتي	["Al Hefeiti"]	14
436	13	ALSHEHHI	ALSHEHHI	الشحي	["Al Shehhi"]	15
437	13	ALJAHOORI	ALJAHOORI	الجهوري	["Al Jahoori"]	16
438	13	ALRAEESI	ALRAEESI	الرئيسي	["Al Raeesi"]	17
439	13	ALMARAR	ALMARAR	المرر	["Al Marar"]	18
440	13	ALKHAALDI	ALKHAALDI	الخالدي	["Al Khaaldi"]	19
441	13	ALKHAJEH	ALKHAJEH	الخاجه	["Al Khajeh"]	20
442	13	ALGHAITHI	ALGHAITHI	الغيثي	["Al Ghaithi"]	21
443	13	ALKHZAIMI	ALKHZAIMI	الخزيمي	["Al Khzaimi"]	22
444	13	ALDARMAKI	ALDARMAKI	الدرمكي	["Al Darmaki"]	23
445	13	ALHEBSHI	ALHEBSHI	الحبشي	["Al Hebshi"]	24
446	13	ALMANSOORI	ALMANSOORI	المنصوري	["Al Mansoori"]	25
447	13	ALTAEE	ALTAEE	الطائي	["Al Taee"]	26
448	13	ALMUALLA	ALMUALLA	المعلا	["Al Mualla"]	27
449	13	ALKATHEERI	ALKATHEERI	الكثيري	["Al Katheeri"]	28
450	13	ALNUAIMI	ALNUAIMI	النعيمي	["Al Nuaimi"]	29
451	13	ALRIYAMI	ALRIYAMI	الريامي	["Al Riyami"]	30
452	13	ALWHEIBI	ALWHEIBI	الوهيبي	["Al Wheibi"]	31
453	13	ALZAROONI	ALZAROONI	الزرعوني	["Al Zarooni"]	32
454	13	ALSHARQI	ALSHARQI	الشرقي	["Al Sharqi"]	33
455	13	ALBLOOSHI	ALBLOOSHI	البلوشي	["Al Blooshi"]	34
456	13	ALBLOOKI	ALBLOOKI	البلوكي	["Al Blooki"]	35
457	13	ALMASKARI	ALMASKARI	المسكري	["Al Maskari"]	36
458	13	ALALAWI	ALALAWI	العلوي	["Al Alawi"]	37
459	13	ALZUBAIDI	ALZUBAIDI	الزبيدي	["Al Zubaidi"]	38
460	13	ALMEQBAALI	ALMEQBAALI	المقبالي	["Al Meqbaali"]	39
461	13	ALJABERI	ALJABERI	الجابري	["Al Jaberi"]	40
462	13	ALRAYSSI	ALRAYSSI	الريسي	["Al Rayssi"]	41
463	13	ALHOSANI	ALHOSANI	الحوسني	["Al Hosani"]	42
464	13	ALKHLAIFI	ALKHLAIFI	الخليفي	["Al Khlaifi"]	43
465	13	ALMURSHIDI	ALMURSHIDI	المرشدي	["Al Murshidi"]	44
466	13	ALJEFRI	ALJEFRI	الجفري	["Al Jefri"]	45
467	13	ALNEYADI	ALNEYADI	النيادي	["Al Neyadi"]	46
468	13	ALMAZROUEI	ALMAZROUEI	المزروعي	["Al Mazrouei"]	47
469	13	ALMESAFRI	ALMESAFRI	المسافري	["Al Mesafri"]	48
470	13	ALAYDAROOS	ALAYDAROOS	العيدروس	["Al Aydaroos"]	49
471	13	ALSAWWAFI	ALSAWWAFI	الصوافي	["Al Sawwafi"]	50
472	13	ALSHEEBANI	ALSHEEBANI	الشيباني	["Al Sheebani"]	51
473	13	ALHELALI	ALHELALI	الهلالي	["Al Helali"]	52
474	13	AHLI	AHLI	أهلي	[]	53
475	13	ALAKBERI	ALAKBERI	العكبري	["Al Akberi"]	54
476	13	ALEFARI	ALEFARI	العفاري	["Al Efari"]	55
477	13	ALKHANBASHI	ALKHANBASHI	الخنبشي	["Al Khanbashi"]	56
478	13	ALEBRI	ALEBRI	العبري	["Al Ebri"]	57
479	13	ALTAMIMI	ALTAMIMI	التميمي	["Al Tamimi"]	58
480	13	ALEISSAEE	ALEISSAEE	العيسائي	["Al Eissaee"]	59
481	13	ALHAJRI	ALHAJRI	الحجري	["Al Hajri"]	60
482	13	ALHAMMADI	ALHAMMADI	الحمادي	["Al Hammadi"]	61
483	13	ALNAHDI	ALNAHDI	النهدي	["Al Nahdi"]	62
484	13	ALDAHMANI	ALDAHMANI	الدهماني	["Al Dahmani"]	63
485	13	ALYASSI	ALYASSI	الياسي	["Al Yassi"]	64
486	13	ALANSAARI	ALANSAARI	الأنصاري	["Al Ansaari"]	65
487	13	ALJASMI	ALJASMI	الجسمي	["Al Jasmi"]	66
488	13	ALMUHARRAMI	ALMUHARRAMI	المحرمي	["Al Muharrami"]	67
489	13	ALSHERYANI	ALSHERYANI	الشرياني	["Al Sheryani"]	68
490	13	ALKEEBALI	ALKEEBALI	الكيبالي	["Al Keebali"]	69
491	13	ALALEELI	ALALEELI	العليلي	["Al Aleeli"]	70
492	13	ALMAHRI	ALMAHRI	المهري	["Al Mahri"]	71
493	13	ALOTHALI	ALOTHALI	العوذلي	["Al Othali"]	72
494	13	ALROWAHI	ALROWAHI	الرواحي	["Al Rowahi"]	73
495	13	ALNOFELI	ALNOFELI	النوفلي	["Al Nofeli"]	74
496	13	ALMAEENI	ALMAEENI	المعيني	["Al Maeeni"]	75
497	13	ALDEREI	ALDEREI	الدرعي	["Al Derei"]	76
498	13	ALYAFEI	ALYAFEI	اليافعي	["Al Yafei"]	77
499	13	ALTHABAHI	ALTHABAHI	الذباحي	["Al Thabahi"]	78
500	13	ALAMERI	ALAMERI	العامري	["Al Ameri"]	79
501	13	ALSALMI	ALSALMI	السالمي	["Al Salmi"]	80
502	13	ALSHEMEILI	ALSHEMEILI	الشميلي	["Al Shemeili"]	81
503	13	ALHANTOOBI	ALHANTOOBI	الحنطوبي	["Al Hantoobi"]	82
504	13	ALHEBSI	ALHEBSI	الحبسي	["Al Hebsi"]	83
505	13	ALKHOORI	ALKHOORI	الخوري	["Al Khoori"]	84
506	13	ALKINDI	ALKINDI	الكندي	["Al Kindi"]	85
507	13	ALSHIMMARI	ALSHIMMARI	الشمري	["Al Shimmari"]	86
508	13	ALDHAHERI	ALDHAHERI	الظاهري	["Al Dhaheri"]	87
509	13	ALDHEFAIRI	ALDHEFAIRI	الظفيري	["Al Dhefairi"]	88
510	13	ALMARZOOQI	ALMARZOOQI	المرزوقي	["Al Marzooqi"]	89
511	13	ALQAYDI	ALQAYDI	القايدي	["Al Qaydi"]	90
512	13	ALFARSI	ALFARSI	الفارسي	["Al Farsi"]	91
513	13	ALMENHALI	ALMENHALI	المنهالي	["Al Menhali"]	92
514	13	ALSHERAIFI	ALSHERAIFI	الشريفي	["Al Sheraifi"]	93
515	13	ALFZARI	ALFZARI	الفزاري	["Al Fzari"]	94
516	13	ALMAHMOUD	ALMAHMOUD	المحمود	["Al Mahmoud"]	95
517	13	ALMESSABI	ALMESSABI	المصعبي	["Al Messabi"]	96
518	13	ALSAADI	ALSAADI	السعدي	["Al Saadi"]	97
519	13	ALSALAMI	ALSALAMI	السلامي	["Al Salami"]	98
520	13	AL-NAHYAN	AL-NAHYAN	آل نهيان	[]	99
521	13	ALKHAROOSSI	ALKHAROOSSI	الخروصي	["Al Kharoossi"]	100
522	13	ALMANNAEE	ALMANNAEE	المناعي	["Al Mannaee"]	101
523	13	ALSHEBLI	ALSHEBLI	الشبلي	["Al Shebli"]	102
524	13	ALHASSANI	ALHASSANI	الحساني	["Al Hassani"]	103
525	13	ALMADHAANI	ALMADHAANI	المدحاني	["Al Madhaani"]	104
526	13	ALNABHANI	ALNABHANI	النبهاني	["Al Nabhani"]	105
527	13	ALBESHR	ALBESHR	البشر	["Al Beshr"]	106
528	13	ALALI	ALALI	العلي	[]	107
529	13	ALBUSAEEDI	ALBUSAEEDI	البوسعيدي	["Al Busaeedi"]	108
530	13	ALMARSHOODI	ALMARSHOODI	المرشودي	["Al Marshoodi"]	109
531	13	ALSOOMEHI	ALSOOMEHI	السومحي	["Al Soomehi"]	110
532	13	ALBAHRANI	ALBAHRANI	البحراني	["Al Bahrani"]	111
533	13	ALHEMEIRI	ALHEMEIRI	الحميري	["Al Hemeiri"]	112
534	13	ALKAABI	ALKAABI	الكعبي	["Al Kaabi"]	113
535	13	ALSHAMSI	ALSHAMSI	الشامسي	["Al Shamsi"]	114
536	13	ALDHUHOORI	ALDHUHOORI	الظهوري	["Al Dhuhoori"]	115
537	13	ALHARTHI	ALHARTHI	الحارثي	["Al Harthi"]	116
538	13	ALSUWAIDI	ALSUWAIDI	السويدي	["Al Suwaidi"]	117
539	13	AL ALI	AL ALI	آل علي	[]	118
540	13	ALKAWWARI	ALKAWWARI	الكواري	["Al Kawwari"]	119
541	13	ALMEHRZI	ALMEHRZI	المحرزي	["Al Mehrzi"]	120
542	13	ALYILEILI	ALYILEILI	اليليلي	["Al Yileili"]	121
543	13	AL-MAKTOUM	AL-MAKTOUM	آل مكتوم	[]	122
544	13	ALSEIARI	ALSEIARI	الصيعري	["Al Seiari"]	123
545	13	ALYAARBI	ALYAARBI	اليعربي	["Al Yaarbi"]	124
546	13	ALKUWAITI	ALKUWAITI	الكويتي	["Al Kuwaiti"]	125
547	13	ALOBEIDLI	ALOBEIDLI	العبيدلي	["Al Obeidli"]	126
548	13	ALZEYOUDI	ALZEYOUDI	الزيودي	["Al Zeyoudi"]	127
549	13	AL- THANI	AL- THANI	آل ثاني	[]	128
550	13	ALKALBANI	ALKALBANI	الكلباني	["Al Kalbani"]	129
551	13	ALKARBI	ALKARBI	الكربي	["Al Karbi"]	130
552	13	ALMEMARI	ALMEMARI	المعمري	["Al Memari"]	131
553	13	ALMERAIKHI	ALMERAIKHI	المريخي	["Al Meraikhi"]	132
554	13	ALQASIMI	ALQASIMI	القاسمي	["Al Qasimi"]	133
555	13	ALREMEITHI	ALREMEITHI	الرميثي	["Al Remeithi"]	134
556	13	ALATEIBI	ALATEIBI	العتيبي	["Al Ateibi"]	135
557	13	ALHASHMI	ALHASHMI	الهاشمي	["Al Hashmi"]	136
558	13	ALKHATERI	ALKHATERI	الخاطري	["Al Khateri"]	137
559	13	ALFALASI	ALFALASI	الفلاسي	["Al Falasi"]	138
560	13	ALNASRI	ALNASRI	الناصري	["Al Nasri"]	139
561	13	ALRASHDI	ALRASHDI	الراشدي	["Al Rashdi"]	140
562	13	ALSEREIDI	ALSEREIDI	الصريدي	["Al Sereidi"]	141
563	13	ALSHEHYARI	ALSHEHYARI	الشهياري	["Al Shehyari"]	142
564	13	ALWAHSHI	ALWAHSHI	الوحشي	["Al Wahshi"]	143
565	13	ALYAMMAHI	ALYAMMAHI	اليماحي	["Al Yammahi"]	144
566	13	ALAWANI	ALAWANI	العواني	["Al Awani"]	145
567	13	ALMARRI	ALMARRI	المري	["Al Marri"]	146
568	13	ALSUBOUSI	ALSUBOUSI	السبوسي	["Al Subousi"]	147
569	13	ALTAHRI	ALTAHRI	الطاهري	["Al Tahri"]	148
570	13	ALYAAMI	ALYAAMI	اليامي	["Al Yaami"]	149
571	13	ALYAHYAEE	ALYAHYAEE	اليحيائي	["Al Yahyaee"]	150
572	13	ALZAHMI	ALZAHMI	الزحمي	["Al Zahmi"]	151
573	13	ALHARMI	ALHARMI	الحرمي	["Al Harmi"]	152
574	13	ALHARSOOSI	ALHARSOOSI	الحرسوسي	["Al Harsoosi"]	153
575	13	ALKAYYOOMI	ALKAYYOOMI	الكيومي	["Al Kayyoomi"]	154
576	13	ALKHEMEIRI	ALKHEMEIRI	الخميري	["Al Khemeiri"]	155
577	13	ALMASHGHOUNI	ALMASHGHOUNI	المشغوني	["Al Mashghouni"]	156
578	13	AL AHBABI	AL AHBABI	الأحبابي	[]	157
579	13	ALATTAS	ALATTAS	العطاس	["Al Attas"]	158
580	13	ALAWADHI	ALAWADHI	العوضي	["Al Awadhi"]	159
581	13	ALAHMED	ALAHMED	الأحمد	["Al Ahmed"]	160
582	13	ALAJAMI	ALAJAMI	العجمي	["Al Ajami"]	161
583	13	ALAMEEMI	ALAMEEMI	العميمي	["Al Ameemi"]	162
584	13	ALANTALI	ALANTALI	العنتلي	["Al Antali"]	163
585	13	ALLOGHANI	ALLOGHANI	اللوغاني	["Al Loghani"]	164
586	13	ALMULLA	ALMULLA	الملا	["Al Mulla"]	165
587	13	ALQUBAISI	ALQUBAISI	القبيسي	["Al Qubaisi"]	166
588	13	ALSAABRI	ALSAABRI	الصابري	["Al Saabri"]	167
589	13	ALBUAINAIN	ALBUAINAIN	البوعينين	["Al Buainain"]	168
590	13	ALKHAZRAJI	ALKHAZRAJI	الخزرجي	["Al Khazraji"]	169
591	13	ALWAHEDI	ALWAHEDI	الواحدي	["Al Wahedi"]	170
592	13	ALHAJERI	ALHAJERI	الهاجري	["Al Hajeri"]	171
593	13	ALHMOUDI	ALHMOUDI	الحمودي	["Al Hmoudi"]	172
594	13	ALKETBI	ALKETBI	الكتبي	["Al Ketbi"]	173
595	13	ALKHANBOULI	ALKHANBOULI	الخنبولي	["Al Khanbouli"]	174
596	13	ALMEHAIRBI	ALMEHAIRBI	المحيربي	["Al Mehairbi"]	175
597	13	ALSHKEILI	ALSHKEILI	الشكيلي	["Al Shkeili"]	176
598	13	ALADAWI	ALADAWI	العدوي	["Al Adawi"]	177
599	13	ALHADHRAMI	ALHADHRAMI	الحضرمي	["Al Hadhrami"]	178
600	13	ALMHEIRI	ALMHEIRI	المهيري	["Al Mheiri"]	179
601	13	ALQAHTANI	ALQAHTANI	القحطاني	["Al Qahtani"]	180
602	13	ALTENEIJI	ALTENEIJI	الطنيجي	["Al Teneiji"]	181
603	13	ALARYANI	ALARYANI	العرياني	["Al Aryani"]	182
604	13	ALAWLAQI	ALAWLAQI	العولقي	["Al Awlaqi"]	183
605	13	ALHATTAWI	ALHATTAWI	الحتاوي	["Al Hattawi"]	184
606	13	ALJANAAHI	ALJANAAHI	الجناحي	["Al Janaahi"]	185
607	13	ALMATROOSHI	ALMATROOSHI	المطروشي	["Al Matrooshi"]	186
608	13	ALMEWALI	ALMEWALI	المعولي	["Al Mewali"]	187
609	13	ALOTAIBA	ALOTAIBA	العتيبة	["Al Otaiba"]	188
610	13	ALSAEDI	ALSAEDI	الساعدي	["Al Saedi"]	189
611	13	ALSENAANI	ALSENAANI	السناني	["Al Senaani"]	190
612	13	ALSEYABI	ALSEYABI	السيابي	["Al Seyabi"]	191
613	13	ALYAQOUBI	ALYAQOUBI	اليعقوبي	["Al Yaqoubi"]	192
614	13	ALAMOODI	ALAMOODI	العمودي	["Al Amoodi"]	193
615	13	ALBADI	ALBADI	البادي	["Al Badi"]	194
616	13	ALENEZI	ALENEZI	العنزي	["Al Enezi"]	195
617	13	ALGHFELI	ALGHFELI	الغفلي	["Al Ghfeli"]	196
618	13	ALHARBI	ALHARBI	الحربي	["Al Harbi"]	197
619	13	ALMENTHERI	ALMENTHERI	المنذري	["Al Mentheri"]	198
620	13	ALBEDWAWI	ALBEDWAWI	البدواوي	["Al Bedwawi"]	199
621	13	ALGHAFRI	ALGHAFRI	الغافري	["Al Ghafri"]	200
622	13	ALJNEIBI	ALJNEIBI	الجنيبي	["Al Jneibi"]	201
623	13	ALMARBOOEI	ALMARBOOEI	المربوعي	["Al Marbooei"]	202
624	13	ALTHEHLI	ALTHEHLI	الذهلي	["Al Thehli"]	203
625	13	ALZAABI	ALZAABI	الزعابي	["Al Zaabi"]	204
626	13	ALAZEEZI	ALAZEEZI	العزيزي	["Al Azeezi"]	205
627	13	ALBREIKI	ALBREIKI	البريكي	["Al Breiki"]	206
628	13	ALHAMMAMI	ALHAMMAMI	الهمامي	["Al Hammami"]	207
629	13	ALHARMOODI	ALHARMOODI	الهرمودي	["Al Harmoodi"]	208
630	13	ALMASHJARI	ALMASHJARI	المشجري	["Al Mashjari"]	209
631	13	ALNAQBI	ALNAQBI	النقبي	["Al Naqbi"]	210
632	13	AL-HAMED	AL-HAMED	آل حامد	[]	211
633	13	ALMAAZMI	ALMAAZMI	المازمي	["Al Maazmi"]	212
634	13	ALSAMAHI	ALSAMAHI	السماحي	["Al Samahi"]	213
635	13	ALAMEERI	ALAMEERI	الأميري	["Al Ameeri"]	214
636	13	ALDHANHANI	ALDHANHANI	الظنحاني	["Al Dhanhani"]	215
637	13	ALMESMARI	ALMESMARI	المسماري	["Al Mesmari"]	216
638	13	ALSEBEYI	ALSEBEYI	السبيعي	["Al Sebeyi"]	217
639	13	ALAFEEFI	ALAFEEFI	العفيفي	["Al Afeefi"]	218
640	13	ALMAHROOQI	ALMAHROOQI	المحروقي	["Al Mahrooqi"]	219
641	13	ALKHYELI	ALKHYELI	الخييلي	["Al Khyeli"]	220
642	13	ALSAEEDI	ALSAEEDI	السعيدي	["Al Saeedi"]	221
643	13	ALHAATEMI	ALHAATEMI	الحاتمي	["Al Haatemi"]	222
644	13	ALSHUWEIHI	ALSHUWEIHI	الشويهي	["Al Shuweihi"]	223
645	13	ALMTEIRI	ALMTEIRI	المطيري	["Al Mteiri"]	224
646	13	ALQEMZI	ALQEMZI	القمزي	["Al Qemzi"]	225
647	14	DUBAI	DUBAI	دبي	[]	0
648	14	HATTA	HATTA	حتا	[]	1
649	14	DEIRA	DEIRA	ديره	[]	2
650	14	DELMA	DELMA	دلما	["Dalma", "Dalma Island"]	3
651	14	AL BADO	AL BADO	البدو-ابوظبى	[]	4
652	14	AL SAJA	AL SAJA	الصجعه	[]	5
653	14	ABU DHABI	ABU DHABI	ابوظبى	[]	6
654	14	AL DHAFRA-LIWA	AL DHAFRA-LIWA	الظفرة-ليوا	[]	7
655	14	AL QATARAH	AL QATARAH	القطاره	[]	8
656	14	DHAID	DHAID	الذيد	[]	9
657	14	AL BADO - AJMAN	AL BADO - AJMAN	البدو-عجمان	[]	10
658	14	ABU MOSA	ABU MOSA	جزيره ابوموسى	["Abu Musa", "Abu Musa Island"]	11
659	14	AL HILI	AL HILI	الهيلى	[]	12
660	14	MASFOOT	MASFOOT	مصفوت	["Masfut"]	13
661	14	AL KHATEM	AL KHATEM	الختم	["Al Khatim"]	14
662	14	AL AIN AL YAHAR	AL AIN AL YAHAR	العين اليحر	[]	15
663	14	AL MUTARED	AL MUTARED	المعترض	[]	16
664	14	SHARJAH	SHARJAH	الشارقه	[]	17
665	14	AJMAN	AJMAN	عجمان	[]	18
666	14	AL AIN	AL AIN	العين	[]	19
667	14	KHORFAKKAN	KHORFAKKAN	خورفكان	["Khor Fakkan", "Khorfakan"]	20
668	14	ABU SAMRAH	ABU SAMRAH	ابوسمره	[]	21
669	14	AL JIMI	AL JIMI	الجيمى	[]	22
670	14	KALBA	KALBA	كلباء	[]	23
671	14	FALAJ AL MOALLA	FALAJ AL MOALLA	فلج المعلا	["Falaj Al Mualla", "Al Mualla"]	24
672	14	AL MALIHA	AL MALIHA	المليحه	["Mleiha", "Al Mleiha"]	25
673	14	AL MANAMA	AL MANAMA	المنامه	[]	26
674	14	AL MUDAM	AL MUDAM	المدام	["Al Madam", "Madam"]	27
675	14	MARGHAM	MARGHAM	مرغم	[]	28
676	14	KHOR KALBA	KHOR KALBA	خوركلبا	[]	29
677	14	DEBA	DEBA	دبا	["Daba", "Dibba", "Dibba Al Hisn"]	30
678	14	FUJAIRAH	FUJAIRAH	الفجيره	[]	31
679	14	SHAEM	SHAEM	شعم	["Shaam", "Sha'am"]	32
680	14	UMM AL QUWAIN	UMM AL QUWAIN	ام القيوين	["Umm Al Qaiwain", "Umm Al Quwain City"]	33
681	14	AL JUWAIS	AL JUWAIS	الجويس	[]	34
682	14	AL SIJI	AL SIJI	السيجى	[]	35
683	14	MEDEK	MEDEK	ميدك	[]	36
684	14	AL KHARAAN	AL KHARAAN	الخران	[]	37
685	14	MASAFI	MASAFI	مسافى	[]	38
686	14	AL QARYAH	AL QARYAH	القريه	[]	39
687	14	MURBEH	MURBEH	مربح	["Mirbah"]	40
688	14	WADI AL QOOR	WADI AL QOOR	وادى القور	[]	41
689	14	AL GHARFA	AL GHARFA	الغرفه	[]	42
690	14	WADI AL MUNAIAI	WADI AL MUNAIAI	وادى المنيعى	[]	43
691	14	WADI KOOB	WADI KOOB	وادى كوب	[]	44
692	14	WADI ALSIDR	WADI ALSIDR	وادي السدر	[]	45
693	14	DEBA FUJAIRAH	DEBA FUJAIRAH	دبا الفجيره	[]	46
694	14	RAS AL KHAIMAH	RAS AL KHAIMAH	راس الخيمه	[]	47
695	14	AL HADEEBAH/AL URAIBI	AL HADEEBAH/AL URAIBI	الحديبه/العريبي	[]	48
696	14	THANHA	THANHA	ظنحا	[]	49
697	14	ZAAB ISLAND	ZAAB ISLAND	جزيره الزعاب	["Zaab", "Jazirat Al Zaab"]	50
698	14	AL BIDYAH	AL BIDYAH	البديه	["Al Bidiya", "Al Bidya"]	51
699	14	WADI AL SHOKI	WADI AL SHOKI	وادى الشوكى	[]	52
700	14	GADFAA	GADFAA	قدفع	["Qidfa", "Qadfa"]	53
701	14	HABHAB	HABHAB	حبحب	[]	54
702	14	GHALILA	GHALILA	غليله	["Ghalilah"]	55
703	14	WADI ALABADLAH	WADI ALABADLAH	وادي العبادلة	[]	56
704	14	KHATT	KHATT	خت	[]	57
705	14	NAKHIL SHAML	NAKHIL SHAML	نخيل شمل	[]	58
706	14	WADI AL ABILI	WADI AL ABILI	وادى العبيلى	[]	59
707	14	KHOR KHUWAIR	KHOR KHUWAIR	خورخوير	[]	60
708	14	AL RAMS	AL RAMS	الرمس	[]	61
709	14	AL SEIH	AL SEIH	السيح	[]	62
710	14	AL FALIYA	AL FALIYA	الفليه	[]	63
711	14	AL QEER	AL QEER	القير	[]	64
712	14	AASMAH	AASMAH	اعسمه	["Al Asmah"]	65
713	14	SADROUH	SADROUH	سدروه	[]	66
714	14	AL HADITHA	AL HADITHA	الحديثه	[]	67
715	14	WADI ASFINI	WADI ASFINI	وادى اصفينى	[]	68
716	14	AL MUAREED	AL MUAREED	المعيريض	[]	69
717	14	AL HAMRANIYA	AL HAMRANIYA	الحمرانيه	[]	70
718	14	AL DIGDAGAH	AL DIGDAGAH	الدقداقه	[]	71
719	15	United Arab Emirates	United Arab Emirates	الإمارات العربية المتحدة	["uae nationals", "\\u0625\\u0645\\u0627\\u0631\\u0627\\u062a\\u064a\\u0648\\u0646", "\\u0625\\u0645\\u0627\\u0631\\u0627\\u062a\\u064a\\u064a\\u0646"]	0
720	15	India	India	الهند	["\\u0647\\u0646\\u0648\\u062f", "\\u0627\\u0644\\u0647\\u0646\\u0648\\u062f", "indians"]	1
721	15	Pakistan	Pakistan	باكستان	["\\u0628\\u0627\\u0643\\u0633\\u062a\\u0627\\u0646\\u064a\\u0648\\u0646", "\\u0628\\u0627\\u0643\\u0633\\u062a\\u0627\\u0646\\u064a\\u064a\\u0646", "pakistanis"]	2
722	15	Bangladesh	Bangladesh	بنغلاديش	["\\u0628\\u0646\\u063a\\u0627\\u0644\\u064a\\u0648\\u0646", "\\u0628\\u0646\\u063a\\u0627\\u0644\\u064a\\u064a\\u0646", "\\u0628\\u0646\\u063a\\u0644\\u0627\\u062f\\u064a\\u0634\\u064a\\u0648\\u0646", "bangladeshis"]	3
723	15	Philippines	Philippines	الفلبين	["\\u0641\\u0644\\u0628\\u064a\\u0646\\u064a\\u0648\\u0646", "\\u0641\\u0644\\u0628\\u064a\\u0646\\u064a\\u064a\\u0646", "filipinos"]	4
724	15	Egypt	Egypt	مصر	["\\u0645\\u0635\\u0631\\u064a\\u0648\\u0646", "\\u0645\\u0635\\u0631\\u064a\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u0635\\u0631\\u064a\\u064a\\u0646", "egyptians"]	5
725	15	Unknown	Unknown	غير معروفة	["unknown", "not recorded", "\\u063a\\u064a\\u0631 \\u0645\\u0639\\u0631\\u0648\\u0641", "\\u0645\\u062c\\u0647\\u0648\\u0644\\u0629"]	6
726	15	SRILANKAN	SRILANKAN	سيرلانكا	["sri lanka", "sri lankan", "sri lankans", "\\u0633\\u0631\\u064a\\u0644\\u0627\\u0646\\u0643\\u0627", "\\u0633\\u0631\\u064a\\u0644\\u0627\\u0646\\u0643\\u064a\\u0648\\u0646", "\\u0633\\u0631\\u064a\\u0644\\u0627\\u0646\\u0643\\u064a\\u064a\\u0646"]	7
727	15	Nepal	Nepal	نيبال	["\\u0646\\u064a\\u0628\\u0627\\u0644\\u064a\\u0648\\u0646", "\\u0646\\u064a\\u0628\\u0627\\u0644\\u064a\\u064a\\u0646", "nepalese"]	8
802	15	Algeria	Algeria	الجزائر	[]	83
803	15	Antigua and Barbuda	Antigua and Barbuda	أنتيغوا وبربودا	[]	84
728	15	Syrian Arab Republic	Syrian Arab Republic	الجمهورية العربية السورية	["syria", "syrians", "\\u0633\\u0648\\u0631\\u064a\\u0627", "\\u0633\\u0648\\u0631\\u064a\\u0648\\u0646", "\\u0633\\u0648\\u0631\\u064a\\u064a\\u0646"]	9
729	15	Jordan	Jordan	الأردن	["\\u0623\\u0631\\u062f\\u0646\\u064a\\u0648\\u0646", "\\u0623\\u0631\\u062f\\u0646\\u064a\\u064a\\u0646", "jordanians"]	10
730	15	Indonesia	Indonesia	إندونيسيا	["\\u0625\\u0646\\u062f\\u0648\\u0646\\u064a\\u0633\\u064a\\u0648\\u0646", "\\u0625\\u0646\\u062f\\u0648\\u0646\\u064a\\u0633\\u064a\\u064a\\u0646", "indonesians"]	11
731	15	United Kingdom	United Kingdom	المملكة المتحدة	["uk", "britain", "british", "\\u0628\\u0631\\u0637\\u0627\\u0646\\u064a\\u0648\\u0646", "\\u0628\\u0631\\u064a\\u0637\\u0627\\u0646\\u064a\\u064a\\u0646", "\\u0628\\u0631\\u064a\\u0637\\u0627\\u0646\\u064a\\u0627", "\\u0628\\u0631\\u064a\\u0637\\u0627\\u0646\\u064a\\u0648\\u0646"]	12
732	15	China	China	الصين	["\\u0635\\u064a\\u0646\\u064a\\u0648\\u0646", "\\u0635\\u064a\\u0646\\u064a\\u064a\\u0646", "chinese"]	13
733	15	Ethiopia	Ethiopia	إثيوبيا	["\\u0625\\u062b\\u064a\\u0648\\u0628\\u064a\\u0648\\u0646", "\\u0625\\u062b\\u064a\\u0648\\u0628\\u064a\\u064a\\u0646", "ethiopians"]	14
734	15	Morocco	Morocco	المغرب	["\\u0645\\u063a\\u0627\\u0631\\u0628\\u0629", "moroccans"]	15
735	15	United States of America	United States of America	الولايات المتحدة	["usa", "us", "america", "americans", "\\u0623\\u0645\\u0631\\u064a\\u0643\\u064a\\u0648\\u0646", "\\u0623\\u0645\\u0631\\u064a\\u0643\\u064a\\u064a\\u0646", "\\u0623\\u0645\\u0631\\u064a\\u0643\\u0627\\u0646"]	16
736	15	Kenya	Kenya	كينيا	["\\u0643\\u064a\\u0646\\u064a\\u0648\\u0646", "kenyans"]	17
737	15	Yemen	Yemen	اليمن	["\\u064a\\u0645\\u0646\\u064a\\u0648\\u0646", "\\u064a\\u0645\\u0646\\u064a\\u064a\\u0646", "yemenis"]	18
738	15	Nigeria	Nigeria	نيجيريا	["\\u0646\\u064a\\u062c\\u064a\\u0631\\u064a\\u0648\\u0646", "nigerians"]	19
739	15	Sudan	Sudan	السودان	["\\u0633\\u0648\\u062f\\u0627\\u0646\\u064a\\u0648\\u0646", "\\u0633\\u0648\\u062f\\u0627\\u0646\\u064a\\u064a\\u0646", "sudanese"]	20
740	15	Lebanon	Lebanon	لبنان	["\\u0644\\u0628\\u0646\\u0627\\u0646\\u064a\\u0648\\u0646", "\\u0644\\u0628\\u0646\\u0627\\u0646\\u064a\\u064a\\u0646", "lebanese"]	21
741	15	Finland	Finland	فنلندا	[]	22
742	15	Saint Lucia	Saint Lucia	سانت لوسيا	[]	23
743	15	Uruguay	Uruguay	أوروغواي	[]	24
744	15	Bhutan	Bhutan	بوتان	[]	25
745	15	Costa Rica	Costa Rica	كوستاريكا	[]	26
746	15	DOMINICAN	DOMINICAN	الدومنيكان	[]	27
747	15	El Salvador	El Salvador	السلفادور	[]	28
748	15	Gabon	Gabon	غابون	[]	29
749	15	Guinea-Bissau	Guinea-Bissau	غينيا بيساو	[]	30
750	15	Hungary	Hungary	هنغاريا	[]	31
751	15	Kazakhstan	Kazakhstan	كازاخستان	[]	32
752	15	Kiribati	Kiribati	كيريباتي	[]	33
753	15	Libya	Libya	ليبيا	[]	34
754	15	Macedonia	Macedonia	مقدونيا	[]	35
755	15	Moldova-	Moldova-	مولدوفا-	[]	36
756	15	Monaco	Monaco	موناكو	[]	37
757	15	Oman	Oman	سلطنة عمان	[]	38
758	15	Portugal	Portugal	البرتغال	[]	39
759	15	Saint Helena	Saint Helena	سانت هيلينا	[]	40
760	15	Sao Tome and Principe	Sao Tome and Principe	ساو تومي وبرينسيبي	[]	41
761	15	Slovenia	Slovenia	سلوفينيا	[]	42
762	15	Swaziland	Swaziland	سوازيلاند	[]	43
763	15	Angola	Angola	انجوليا	[]	44
764	15	Azerbaijan	Azerbaijan	أذربيجان	[]	45
765	15	Bermuda	Bermuda	برمودا	[]	46
766	15	Brazil	Brazil	البرازيل	[]	47
767	15	Bulgaria	Bulgaria	بلغاريا	[]	48
768	15	Burkina Faso	Burkina Faso	بوركينا فاسو	[]	49
769	15	COMMONWEALTH OF DOMINICA	COMMONWEALTH OF DOMINICA	كمنولث دومينكا	[]	50
770	15	Colombia	Colombia	كولومبيا	[]	51
771	15	Cote d'lvoire	Cote d'lvoire	كوت ديفوار(ساحل العاج)	[]	52
772	15	Croatia	Croatia	كرواتيا	[]	53
773	15	Denmark	Denmark	الدنمارك	[]	54
774	15	Estonia	Estonia	إستونيا	[]	55
775	15	Faroe Islands	Faroe Islands	جزر الفارو	[]	56
776	15	France	France	فرنسا	["\\u0641\\u0631\\u0646\\u0633\\u064a\\u0648\\u0646", "\\u0641\\u0631\\u0646\\u0633\\u064a\\u064a\\u0646"]	57
777	15	French Guiana	French Guiana	غيانا الفرنسية	[]	58
778	15	Guatemala	Guatemala	غواتيمالا	[]	59
779	15	Hong Kong	Hong Kong	هونغ كونغ	[]	60
780	15	Iceland	Iceland	ايسلندا	[]	61
781	15	Jamaica	Jamaica	جامايكا	[]	62
782	15	Maldives	Maldives	المالديف	[]	63
783	15	Marshall Islands	Marshall Islands	جزر مارشال	[]	64
784	15	Mauritius	Mauritius	موريشيوس	[]	65
785	15	Micronesia  Federated St.	Micronesia  Federated St.	ولايات ميكرونيزيا الموحدة	[]	66
786	15	Mongolia	Mongolia	منغوليا	[]	67
787	15	Niger	Niger	النيجر	[]	68
788	15	Papua New Guinea	Papua New Guinea	بابوا غينيا الجديدة	[]	69
789	15	Peru	Peru	بيرو	[]	70
790	15	Republic of Somaliland	Republic of Somaliland	جمهورية أرض الصومال	[]	71
791	15	Saint Kitts and Nevis	Saint Kitts and Nevis	سانت كيتس ونيفيس	[]	72
792	15	San Marino	San Marino	سان مارينو	[]	73
793	15	Serbia	Serbia	صربيا	[]	74
794	15	South Africa	South Africa	جنوب أفريقيا	[]	75
795	15	St Vincent and Grenadines	St Vincent and Grenadines	سانت فنسنت والجرينادينز	[]	76
796	15	Suriname	Suriname	سورينام	[]	77
797	15	Tanzania United Republic	Tanzania United Republic	جمهورية تنزانيا المتحدة	[]	78
798	15	Venezuela	Venezuela	فنزويلا	[]	79
799	15	"Palestine, State of"	"Palestine, State of"	فلسطين	[]	80
800	15	Afghanistan	Afghanistan	افغانستان	[]	81
801	15	Albania	Albania	البانيا	[]	82
804	15	Barbados	Barbados	بربادوس	[]	85
805	15	Belgium	Belgium	بلجيكا	[]	86
806	15	Belize	Belize	بليز	[]	87
807	15	Bosnia and Herzegovina	Bosnia and Herzegovina	البوسنه والهرسك	[]	88
808	15	Brunei Darussalam	Brunei Darussalam	بروناي دار السلام	[]	89
809	15	Canada	Canada	كندا	[]	90
810	15	Cayman Islands	Cayman Islands	جزر كايمن	[]	91
811	15	Chad	Chad	تشاد	[]	92
812	15	Comoros	Comoros	جزر القمر	[]	93
813	15	Congo	Congo	الكونغو	[]	94
814	15	Cuba	Cuba	كوبا	[]	95
815	15	Democratic Rep. of Congo	Democratic Rep. of Congo	جمهورية كونغوالديمقراطية	[]	96
816	15	Ecuador	Ecuador	الاكوادور	[]	97
817	15	Equatorial Guinea	Equatorial Guinea	غينيا الاستوائية	[]	98
818	15	Eritrea	Eritrea	إريتريا	[]	99
819	15	Fiji	Fiji	فيجي	[]	100
820	15	Gambia	Gambia	غامبيا	[]	101
821	15	Georgia	Georgia	جورجيا	[]	102
822	15	Germany	Germany	المانيا	["\\u0623\\u0644\\u0645\\u0627\\u0646", "germans"]	103
823	15	Greece	Greece	اليونان	[]	104
824	15	Greenland	Greenland	جرينلاند	[]	105
825	15	Grenada	Grenada	غرينادا	[]	106
826	15	Haiti	Haiti	هايتي	[]	107
827	15	Holy See (Vatican)	Holy See (Vatican)	الفاتيكان	[]	108
828	15	Iraq	Iraq	العراق	[]	109
829	15	Ireland	Ireland	ايرلندا	[]	110
830	15	Japan	Japan	اليابان	[]	111
831	15	Kosovo	Kosovo	كوسوفو	[]	112
832	15	Kuwait	Kuwait	الكويت	[]	113
833	15	Lao People's Democratic	Lao People's Democratic	جمهورية لاو الديمقراطية	[]	114
834	15	Lesotho	Lesotho	ليسوتو	[]	115
835	15	Liberia	Liberia	ليبيريا	[]	116
836	15	Liechtenstein	Liechtenstein	ليختنشتاين	[]	117
837	15	Luxembourg	Luxembourg	لوكسمبورج	[]	118
838	15	Malaysia	Malaysia	ماليزيا	[]	119
839	15	Mali	Mali	مالي	[]	120
840	15	Martinique	Martinique	مارتينيك	[]	121
841	15	Moldova  Republic of	Moldova  Republic of	جمهورية مولدوفا	[]	122
842	15	Montenegro	Montenegro	مونتينيجرو	[]	123
843	15	Mozambique	Mozambique	موزمبيق	[]	124
844	15	Myanmar	Myanmar	ميانمار	[]	125
845	15	Nauru	Nauru	ناورو	[]	126
846	15	New Zealand	New Zealand	نيوزيلاندا	[]	127
847	15	North Korea Democratic R.	North Korea Democratic R.	جمهورية كوريا الشمالية	["north korea", "\\u0643\\u0648\\u0631\\u064a\\u0627 \\u0627\\u0644\\u0634\\u0645\\u0627\\u0644\\u064a\\u0629"]	128
848	15	Northern Mariana Islands	Northern Mariana Islands	جزر ماريانا الشمالية	[]	129
849	15	Norway	Norway	النرويج	[]	130
850	15	Palau	Palau	بالاو	[]	131
851	15	Panama	Panama	بنما	[]	132
852	15	Poland	Poland	بولندا	[]	133
853	15	Puerto Rico	Puerto Rico	بورتوريكو	[]	134
854	15	Romania	Romania	رومانيا	[]	135
855	15	Russian Federation	Russian Federation	الاتحاد الروسي	["russia", "russians", "\\u0631\\u0648\\u0633\\u064a\\u0627", "\\u0631\\u0648\\u0633"]	136
856	15	Samoa	Samoa	ساموا	[]	137
857	15	Saudi Arabia	Saudi Arabia	السعوديه	["ksa", "saudi", "saudis", "\\u0633\\u0639\\u0648\\u062f\\u064a\\u0648\\u0646", "\\u0633\\u0639\\u0648\\u062f\\u064a\\u064a\\u0646"]	138
858	15	Senegal	Senegal	السنغال	[]	139
859	15	Seychelles	Seychelles	سيشيل	[]	140
860	15	Sierra Leone	Sierra Leone	سيراليون	[]	141
861	15	Solomon Islands	Solomon Islands	جزر سولومون	[]	142
862	15	Somalia	Somalia	الصومال	[]	143
863	15	South Korea  Republic of	South Korea  Republic of	جمهورية كوريا الجنوبية	["south korea", "south koreans", "\\u0643\\u0648\\u0631\\u064a\\u0627 \\u0627\\u0644\\u062c\\u0646\\u0648\\u0628\\u064a\\u0629"]	144
864	15	South Sudan	South Sudan	جنوب السودان	[]	145
865	15	Spain	Spain	اسبانيا	[]	146
866	15	Tajikistan	Tajikistan	طاجكستان	[]	147
867	15	Togo	Togo	توغو	[]	148
868	15	Trinidad and Tobago	Trinidad and Tobago	ترينيداد وتوباغو	[]	149
869	15	Turkey	Turkey	تركيا	["\\u0623\\u062a\\u0631\\u0627\\u0643", "turks", "turkish"]	150
870	15	Tuvalu	Tuvalu	توفالو	[]	151
871	15	Ukraine	Ukraine	أوكرانيا	[]	152
872	15	Uzbekistan	Uzbekistan	أوزبكستان	[]	153
873	15	Vanuatu	Vanuatu	فانواتو	[]	154
874	15	Viet Nam	Viet Nam	فيتنام	["vietnam", "\\u0641\\u064a\\u062a\\u0646\\u0627\\u0645"]	155
\.


--
-- Data for Name: glossary_term; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.glossary_term (id, term, term_ar, definition, definition_ar, synonyms, synonyms_ar, links) FROM stdin;
\.


--
-- Data for Name: login_attempt; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.login_attempt (id, email, at) FROM stdin;
\.


--
-- Data for Name: metric; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.metric (id, name, name_ar, description, description_ar, sql_expression, base_table_id, filters, allowed_dimensions, synonyms, synonyms_ar, owner, status) FROM stdin;
3	tribe_count	\N	How many DISTINCT tribes are recorded — NOTE: the count includes the administrative categories ("No Tribe", "Unknown", "Non Confirmed Tribes") because they are stored values; say so if asked precisely. Tribes exist for UAE CITIZENS only, so the count naturally covers citizens (rows without a recorded tribe are not counted). Use for "how many tribes" questions — NOT for counting people (population_count) and NOT for listing tribes (population_count grouped by tribe).	عدد القبائل المختلفة المسجلة. القبائل خاصة بمواطني الدولة فقط. يُستخدم لأسئلة "كم قبيلة" — وليس لعدّ الأشخاص.	COUNT(DISTINCT citi_tribe_en)	1	\N	["person_category", "person_subcategory", "gender", "age_group", "emirate", "is_currently_inside", "is_born_inside", "citizen_area"]	["tribes", "distinct tribes"]	["\\u0639\\u062f\\u062f \\u0627\\u0644\\u0642\\u0628\\u0627\\u0626\\u0644", "\\u0643\\u0645 \\u0642\\u0628\\u064a\\u0644\\u0629", "\\u0642\\u0628\\u0627\\u0626\\u0644"]	\N	published
1	population_count	\N	Number of individuals currently in the UAE population — citizens, residents (expats), GCC nationals, and visitors. A CURRENT snapshot: there is no historical time axis, so time-based questions do not apply. Filter person_category to count a single group (e.g. only citizens).	عدد الأفراد الحاليين في سكان دولة الإمارات — المواطنون والمقيمون والخليجيون والزوار. لقطة حالية بدون محور زمني.	SUM(population_cnt)	1	\N	["person_category", "person_subcategory", "nationality", "gender", "age_group", "emirate", "is_born_inside", "is_currently_inside", "profession_base", "job_classification", "sponsor_category", "destination_country", "tribe", "citizen_area", "previous_nationality"]	["population", "people", "individuals", "headcount", "citizens", "residents", "expats", "visitors", "demographics"]	["\\u0627\\u0644\\u0633\\u0643\\u0627\\u0646", "\\u0639\\u062f\\u062f \\u0627\\u0644\\u0633\\u0643\\u0627\\u0646", "\\u0627\\u0644\\u0623\\u0641\\u0631\\u0627\\u062f", "\\u0627\\u0644\\u062a\\u0639\\u062f\\u0627\\u062f", "\\u0627\\u0644\\u0645\\u0648\\u0627\\u0637\\u0646\\u0648\\u0646", "\\u0627\\u0644\\u0645\\u0642\\u064a\\u0645\\u0648\\u0646", "\\u0627\\u0644\\u0632\\u0648\\u0627\\u0631", "\\u0627\\u0644\\u062a\\u0631\\u0643\\u064a\\u0628\\u0629 \\u0627\\u0644\\u0633\\u0643\\u0627\\u0646\\u064a\\u0629", "\\u0627\\u0644\\u062f\\u064a\\u0645\\u0648\\u063a\\u0631\\u0627\\u0641\\u064a\\u0627"]	\N	published
2	nationality_count	\N	How many DISTINCT nationalities are present in the registry (optionally within a filtered group). Use for "how many nationalities" questions — NOT for counting people (that is population_count).	عدد الجنسيات المختلفة الموجودة في السجل (ويمكن حصرها ضمن فئة). يُستخدم لأسئلة "كم جنسية" — وليس لعدّ الأشخاص.	COUNT(DISTINCT nationality_en)	1	\N	["person_category", "person_subcategory", "gender", "age_group", "emirate", "is_currently_inside", "is_born_inside", "job_classification", "sponsor_category"]	["nationalities", "distinct nationalities"]	["\\u0639\\u062f\\u062f \\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0627\\u062a", "\\u0643\\u0645 \\u062c\\u0646\\u0633\\u064a\\u0629"]		published
\.


--
-- Data for Name: profile; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.profile (id, column_id, null_fraction, distinct_count, min_value, max_value, top_values, profiled_at) FROM stdin;
\.


--
-- Data for Name: relationship; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.relationship (id, from_column_id, to_column_id, cardinality, join_type, description) FROM stdin;
\.


--
-- Data for Name: sample_query; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.sample_query (id, question, sql, tables, verified) FROM stdin;
\.


--
-- Data for Name: schema_meta; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.schema_meta (id, source_id, name, display_name, display_name_ar, description, description_ar, domain, owner) FROM stdin;
1	1	demographics	\N	\N	\N	\N	\N	\N
2	1	sales	\N	\N	\N	\N	\N	\N
\.


--
-- Data for Name: source; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.source (id, name, kind, config, last_synced_at) FROM stdin;
1	datalake	trino	{"host": "localhost", "port": 8080, "catalog": "lake", "user": "catalog", "http_scheme": "http"}	2026-10-25 18:34:13.7163+00
\.


--
-- Data for Name: table; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."table" (id, source_id, schema_name, name, table_format, location, partitioned_by, row_count, removed, needs_review, display_name, description, grain, table_type, domain, owner, refresh_cadence, usage_notes, caveats, display_name_ar, description_ar, grain_ar, usage_notes_ar, caveats_ar, pii_level, certified, status, version) FROM stdin;
1	1	demographics	population_f	iceberg	s3://warehouse/demographics/population_f-f9bdd28278914c078cdc885a1976216b	[]	173724	f	t	\N	Current snapshot of individuals in the UAE population — citizens, residents (expats), GCC nationals and visitors. Each row is a pre-aggregated count of individuals sharing one combination of demographic dimension values within a person category; population_cnt must be SUMmed, never counted with COUNT(*). No time axis — historical questions do not apply.	One row per unique combination of demographic dimension values (nationality, emirate, gender, age group, job, sponsor, etc.) within one person_category — not one row per person. population_cnt holds the count of individuals in that combination.	fact	demographics	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	t	published	3
2	1	sales	dim_customer	iceberg	s3://warehouse/sales/dim_customer-c3023c9315e044db99e14ae3c891dc4b	[]	2	f	t	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	f	draft	0
3	1	sales	dim_date	iceberg	s3://warehouse/sales/dim_date-61d86265c4ec41ff88c3e6978764d315	[]	2	f	t	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	f	draft	0
4	1	sales	dim_product	iceberg	s3://warehouse/sales/dim_product-480e01096b18421ea262640ebea95c62	[]	2	f	t	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	f	draft	0
5	1	sales	fact_orders	iceberg	s3://warehouse/sales/fact_orders-65fbed5776c14a46b66158cb9117a705	["month(order_date)"]	2	f	t	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	f	draft	0
\.


--
-- Data for Name: table_revision; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.table_revision (id, table_id, number, status, changes, diff, snapshot, message, created_by, contributors, created_at, updated_at, published_by, published_at) FROM stdin;
1	1	1	published	{}	[]	{"table": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "grain": null, "grain_ar": null, "table_type": "fact", "domain": "demographics", "owner": null, "refresh_cadence": null, "usage_notes": null, "usage_notes_ar": null, "caveats": null, "caveats_ar": null, "pii_level": null, "certified": true}, "columns": {"population_cnt": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "nat_iso_code": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "nationality_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "nationality_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "gender_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "gender_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "is_born_inside": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "age_group": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "emirate_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "emirate_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prof_base_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prof_base_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prof_cat_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prof_cat_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "job_level_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "job_level_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "is_cur_inside": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "last_known_des_cntry_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "last_known_des_cntry_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prsn_cat_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prsn_cat_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prsn_sub_cat_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prsn_sub_cat_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "spon_cat_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "spon_cat_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "citi_tribe_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "citi_tribe_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "citi_prv_nat_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "citi_prv_nat_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "cit_desc_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "cit_desc_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}}}	Published	iris009147@gmail.com	["iris009147@gmail.com"]	2026-10-25 12:15:43.754028+00	2026-10-25 12:15:43.75403+00	iris009147@gmail.com	2026-10-25 12:15:43.752742+00
2	1	2	published	{"table": {"description": "Current snapshot of individuals in the UAE population \\u2014 citizens, residents (expats), GCC nationals and visitors. Each row is a pre-aggregated count of individuals sharing one combination of demographic dimension values within a person category; population_cnt must be SUMmed, never counted with COUNT(*). No time axis \\u2014 historical questions do not apply.", "grain": "One row per unique combination of demographic dimension values (nationality, emirate, gender, age group, job, sponsor, etc.) within one person_category \\u2014 not one row per person. population_cnt holds the count of individuals in that combination."}, "columns": {"prsn_cat_en": {"synonyms": ["category", "Person category"]}, "prsn_sub_cat_en": {"synonyms": ["subcategory", "residency type", "visa type", "citizenship type", "Person subcategory"]}, "nationality_en": {"synonyms": ["nationality", "nationalities"]}, "gender_en": {"synonyms": ["gender", "sex"]}, "age_group": {"synonyms": ["age", "age band", "age bracket", "age range", "age group"]}, "emirate_en": {"synonyms": ["emirate", "city", "region"]}, "is_born_inside": {"synonyms": ["birthplace", "place of birth", "born inside", "born outside", "Born inside country"]}, "is_cur_inside": {"synonyms": ["presence", "currently inside", "currently outside", "Currently inside country"]}, "prof_base_en": {"synonyms": ["job", "occupation", "profession", "job title"]}, "job_level_en": {"synonyms": ["job classification", "occupational level", "skill level", "job level", "workforce level"]}, "spon_cat_en": {"synonyms": ["sponsor", "sponsorship", "sponsored", "Sponsor category"]}, "last_known_des_cntry_en": {"synonyms": ["destination", "destination country", "Last known destination country"]}, "citi_tribe_en": {"synonyms": ["tribe", "family", "clan", "family name"]}, "cit_desc_en": {"synonyms": ["registry area", "area of registration", "place of registration", "area of origin", "khulasat al qaid", "registry district"]}, "citi_prv_nat_en": {"synonyms": ["previous nationality", "former nationality", "original nationality", "naturalized", "naturalised", "naturalization"]}, "population_cnt": {"synonyms": ["population", "population count", "headcount", "count"]}}}	[{"scope": "table", "column": null, "field": "description", "old": null, "new": "Current snapshot of individuals in the UAE population \\u2014 citizens, residents (expats), GCC nationals and visitors. Each row is a pre-aggregated count of individuals sharing one combination of demographic dimension values within a person category; population_cnt must be SUMmed, never counted with COUNT(*). No time axis \\u2014 historical questions do not apply."}, {"scope": "table", "column": null, "field": "grain", "old": null, "new": "One row per unique combination of demographic dimension values (nationality, emirate, gender, age group, job, sponsor, etc.) within one person_category \\u2014 not one row per person. population_cnt holds the count of individuals in that combination."}, {"scope": "column", "column": "population_cnt", "field": "synonyms", "old": [], "new": ["population", "population count", "headcount", "count"]}, {"scope": "column", "column": "nationality_en", "field": "synonyms", "old": [], "new": ["nationality", "nationalities"]}, {"scope": "column", "column": "gender_en", "field": "synonyms", "old": [], "new": ["gender", "sex"]}, {"scope": "column", "column": "is_born_inside", "field": "synonyms", "old": [], "new": ["birthplace", "place of birth", "born inside", "born outside", "Born inside country"]}, {"scope": "column", "column": "age_group", "field": "synonyms", "old": [], "new": ["age", "age band", "age bracket", "age range", "age group"]}, {"scope": "column", "column": "emirate_en", "field": "synonyms", "old": [], "new": ["emirate", "city", "region"]}, {"scope": "column", "column": "prof_base_en", "field": "synonyms", "old": [], "new": ["job", "occupation", "profession", "job title"]}, {"scope": "column", "column": "job_level_en", "field": "synonyms", "old": [], "new": ["job classification", "occupational level", "skill level", "job level", "workforce level"]}, {"scope": "column", "column": "is_cur_inside", "field": "synonyms", "old": [], "new": ["presence", "currently inside", "currently outside", "Currently inside country"]}, {"scope": "column", "column": "last_known_des_cntry_en", "field": "synonyms", "old": [], "new": ["destination", "destination country", "Last known destination country"]}, {"scope": "column", "column": "prsn_cat_en", "field": "synonyms", "old": [], "new": ["category", "Person category"]}, {"scope": "column", "column": "prsn_sub_cat_en", "field": "synonyms", "old": [], "new": ["subcategory", "residency type", "visa type", "citizenship type", "Person subcategory"]}, {"scope": "column", "column": "spon_cat_en", "field": "synonyms", "old": [], "new": ["sponsor", "sponsorship", "sponsored", "Sponsor category"]}, {"scope": "column", "column": "citi_tribe_en", "field": "synonyms", "old": [], "new": ["tribe", "family", "clan", "family name"]}, {"scope": "column", "column": "citi_prv_nat_en", "field": "synonyms", "old": [], "new": ["previous nationality", "former nationality", "original nationality", "naturalized", "naturalised", "naturalization"]}, {"scope": "column", "column": "cit_desc_en", "field": "synonyms", "old": [], "new": ["registry area", "area of registration", "place of registration", "area of origin", "khulasat al qaid", "registry district"]}]	{"table": {"display_name": null, "display_name_ar": null, "description": "Current snapshot of individuals in the UAE population \\u2014 citizens, residents (expats), GCC nationals and visitors. Each row is a pre-aggregated count of individuals sharing one combination of demographic dimension values within a person category; population_cnt must be SUMmed, never counted with COUNT(*). No time axis \\u2014 historical questions do not apply.", "description_ar": null, "grain": "One row per unique combination of demographic dimension values (nationality, emirate, gender, age group, job, sponsor, etc.) within one person_category \\u2014 not one row per person. population_cnt holds the count of individuals in that combination.", "grain_ar": null, "table_type": "fact", "domain": "demographics", "owner": null, "refresh_cadence": null, "usage_notes": null, "usage_notes_ar": null, "caveats": null, "caveats_ar": null, "pii_level": null, "certified": true}, "columns": {"population_cnt": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["population", "population count", "headcount", "count"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "nat_iso_code": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "nationality_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["nationality", "nationalities"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "nationality_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "gender_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["gender", "sex"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "gender_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "is_born_inside": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["birthplace", "place of birth", "born inside", "born outside", "Born inside country"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "age_group": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["age", "age band", "age bracket", "age range", "age group"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "emirate_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["emirate", "city", "region"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "emirate_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prof_base_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["job", "occupation", "profession", "job title"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prof_base_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prof_cat_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prof_cat_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "job_level_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["job classification", "occupational level", "skill level", "job level", "workforce level"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "job_level_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "is_cur_inside": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["presence", "currently inside", "currently outside", "Currently inside country"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "last_known_des_cntry_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["destination", "destination country", "Last known destination country"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "last_known_des_cntry_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prsn_cat_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["category", "Person category"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prsn_cat_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prsn_sub_cat_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["subcategory", "residency type", "visa type", "citizenship type", "Person subcategory"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prsn_sub_cat_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "spon_cat_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["sponsor", "sponsorship", "sponsored", "Sponsor category"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "spon_cat_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "citi_tribe_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["tribe", "family", "clan", "family name"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "citi_tribe_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "citi_prv_nat_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["previous nationality", "former nationality", "original nationality", "naturalized", "naturalised", "naturalization"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "citi_prv_nat_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "cit_desc_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "cit_desc_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["registry area", "area of registration", "place of registration", "area of origin", "khulasat al qaid", "registry district"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}}}	Semantic import: dimensions, metrics, descriptions, synonyms	import:population.yaml	["import:population.yaml"]	2026-10-25 14:06:07.467264+00	2026-10-25 14:06:07.489114+00	import:population.yaml	2026-10-25 14:06:07.497011+00
3	1	3	published	{"table": {}, "columns": {"prsn_cat_en": {"synonyms_ar": ["\\u0641\\u0626\\u0629", "\\u0627\\u0644\\u0641\\u0626\\u0629", "\\u0641\\u0626\\u0629 \\u0627\\u0644\\u0634\\u062e\\u0635"]}, "prsn_sub_cat_en": {"synonyms_ar": ["\\u0646\\u0648\\u0639 \\u0627\\u0644\\u0627\\u0642\\u0627\\u0645\\u0629", "\\u0646\\u0648\\u0639 \\u0627\\u0644\\u062a\\u0623\\u0634\\u064a\\u0631\\u0629", "\\u0627\\u0644\\u0641\\u0626\\u0629 \\u0627\\u0644\\u0641\\u0631\\u0639\\u064a\\u0629"]}, "nationality_en": {"synonyms_ar": ["\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0629", "\\u062c\\u0646\\u0633\\u064a\\u0629", "\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0627\\u062a"]}, "gender_en": {"synonyms_ar": ["\\u0627\\u0644\\u062c\\u0646\\u0633", "\\u0627\\u0644\\u0646\\u0648\\u0639"]}, "age_group": {"synonyms_ar": ["\\u0627\\u0644\\u0639\\u0645\\u0631", "\\u0627\\u0644\\u0633\\u0646", "\\u0627\\u0644\\u0623\\u0639\\u0645\\u0627\\u0631", "\\u0627\\u0644\\u0641\\u0626\\u0629 \\u0627\\u0644\\u0639\\u0645\\u0631\\u064a\\u0629"]}, "emirate_en": {"synonyms_ar": ["\\u0627\\u0644\\u0625\\u0645\\u0627\\u0631\\u0629", "\\u0625\\u0645\\u0627\\u0631\\u0629", "\\u0627\\u0644\\u0645\\u062f\\u064a\\u0646\\u0629"]}, "is_born_inside": {"synonyms_ar": ["\\u0645\\u0643\\u0627\\u0646 \\u0627\\u0644\\u0648\\u0644\\u0627\\u062f\\u0629", "\\u0645\\u0643\\u0627\\u0646 \\u0627\\u0644\\u0645\\u064a\\u0644\\u0627\\u062f"]}, "is_cur_inside": {"synonyms_ar": ["\\u0627\\u0644\\u062a\\u0648\\u0627\\u062c\\u062f", "\\u0627\\u0644\\u062d\\u0636\\u0648\\u0631", "\\u0627\\u0644\\u062a\\u0648\\u0627\\u062c\\u062f \\u0627\\u0644\\u062d\\u0627\\u0644\\u064a"]}, "prof_base_en": {"synonyms_ar": ["\\u0627\\u0644\\u0645\\u0647\\u0646\\u0629", "\\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u0629", "\\u0627\\u0644\\u0645\\u0633\\u0645\\u0649 \\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u064a"]}, "job_level_en": {"synonyms_ar": ["\\u062a\\u0635\\u0646\\u064a\\u0641 \\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u0629", "\\u0627\\u0644\\u0645\\u0633\\u062a\\u0648\\u0649 \\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u064a", "\\u0645\\u0633\\u062a\\u0648\\u0649 \\u0627\\u0644\\u0645\\u0647\\u0627\\u0631\\u0629"]}, "spon_cat_en": {"synonyms_ar": ["\\u0627\\u0644\\u0643\\u0641\\u064a\\u0644", "\\u0627\\u0644\\u0643\\u0641\\u0627\\u0644\\u0629", "\\u0627\\u0644\\u0645\\u0643\\u0641\\u0648\\u0644\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u0643\\u0641\\u0648\\u0644\\u0648\\u0646", "\\u0641\\u0626\\u0629 \\u0627\\u0644\\u0643\\u0641\\u064a\\u0644"]}, "last_known_des_cntry_en": {"synonyms_ar": ["\\u0627\\u0644\\u0648\\u062c\\u0647\\u0629", "\\u0628\\u0644\\u062f \\u0627\\u0644\\u0648\\u062c\\u0647\\u0629", "\\u0628\\u0644\\u062f \\u0627\\u0644\\u0648\\u062c\\u0647\\u0629 \\u0627\\u0644\\u0623\\u062e\\u064a\\u0631\\u0629"]}, "citi_tribe_en": {"synonyms_ar": ["\\u0627\\u0644\\u0642\\u0628\\u064a\\u0644\\u0629", "\\u0627\\u0644\\u0639\\u0627\\u0626\\u0644\\u0629", "\\u0627\\u0644\\u0641\\u062e\\u0630"]}, "cit_desc_en": {"synonyms_ar": ["\\u062e\\u0644\\u0627\\u0635\\u0629 \\u0627\\u0644\\u0642\\u064a\\u062f", "\\u0645\\u0646\\u0637\\u0642\\u0629 \\u0627\\u0644\\u0642\\u064a\\u062f", "\\u0645\\u0646\\u0637\\u0642\\u0629 \\u062e\\u0644\\u0627\\u0635\\u0629 \\u0627\\u0644\\u0642\\u064a\\u062f", "\\u0645\\u0646\\u0637\\u0642\\u0629 \\u0627\\u0644\\u0623\\u0635\\u0644", "\\u0627\\u0644\\u0645\\u0642\\u064a\\u062f\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u0642\\u064a\\u062f\\u0648\\u0646", "\\u0645\\u0642\\u064a\\u062f"]}, "citi_prv_nat_en": {"synonyms_ar": ["\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0629 \\u0627\\u0644\\u0633\\u0627\\u0628\\u0642\\u0629", "\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0629 \\u0627\\u0644\\u0623\\u0635\\u0644\\u064a\\u0629", "\\u0627\\u0644\\u0645\\u062a\\u062c\\u0646\\u0633\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u062a\\u062c\\u0646\\u0633\\u0648\\u0646", "\\u0645\\u062a\\u062c\\u0646\\u0633\\u064a\\u0646", "\\u0627\\u0644\\u062a\\u062c\\u0646\\u0633"]}}}	[{"scope": "column", "column": "nationality_en", "field": "synonyms_ar", "old": [], "new": ["\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0629", "\\u062c\\u0646\\u0633\\u064a\\u0629", "\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0627\\u062a"]}, {"scope": "column", "column": "gender_en", "field": "synonyms_ar", "old": [], "new": ["\\u0627\\u0644\\u062c\\u0646\\u0633", "\\u0627\\u0644\\u0646\\u0648\\u0639"]}, {"scope": "column", "column": "is_born_inside", "field": "synonyms_ar", "old": [], "new": ["\\u0645\\u0643\\u0627\\u0646 \\u0627\\u0644\\u0648\\u0644\\u0627\\u062f\\u0629", "\\u0645\\u0643\\u0627\\u0646 \\u0627\\u0644\\u0645\\u064a\\u0644\\u0627\\u062f"]}, {"scope": "column", "column": "age_group", "field": "synonyms_ar", "old": [], "new": ["\\u0627\\u0644\\u0639\\u0645\\u0631", "\\u0627\\u0644\\u0633\\u0646", "\\u0627\\u0644\\u0623\\u0639\\u0645\\u0627\\u0631", "\\u0627\\u0644\\u0641\\u0626\\u0629 \\u0627\\u0644\\u0639\\u0645\\u0631\\u064a\\u0629"]}, {"scope": "column", "column": "emirate_en", "field": "synonyms_ar", "old": [], "new": ["\\u0627\\u0644\\u0625\\u0645\\u0627\\u0631\\u0629", "\\u0625\\u0645\\u0627\\u0631\\u0629", "\\u0627\\u0644\\u0645\\u062f\\u064a\\u0646\\u0629"]}, {"scope": "column", "column": "prof_base_en", "field": "synonyms_ar", "old": [], "new": ["\\u0627\\u0644\\u0645\\u0647\\u0646\\u0629", "\\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u0629", "\\u0627\\u0644\\u0645\\u0633\\u0645\\u0649 \\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u064a"]}, {"scope": "column", "column": "job_level_en", "field": "synonyms_ar", "old": [], "new": ["\\u062a\\u0635\\u0646\\u064a\\u0641 \\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u0629", "\\u0627\\u0644\\u0645\\u0633\\u062a\\u0648\\u0649 \\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u064a", "\\u0645\\u0633\\u062a\\u0648\\u0649 \\u0627\\u0644\\u0645\\u0647\\u0627\\u0631\\u0629"]}, {"scope": "column", "column": "is_cur_inside", "field": "synonyms_ar", "old": [], "new": ["\\u0627\\u0644\\u062a\\u0648\\u0627\\u062c\\u062f", "\\u0627\\u0644\\u062d\\u0636\\u0648\\u0631", "\\u0627\\u0644\\u062a\\u0648\\u0627\\u062c\\u062f \\u0627\\u0644\\u062d\\u0627\\u0644\\u064a"]}, {"scope": "column", "column": "last_known_des_cntry_en", "field": "synonyms_ar", "old": [], "new": ["\\u0627\\u0644\\u0648\\u062c\\u0647\\u0629", "\\u0628\\u0644\\u062f \\u0627\\u0644\\u0648\\u062c\\u0647\\u0629", "\\u0628\\u0644\\u062f \\u0627\\u0644\\u0648\\u062c\\u0647\\u0629 \\u0627\\u0644\\u0623\\u062e\\u064a\\u0631\\u0629"]}, {"scope": "column", "column": "prsn_cat_en", "field": "synonyms_ar", "old": [], "new": ["\\u0641\\u0626\\u0629", "\\u0627\\u0644\\u0641\\u0626\\u0629", "\\u0641\\u0626\\u0629 \\u0627\\u0644\\u0634\\u062e\\u0635"]}, {"scope": "column", "column": "prsn_sub_cat_en", "field": "synonyms_ar", "old": [], "new": ["\\u0646\\u0648\\u0639 \\u0627\\u0644\\u0627\\u0642\\u0627\\u0645\\u0629", "\\u0646\\u0648\\u0639 \\u0627\\u0644\\u062a\\u0623\\u0634\\u064a\\u0631\\u0629", "\\u0627\\u0644\\u0641\\u0626\\u0629 \\u0627\\u0644\\u0641\\u0631\\u0639\\u064a\\u0629"]}, {"scope": "column", "column": "spon_cat_en", "field": "synonyms_ar", "old": [], "new": ["\\u0627\\u0644\\u0643\\u0641\\u064a\\u0644", "\\u0627\\u0644\\u0643\\u0641\\u0627\\u0644\\u0629", "\\u0627\\u0644\\u0645\\u0643\\u0641\\u0648\\u0644\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u0643\\u0641\\u0648\\u0644\\u0648\\u0646", "\\u0641\\u0626\\u0629 \\u0627\\u0644\\u0643\\u0641\\u064a\\u0644"]}, {"scope": "column", "column": "citi_tribe_en", "field": "synonyms_ar", "old": [], "new": ["\\u0627\\u0644\\u0642\\u0628\\u064a\\u0644\\u0629", "\\u0627\\u0644\\u0639\\u0627\\u0626\\u0644\\u0629", "\\u0627\\u0644\\u0641\\u062e\\u0630"]}, {"scope": "column", "column": "citi_prv_nat_en", "field": "synonyms_ar", "old": [], "new": ["\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0629 \\u0627\\u0644\\u0633\\u0627\\u0628\\u0642\\u0629", "\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0629 \\u0627\\u0644\\u0623\\u0635\\u0644\\u064a\\u0629", "\\u0627\\u0644\\u0645\\u062a\\u062c\\u0646\\u0633\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u062a\\u062c\\u0646\\u0633\\u0648\\u0646", "\\u0645\\u062a\\u062c\\u0646\\u0633\\u064a\\u0646", "\\u0627\\u0644\\u062a\\u062c\\u0646\\u0633"]}, {"scope": "column", "column": "cit_desc_en", "field": "synonyms_ar", "old": [], "new": ["\\u062e\\u0644\\u0627\\u0635\\u0629 \\u0627\\u0644\\u0642\\u064a\\u062f", "\\u0645\\u0646\\u0637\\u0642\\u0629 \\u0627\\u0644\\u0642\\u064a\\u062f", "\\u0645\\u0646\\u0637\\u0642\\u0629 \\u062e\\u0644\\u0627\\u0635\\u0629 \\u0627\\u0644\\u0642\\u064a\\u062f", "\\u0645\\u0646\\u0637\\u0642\\u0629 \\u0627\\u0644\\u0623\\u0635\\u0644", "\\u0627\\u0644\\u0645\\u0642\\u064a\\u062f\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u0642\\u064a\\u062f\\u0648\\u0646", "\\u0645\\u0642\\u064a\\u062f"]}]	{"table": {"display_name": null, "display_name_ar": null, "description": "Current snapshot of individuals in the UAE population \\u2014 citizens, residents (expats), GCC nationals and visitors. Each row is a pre-aggregated count of individuals sharing one combination of demographic dimension values within a person category; population_cnt must be SUMmed, never counted with COUNT(*). No time axis \\u2014 historical questions do not apply.", "description_ar": null, "grain": "One row per unique combination of demographic dimension values (nationality, emirate, gender, age group, job, sponsor, etc.) within one person_category \\u2014 not one row per person. population_cnt holds the count of individuals in that combination.", "grain_ar": null, "table_type": "fact", "domain": "demographics", "owner": null, "refresh_cadence": null, "usage_notes": null, "usage_notes_ar": null, "caveats": null, "caveats_ar": null, "pii_level": null, "certified": true}, "columns": {"population_cnt": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["population", "population count", "headcount", "count"], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "nat_iso_code": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "nationality_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["nationality", "nationalities"], "synonyms_ar": ["\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0629", "\\u062c\\u0646\\u0633\\u064a\\u0629", "\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0627\\u062a"], "is_primary_key": false, "pii": false, "deprecated": false}, "nationality_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "gender_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["gender", "sex"], "synonyms_ar": ["\\u0627\\u0644\\u062c\\u0646\\u0633", "\\u0627\\u0644\\u0646\\u0648\\u0639"], "is_primary_key": false, "pii": false, "deprecated": false}, "gender_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "is_born_inside": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["birthplace", "place of birth", "born inside", "born outside", "Born inside country"], "synonyms_ar": ["\\u0645\\u0643\\u0627\\u0646 \\u0627\\u0644\\u0648\\u0644\\u0627\\u062f\\u0629", "\\u0645\\u0643\\u0627\\u0646 \\u0627\\u0644\\u0645\\u064a\\u0644\\u0627\\u062f"], "is_primary_key": false, "pii": false, "deprecated": false}, "age_group": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["age", "age band", "age bracket", "age range", "age group"], "synonyms_ar": ["\\u0627\\u0644\\u0639\\u0645\\u0631", "\\u0627\\u0644\\u0633\\u0646", "\\u0627\\u0644\\u0623\\u0639\\u0645\\u0627\\u0631", "\\u0627\\u0644\\u0641\\u0626\\u0629 \\u0627\\u0644\\u0639\\u0645\\u0631\\u064a\\u0629"], "is_primary_key": false, "pii": false, "deprecated": false}, "emirate_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["emirate", "city", "region"], "synonyms_ar": ["\\u0627\\u0644\\u0625\\u0645\\u0627\\u0631\\u0629", "\\u0625\\u0645\\u0627\\u0631\\u0629", "\\u0627\\u0644\\u0645\\u062f\\u064a\\u0646\\u0629"], "is_primary_key": false, "pii": false, "deprecated": false}, "emirate_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prof_base_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["job", "occupation", "profession", "job title"], "synonyms_ar": ["\\u0627\\u0644\\u0645\\u0647\\u0646\\u0629", "\\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u0629", "\\u0627\\u0644\\u0645\\u0633\\u0645\\u0649 \\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u064a"], "is_primary_key": false, "pii": false, "deprecated": false}, "prof_base_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prof_cat_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prof_cat_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "job_level_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["job classification", "occupational level", "skill level", "job level", "workforce level"], "synonyms_ar": ["\\u062a\\u0635\\u0646\\u064a\\u0641 \\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u0629", "\\u0627\\u0644\\u0645\\u0633\\u062a\\u0648\\u0649 \\u0627\\u0644\\u0648\\u0638\\u064a\\u0641\\u064a", "\\u0645\\u0633\\u062a\\u0648\\u0649 \\u0627\\u0644\\u0645\\u0647\\u0627\\u0631\\u0629"], "is_primary_key": false, "pii": false, "deprecated": false}, "job_level_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "is_cur_inside": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["presence", "currently inside", "currently outside", "Currently inside country"], "synonyms_ar": ["\\u0627\\u0644\\u062a\\u0648\\u0627\\u062c\\u062f", "\\u0627\\u0644\\u062d\\u0636\\u0648\\u0631", "\\u0627\\u0644\\u062a\\u0648\\u0627\\u062c\\u062f \\u0627\\u0644\\u062d\\u0627\\u0644\\u064a"], "is_primary_key": false, "pii": false, "deprecated": false}, "last_known_des_cntry_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["destination", "destination country", "Last known destination country"], "synonyms_ar": ["\\u0627\\u0644\\u0648\\u062c\\u0647\\u0629", "\\u0628\\u0644\\u062f \\u0627\\u0644\\u0648\\u062c\\u0647\\u0629", "\\u0628\\u0644\\u062f \\u0627\\u0644\\u0648\\u062c\\u0647\\u0629 \\u0627\\u0644\\u0623\\u062e\\u064a\\u0631\\u0629"], "is_primary_key": false, "pii": false, "deprecated": false}, "last_known_des_cntry_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prsn_cat_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["category", "Person category"], "synonyms_ar": ["\\u0641\\u0626\\u0629", "\\u0627\\u0644\\u0641\\u0626\\u0629", "\\u0641\\u0626\\u0629 \\u0627\\u0644\\u0634\\u062e\\u0635"], "is_primary_key": false, "pii": false, "deprecated": false}, "prsn_cat_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "prsn_sub_cat_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["subcategory", "residency type", "visa type", "citizenship type", "Person subcategory"], "synonyms_ar": ["\\u0646\\u0648\\u0639 \\u0627\\u0644\\u0627\\u0642\\u0627\\u0645\\u0629", "\\u0646\\u0648\\u0639 \\u0627\\u0644\\u062a\\u0623\\u0634\\u064a\\u0631\\u0629", "\\u0627\\u0644\\u0641\\u0626\\u0629 \\u0627\\u0644\\u0641\\u0631\\u0639\\u064a\\u0629"], "is_primary_key": false, "pii": false, "deprecated": false}, "prsn_sub_cat_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "spon_cat_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["sponsor", "sponsorship", "sponsored", "Sponsor category"], "synonyms_ar": ["\\u0627\\u0644\\u0643\\u0641\\u064a\\u0644", "\\u0627\\u0644\\u0643\\u0641\\u0627\\u0644\\u0629", "\\u0627\\u0644\\u0645\\u0643\\u0641\\u0648\\u0644\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u0643\\u0641\\u0648\\u0644\\u0648\\u0646", "\\u0641\\u0626\\u0629 \\u0627\\u0644\\u0643\\u0641\\u064a\\u0644"], "is_primary_key": false, "pii": false, "deprecated": false}, "spon_cat_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "citi_tribe_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["tribe", "family", "clan", "family name"], "synonyms_ar": ["\\u0627\\u0644\\u0642\\u0628\\u064a\\u0644\\u0629", "\\u0627\\u0644\\u0639\\u0627\\u0626\\u0644\\u0629", "\\u0627\\u0644\\u0641\\u062e\\u0630"], "is_primary_key": false, "pii": false, "deprecated": false}, "citi_tribe_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "citi_prv_nat_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["previous nationality", "former nationality", "original nationality", "naturalized", "naturalised", "naturalization"], "synonyms_ar": ["\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0629 \\u0627\\u0644\\u0633\\u0627\\u0628\\u0642\\u0629", "\\u0627\\u0644\\u062c\\u0646\\u0633\\u064a\\u0629 \\u0627\\u0644\\u0623\\u0635\\u0644\\u064a\\u0629", "\\u0627\\u0644\\u0645\\u062a\\u062c\\u0646\\u0633\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u062a\\u062c\\u0646\\u0633\\u0648\\u0646", "\\u0645\\u062a\\u062c\\u0646\\u0633\\u064a\\u0646", "\\u0627\\u0644\\u062a\\u062c\\u0646\\u0633"], "is_primary_key": false, "pii": false, "deprecated": false}, "citi_prv_nat_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "cit_desc_ar": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": [], "synonyms_ar": [], "is_primary_key": false, "pii": false, "deprecated": false}, "cit_desc_en": {"display_name": null, "display_name_ar": null, "description": null, "description_ar": null, "role": null, "semantic_type": null, "unit": null, "default_aggregation": null, "non_additive": false, "allowed_values": {}, "allowed_values_ar": {}, "example_values": [], "format": null, "synonyms": ["registry area", "area of registration", "place of registration", "area of origin", "khulasat al qaid", "registry district"], "synonyms_ar": ["\\u062e\\u0644\\u0627\\u0635\\u0629 \\u0627\\u0644\\u0642\\u064a\\u062f", "\\u0645\\u0646\\u0637\\u0642\\u0629 \\u0627\\u0644\\u0642\\u064a\\u062f", "\\u0645\\u0646\\u0637\\u0642\\u0629 \\u062e\\u0644\\u0627\\u0635\\u0629 \\u0627\\u0644\\u0642\\u064a\\u062f", "\\u0645\\u0646\\u0637\\u0642\\u0629 \\u0627\\u0644\\u0623\\u0635\\u0644", "\\u0627\\u0644\\u0645\\u0642\\u064a\\u062f\\u064a\\u0646", "\\u0627\\u0644\\u0645\\u0642\\u064a\\u062f\\u0648\\u0646", "\\u0645\\u0642\\u064a\\u062f"], "is_primary_key": false, "pii": false, "deprecated": false}}}	Add Arabic column synonyms	import:population.yaml:ar-synonyms	["import:population.yaml:ar-synonyms"]	2026-10-25 14:07:47.903767+00	2026-10-25 14:07:47.919664+00	import:population.yaml:ar-synonyms	2026-10-25 14:07:47.92429+00
\.


--
-- Data for Name: user_session; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_session (id, token_hash, user_id, created_at, expires_at) FROM stdin;
3	e16f4df0a82457e253b9f33f698843d630713c16bb96ee8df0d9806a89dfcac8	1	2026-10-26 09:26:33.700151+00	2026-10-26 21:26:33.686591+00
\.


--
-- Data for Name: webhook; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.webhook (id, name, url, secret, events, is_active, created_at, last_delivery_at, last_status) FROM stdin;
\.


--
-- Name: api_key_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.api_key_id_seq', 1, true);


--
-- Name: app_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.app_user_id_seq', 1000, true);


--
-- Name: audit_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.audit_log_id_seq', 46, true);


--
-- Name: column_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.column_id_seq', 53, true);


--
-- Name: dimension_binding_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dimension_binding_id_seq', 15, true);


--
-- Name: dimension_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dimension_id_seq', 15, true);


--
-- Name: dimension_value_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.dimension_value_id_seq', 874, true);


--
-- Name: glossary_term_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.glossary_term_id_seq', 1, true);


--
-- Name: login_attempt_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.login_attempt_id_seq', 1, true);


--
-- Name: metric_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.metric_id_seq', 3, true);


--
-- Name: profile_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.profile_id_seq', 1, true);


--
-- Name: relationship_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.relationship_id_seq', 1, true);


--
-- Name: sample_query_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.sample_query_id_seq', 1, true);


--
-- Name: schema_meta_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.schema_meta_id_seq', 2, true);


--
-- Name: source_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.source_id_seq', 1, true);


--
-- Name: table_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.table_id_seq', 5, true);


--
-- Name: table_revision_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.table_revision_id_seq', 3, true);


--
-- Name: user_session_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_session_id_seq', 3, true);


--
-- Name: webhook_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.webhook_id_seq', 1, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: api_key pk_api_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT pk_api_key PRIMARY KEY (id);


--
-- Name: app_setting pk_app_setting; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_setting
    ADD CONSTRAINT pk_app_setting PRIMARY KEY (key);


--
-- Name: app_user pk_app_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT pk_app_user PRIMARY KEY (id);


--
-- Name: audit_log pk_audit_log; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT pk_audit_log PRIMARY KEY (id);


--
-- Name: column pk_column; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."column"
    ADD CONSTRAINT pk_column PRIMARY KEY (id);


--
-- Name: dimension pk_dimension; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dimension
    ADD CONSTRAINT pk_dimension PRIMARY KEY (id);


--
-- Name: dimension_binding pk_dimension_binding; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dimension_binding
    ADD CONSTRAINT pk_dimension_binding PRIMARY KEY (id);


--
-- Name: dimension_value pk_dimension_value; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dimension_value
    ADD CONSTRAINT pk_dimension_value PRIMARY KEY (id);


--
-- Name: glossary_term pk_glossary_term; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_term
    ADD CONSTRAINT pk_glossary_term PRIMARY KEY (id);


--
-- Name: login_attempt pk_login_attempt; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_attempt
    ADD CONSTRAINT pk_login_attempt PRIMARY KEY (id);


--
-- Name: metric pk_metric; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metric
    ADD CONSTRAINT pk_metric PRIMARY KEY (id);


--
-- Name: profile pk_profile; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profile
    ADD CONSTRAINT pk_profile PRIMARY KEY (id);


--
-- Name: relationship pk_relationship; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relationship
    ADD CONSTRAINT pk_relationship PRIMARY KEY (id);


--
-- Name: sample_query pk_sample_query; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sample_query
    ADD CONSTRAINT pk_sample_query PRIMARY KEY (id);


--
-- Name: schema_meta pk_schema_meta; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_meta
    ADD CONSTRAINT pk_schema_meta PRIMARY KEY (id);


--
-- Name: source pk_source; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source
    ADD CONSTRAINT pk_source PRIMARY KEY (id);


--
-- Name: table pk_table; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."table"
    ADD CONSTRAINT pk_table PRIMARY KEY (id);


--
-- Name: table_revision pk_table_revision; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_revision
    ADD CONSTRAINT pk_table_revision PRIMARY KEY (id);


--
-- Name: user_session pk_user_session; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_session
    ADD CONSTRAINT pk_user_session PRIMARY KEY (id);


--
-- Name: webhook pk_webhook; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.webhook
    ADD CONSTRAINT pk_webhook PRIMARY KEY (id);


--
-- Name: api_key uq_api_key_key_hash; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT uq_api_key_key_hash UNIQUE (key_hash);


--
-- Name: app_user uq_app_user_email; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT uq_app_user_email UNIQUE (email);


--
-- Name: column uq_column_table_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."column"
    ADD CONSTRAINT uq_column_table_id UNIQUE (table_id, name);


--
-- Name: dimension_binding uq_dimension_binding_column_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dimension_binding
    ADD CONSTRAINT uq_dimension_binding_column_id UNIQUE (column_id);


--
-- Name: dimension uq_dimension_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dimension
    ADD CONSTRAINT uq_dimension_key UNIQUE (key);


--
-- Name: dimension_value uq_dimension_value_dimension_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dimension_value
    ADD CONSTRAINT uq_dimension_value_dimension_id UNIQUE (dimension_id, value);


--
-- Name: glossary_term uq_glossary_term_term; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.glossary_term
    ADD CONSTRAINT uq_glossary_term_term UNIQUE (term);


--
-- Name: metric uq_metric_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metric
    ADD CONSTRAINT uq_metric_name UNIQUE (name);


--
-- Name: profile uq_profile_column_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profile
    ADD CONSTRAINT uq_profile_column_id UNIQUE (column_id);


--
-- Name: schema_meta uq_schema_meta_source_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_meta
    ADD CONSTRAINT uq_schema_meta_source_id UNIQUE (source_id, name);


--
-- Name: source uq_source_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source
    ADD CONSTRAINT uq_source_name UNIQUE (name);


--
-- Name: table_revision uq_table_revision_table_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_revision
    ADD CONSTRAINT uq_table_revision_table_id UNIQUE (table_id, number);


--
-- Name: table uq_table_source_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."table"
    ADD CONSTRAINT uq_table_source_id UNIQUE (source_id, schema_name, name);


--
-- Name: user_session uq_user_session_token_hash; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_session
    ADD CONSTRAINT uq_user_session_token_hash UNIQUE (token_hash);


--
-- Name: ix_login_attempt_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_login_attempt_at ON public.login_attempt USING btree (at);


--
-- Name: ix_login_attempt_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_login_attempt_email ON public.login_attempt USING btree (email);


--
-- Name: uq_table_revision_one_pending; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_table_revision_one_pending ON public.table_revision USING btree (table_id) WHERE ((status)::text = 'pending'::text);


--
-- Name: column fk_column_table_id_table; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."column"
    ADD CONSTRAINT fk_column_table_id_table FOREIGN KEY (table_id) REFERENCES public."table"(id);


--
-- Name: dimension_binding fk_dimension_binding_column_id_column; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dimension_binding
    ADD CONSTRAINT fk_dimension_binding_column_id_column FOREIGN KEY (column_id) REFERENCES public."column"(id);


--
-- Name: dimension_binding fk_dimension_binding_dimension_id_dimension; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dimension_binding
    ADD CONSTRAINT fk_dimension_binding_dimension_id_dimension FOREIGN KEY (dimension_id) REFERENCES public.dimension(id);


--
-- Name: dimension_value fk_dimension_value_dimension_id_dimension; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dimension_value
    ADD CONSTRAINT fk_dimension_value_dimension_id_dimension FOREIGN KEY (dimension_id) REFERENCES public.dimension(id);


--
-- Name: metric fk_metric_base_table_id_table; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metric
    ADD CONSTRAINT fk_metric_base_table_id_table FOREIGN KEY (base_table_id) REFERENCES public."table"(id);


--
-- Name: profile fk_profile_column_id_column; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profile
    ADD CONSTRAINT fk_profile_column_id_column FOREIGN KEY (column_id) REFERENCES public."column"(id);


--
-- Name: relationship fk_relationship_from_column_id_column; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relationship
    ADD CONSTRAINT fk_relationship_from_column_id_column FOREIGN KEY (from_column_id) REFERENCES public."column"(id);


--
-- Name: relationship fk_relationship_to_column_id_column; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.relationship
    ADD CONSTRAINT fk_relationship_to_column_id_column FOREIGN KEY (to_column_id) REFERENCES public."column"(id);


--
-- Name: schema_meta fk_schema_meta_source_id_source; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_meta
    ADD CONSTRAINT fk_schema_meta_source_id_source FOREIGN KEY (source_id) REFERENCES public.source(id);


--
-- Name: table_revision fk_table_revision_table_id_table; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.table_revision
    ADD CONSTRAINT fk_table_revision_table_id_table FOREIGN KEY (table_id) REFERENCES public."table"(id);


--
-- Name: table fk_table_source_id_source; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."table"
    ADD CONSTRAINT fk_table_source_id_source FOREIGN KEY (source_id) REFERENCES public.source(id);


--
-- Name: user_session fk_user_session_user_id_app_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_session
    ADD CONSTRAINT fk_user_session_user_id_app_user FOREIGN KEY (user_id) REFERENCES public.app_user(id);


--
-- PostgreSQL database dump complete
--

\unrestrict MDOE73xUYp739FUH4lGrV1kj0fwqE0MahM4vswAgAK92MVRtjhTuixFOW80TUkj

