-- ****************************************************************************
CREATE SEQUENCE public.entity_tripdatacommon_id_seq
  INCREMENT 1
  MINVALUE 1
  MAXVALUE 9223372036854775807
  START 4
  CACHE 1;
ALTER TABLE public.entity_tripdatacommon_id_seq
  OWNER TO django;
  
CREATE TABLE public.entity_tripdatacommon
(
  id integer NOT NULL DEFAULT nextval('entity_tripdatacommon_id_seq'::regclass),
  ts timestamp with time zone[] NOT NULL,
  CONSTRAINT entity_tripdatacommon_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.entity_tripdatacommon
  OWNER TO django;



-- ****************************************************************************
CREATE TABLE public.entity_tripdatadecimal
(
  "values" numeric(20,6)[] NOT NULL,
  columns character varying(64)[] NOT NULL
) INHERITS (public.entity_tripdatacommon)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.entity_tripdatadecimal
  OWNER TO django;




-- ****************************************************************************
CREATE TABLE public.entity_tripdataint
(
  "values" integer[] NOT NULL,
  columns character varying(64)[] NOT NULL
) INHERITS (public.entity_tripdatacommon)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.entity_tripdataint
  OWNER TO django;




-- ****************************************************************************
CREATE TABLE public.entity_tripdatastring
(
  "values" character varying(256)[] NOT NULL,
  columns character varying(64)[] NOT NULL
) INHERITS (public.entity_tripdatacommon)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.entity_tripdatastring
  OWNER TO django;





-- ****************************************************************************
-- ****************************************************************************
-- ****************************************************************************
INSERT INTO entity_tripdatadecimal (columns, ts, "values") VALUES (
	'{"val1","val2"}',
	'{"2011-01-01 00:01:00", "2011-01-01 00:02:00"}',
	'{1.1, 2.2}'
);

INSERT INTO entity_tripdataint (columns, ts, "values") VALUES (
	'{"val3","val4"}',
	'{"2011-01-01 00:01:00", "2011-01-01 00:02:00"}',
	'{3, 4}'
);

INSERT INTO entity_tripdatastring (columns, ts, "values") VALUES (
	'{"val5","val6"}',
	'{"2011-01-01 00:01:00", "2011-01-01 00:02:00"}',
	'{"5555", "6666"}'
);




-- ****************************************************************************
-- ****************************************************************************
-- ****************************************************************************
SELECT * FROM entity_tripdatacommon
SELECT * FROM entity_tripdataint
SELECT * FROM entity_tripdatadecimal
SELECT * FROM entity_tripdatastring
