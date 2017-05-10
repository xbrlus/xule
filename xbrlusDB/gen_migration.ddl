CREATE TABLE source (
	source_id SERIAL NOT NULL PRIMARY KEY,
	source_name text);
	
INSERT INTO source (source_id, source_name) VALUES (0, 'default');
INSERT INTO source (source_name) VALUES ('SEC');

CREATE TABLE report (
	report_id SERIAL NOT NULL PRIMARY KEY,
	source_id integer NOT NULL,
	entity_id integer NOT NULL,
	source_report_identifier text,
	dts_id integer NOT NULL,
	entry_dts_id integer,
	creation_timestamp timestamp NOT NULL DEFAULT now(),
	accepted_timestamp timestamp NOT NULL DEFAULT now(),
	is_most_current boolean NOT NULL DEFAULT false,
	entity_name text,
	creation_software text,
	entry_type text NOT NULL,
	entry_url text NOT NULL,
	entry_document_id integer NOT NULL,
	alternative_document_id integer,
	reporting_period_end_date timestamp,
	restatement_index integer,
	period_index integer,
	properties JSONB);
	
CREATE UNIQUE INDEX report_index01 ON report (source_report_identifier);
CREATE INDEX report_index02 ON report (entity_id);
CREATE INDEX report_ts_index03 ON report USING gin (to_tsvector('english'::regconfig, entity_name::text));
CREATE INDEX report_index04 ON report (((properties->>'standard_industrial_classificaiton')::integer));

	
ALTER TABLE accession
	ADD COLUMN source_id integer NOT NULL DEFAULT 1;
	
ALTER TABLE accession
	ALTER COLUMN source_id DROP DEFAULT;

ALTER TABLE base_namespace
	ADD COLUMN source_id integer NOT NULL DEFAULT 1;

ALTER TABLE base_namespace
	ALTER COLUMN source_id DROP DEFAULT;

ALTER TABLE fact
	ALTER COLUMN context_id DROP NOT NULL,
	ADD COLUMN fiscal_hash bytea,
	ADD COLUMN fiscal_ultimus_index integer,
	ADD COLUMN unit_base_id integer;
	
ALTER TABLE element
	ADD COLUMN is_tuple boolean NOT NULL DEFAULT false;

ALTER TABLE element
	ALTER COLUMN is_tuple DROP DEFAULT;
	
ALTER TABLE accession
	ADD COLUMN dts_id integer;

/*	
CREATE TABLE entity_identifier
(
  entity_identifier_id serial NOT NULL PRIMARY KEY,
  entity_id integer NOT NULL,
  scheme character varying NOT NULL,
  entity_identifier character varying NOT NULL);
*/

CREATE TABLE entity_source (
	entity_source_id SERIAL NOT NULL PRIMARY KEY,
	entity_id integer NOT NULL,
	source_id integer NOT NULL);
	

CREATE UNIQUE INDEX entity_source_index01 ON entity_source (entity_id, source_id);

CREATE TABLE namespace_source (
	namespace_source_id SERIAL NOT NULL PRIMARY KEY,
	namespace_id integer NOT NULL,
	source_id integer NOT NULL,
	is_base boolean NOT NULL);
	
CREATE UNIQUE INDEX namespace_source_index01 ON namespace_source (namespace_id, source_id);	

CREATE TABLE dts (
	dts_id SERIAL NOT NULL PRIMARY KEY,
	dts_hash bytea NOT NULL,
	dts_name varchar);

CREATE UNIQUE INDEX dts_index01 ON dts (dts_hash);

CREATE TABLE dts_document (
	dts_document_id SERIAL NOT NULL PRIMARY KEY,
	dts_id integer NOT NULL,
	top_level boolean NOT NULL,
	document_id integer NOT NULL);

CREATE INDEX dts_document_index01 ON dts_document (dts_id);

CREATE TABLE dts_network (
	dts_network_id SERIAL NOT NULL PRIMARY KEY,
	dts_id integer NOT NULL,
	extended_link_qname_id integer NOT NULL,
	extended_link_role_uri_id INTEGER NOT NULL,
	arc_qname_id integer NOT NULL,
	arcrole_uri_id integer NOT NULL,
	description text);

CREATE INDEX dts_network_index01 ON dts_network (dts_id);

CREATE INDEX dts_network_index02 ON dts_network (arcrole_uri_id);

CREATE TABLE dts_element
(
  dts_element_id serial NOT NULL,
  dts_id integer NOT NULL,
  element_id integer NOT NULL,
  is_base boolean NOT NULL,
  in_relationship boolean NOT NULL
);

CREATE UNIQUE INDEX dts_element_index01 ON dts_element (dts_id, element_id);
CREATE UNIQUE INDEX dts_element_index02 ON dts_element (element_id, dts_id);

CREATE TABLE report_element
(
  report_element_id serial NOT NULL PRIMARY KEY,
  report_id integer NOT NULL,
  element_id integer NOT NULL,
  is_base boolean NOT NULL,
  primary_count integer,
  dimension_count integer,
  member_count integer
);

CREATE UNIQUE INDEX report_element_index01 ON report_element (report_id, element_id);

CREATE UNIQUE INDEX report_element_index02 ON report_element (element_id, report_id);

CREATE TABLE document_structure (
	document_structure_id SERIAL NOT NULL PRIMARY KEY,
	parent_document_id integer NOT NULL,
	child_document_id integer NOT NULL);
	
CREATE INDEX document_structure_index01
  ON document_structure
  USING btree
  (parent_document_id, child_document_id);

ALTER TABLE document
	ADD COLUMN document_type character varying,
	ADD COLUMN target_namespace character varying;

CREATE UNIQUE INDEX base_namespace_index01 ON base_namespace (source_id, preface);

CREATE UNIQUE INDEX fact_index17 ON fact (fiscal_ultimus_index, fact_id);
CREATE UNIQUE INDEX fact_index18 ON fact (fact_id, fiscal_ultimus_index);

COMMENT ON COLUMN namespace.is_base IS 'Deprecated, use is_base on table namespace_source. Value is used for SEC reports only.';
COMMENT ON COLUMN entity.entity_code IS 'Deprecated, use entity_identifier on table entity_identifier. Value is used for SEC reports only.';
COMMENT ON COLUMN entity.authority_scheme IS 'Deprecated, used scheme on table entity_identifier. Value is used for SEC reports only.';	

CREATE TABLE unit_base (
	unit_base_id SERIAL NOT NULL PRIMARY KEY,
	unit_hash bytea NOT NULL,
	unit_hash_string character varying NOT NULL,
	unit_string character varying);

CREATE TABLE unit_measure_base (
	unit_measure_base_id SERIAL NOT NULL PRIMARY KEY,
	unit_base_id integer NOT NULL,
	qname_id integer NOT NULL,
	location_id smallint);
COMMENT ON COLUMN unit_measure_base.location_id IS '1 = measure; 2 = numerator; 3 = denominator';


CREATE TABLE unit_report (
	unit_report_id SERIAL NOT NULL,

-- Function: document_navigate(integer, integer, integer, integer[])

-- DROP FUNCTION document_navigate(integer, integer, integer, integer[]);

CREATE OR REPLACE FUNCTION document_navigate(
    IN doc_id_arg integer,
    IN tree_order_arg integer,
    IN level_arg integer,
    IN processed_ids integer[])
  RETURNS TABLE(tree_order integer, level integer, document_id integer, starts_loop boolean) AS
$BODY$
DECLARE
	next_doc_id int;
	child_row	record;
	cur_tree_order int;
	ignore_uris	varchar[] := ARRAY['http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd',
				   'http://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd',
				   'http://www.xbrl.org/2005/xbrldt-2005.xsd'];
BEGIN
	RETURN QUERY SELECT tree_order_arg, level_arg, doc_id_arg, False;
	cur_tree_order := tree_order_arg;
	cur_tree_order := cur_tree_order + 1;
	FOR next_doc_id IN SELECT dr.child_document_id 
			   FROM document_structure dr 
			   JOIN document d
			     ON dr.child_document_id = d.document_id
			   WHERE dr.parent_document_id = doc_id_arg
			     AND d.document_uri != ALL(ignore_uris)
	LOOP
		IF next_doc_id = ANY(processed_ids) THEN
			RETURN QUERY SELECT cur_tree_order, level_arg + 1, next_doc_id, True;
			CONTINUE;
		END IF;
		
		FOR child_row IN SELECT * FROM document_navigate(next_doc_id, cur_tree_order, level_arg + 1, processed_ids || doc_id_arg) LOOP
			cur_tree_order := cur_tree_order + 1;
			RETURN QUERY SELECT child_row.tree_order, child_row.level, child_row.document_id, child_row.starts_loop;
		END LOOP;
	END LOOP;
	RETURN;
END

$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION document_navigate(integer, integer, integer, integer[])
  OWNER TO postgres;

-- Function: dts_tree(integer)

-- DROP FUNCTION dts_tree(integer);

CREATE OR REPLACE FUNCTION dts_tree(IN dts_id_arg integer)
  RETURNS TABLE(tree_order integer, level integer, document_id integer, starts_loop boolean) AS
$BODY$

DECLARE
	root_doc_id	int;
BEGIN
	FOR root_doc_id IN SELECT dd.document_id FROM dts_document dd WHERE dd.dts_id = dts_id_arg AND top_level LOOP
		RETURN QUERY SELECT * FROM document_navigate(root_doc_id, 0, 0, ARRAY[]::int[]);
	END LOOP;

	RETURN;
END

$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION dts_tree(integer)
  OWNER TO postgres;
-- Function: report_tree(integer)

-- DROP FUNCTION report_tree(integer);

CREATE OR REPLACE FUNCTION report_tree(IN report_id_arg integer)
  RETURNS TABLE(tree_order integer, level integer, document_id integer, starts_loop boolean) AS
$BODY$
	SELECT *
	FROM document_navigate((SELECT entry_document_id FROM report WHERE report_id = report_id_arg), 0, 0, ARRAY[]::int[]);
$BODY$
  LANGUAGE sql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION report_tree(integer)
  OWNER TO postgres;

CREATE TABLE report_document (
	report_document_id SERIAL NOT NULL,
	report_id integer NOT NULL,
	document_id integer NOT NULL);

CREATE UNIQUE INDEX report_document_index01 ON report_document (report_id, document_id);
CREATE UNIQUE INDEX report_document_index02 ON report_document (document_id, report_id);


ALTER TABLE accession_document_association RENAME TO accession_document_association_migration;


CREATE VIEW accession_document_association AS
WITH r AS (
	SELECT r.report_id, r.dts_id
	FROM report r
)	
SELECT rd.report_document_id AS accession_document_association_id
      ,rd.report_id AS accession_id
      ,rd.document_id
FROM report_document rd
JOIN r
  ON rd.report_id = r.report_id
UNION ALL
SELECT dd.dts_document_id AS accession_document_association_id
      ,r.report_id AS accession_id
      ,dd.document_id
FROM r
JOIN dts_document dd
  ON r.dts_id = dd.dts_id
WHERE r.report_id IN (SELECT r.report_id FROM r);

ALTER TABLE accession_element RENAME TO accession_element_migration;

CREATE OR REPLACE VIEW accession_element AS 
 SELECT COALESCE(re.report_element_id, de.dts_element_id) AS accession_element_id,
    COALESCE(re.report_id, r.report_id) AS accession_id,
    COALESCE(re.element_id, de.element_id) AS element_id,
    COALESCE(re.is_base, de.is_base) AS is_base,
    COALESCE(re.primary_count, NULL::integer) AS primary_count,
    COALESCE(re.dimension_count, NULL::integer) AS dimension_count,
    COALESCE(re.member_count, NULL::integer) AS member_count
   FROM report_element re
     FULL JOIN (dts_element de
     JOIN report r ON de.dts_id = r.dts_id AND de.in_relationship) ON re.report_id = r.report_id AND re.element_id = de.element_id;

CREATE OR REPLACE FUNCTION delete_report(in_report_id bigint)
  RETURNS integer AS
$BODY$
DECLARE
  m_updated INTEGER;
  m_docs RECORD;
  m_sql TEXT;
  m_prev_accession_id INTEGER;
  m_entity_id INTEGER;
  m_source_name VARCHAR;
  m_source_function VARCHAR;
  m_dts_id INTEGER;

BEGIN
    --check if the report exists
    IF ((SELECT 1 FROM report WHERE report_id = in_report_id) IS NULL) THEN
	RETURN 0;
    END IF;

    SELECT entity_id INTO m_entity_id FROM report WHERE report_id = in_report_id;
    SELECT s.source_name 
    INTO m_source_name 
    FROM source s
    JOIN report r
      ON s.source_id = r.source_id
    WHERE r.report_id = in_report_id;
    
    BEGIN
	m_source_function := 'delete_report_pre_' || m_source_name;
	IF (pg_get_functiondef((m_source_function || '(bigint, bigint)')::regprocedure) IS NOT NULL) THEN
		EXECUTE 'SELECT ' || m_source_function || '($1, $2)' USING in_report_id, m_entity_id;
	END IF;
    EXCEPTION WHEN undefined_function THEN
    --do nothing
    END;

    DELETE FROM fact WHERE accession_id = in_report_id;
      
    DELETE FROM unit_measure WHERE unit_id IN 
              (SELECT unit_id FROM unit WHERE accession_id = in_report_id);
              
    DELETE FROM unit WHERE accession_id = in_report_id;
    
    DELETE FROM context_dimension WHERE context_id IN 
            (SELECT context_id FROM context WHERE accession_id = in_report_id);
    
    DELETE FROM context WHERE accession_id = in_report_id;

    SELECT dts_id INTO m_dts_id FROM report WHERE report_id = in_report_id;

    IF (SELECT count(*) = 1 FROM report WHERE dts_id = m_dts_id) THEN
	--dts information is only deleted if there are no other reports that use the dts.
	DELETE FROM relationship rel
		USING dts_network dn
		WHERE dn.dts_id = m_dts_id
		AND rel.network_id = dn.dts_network_id;
	DELETE FROM dts_network
		WHERE dts_id = m_dts_id;
	DELETE FROM dts_document 
		WHERE dts_id = m_dts_id;
	DELETE FROM dts
		WHERE dts_id = m_dts_id;
    END IF;

    /*
    DELETE FROM relationship WHERE network_id in 
        (select network_id from network where accession_id = in_report_id);
    
    DELETE FROM network WHERE accession_id = in_report_id;
    */
    DELETE FROM accession_element WHERE accession_id = in_report_id;
    
    FOR m_docs IN select a.document_id, count(*) c from (select document_id from accession_document_association where accession_id = in_report_id) a
        left outer join accession_document_association b
        on a.document_id = b.document_id
        group by a.document_id LOOP
        
        --This document is not refered by any other accession. delete all related recs
        IF m_docs.c = 1 THEN
            delete from reference_part where resource_id in (select resource_id from resource where document_id = m_docs.document_id);
            delete from label_resource where resource_id in (select resource_id from resource where document_id = m_docs.document_id);
            delete from resource where document_id = m_docs.document_id;
            
            delete from element_attribute where element_id in (select element_id from element where document_id = m_docs.document_id);

            delete from element_attribute_value_association where element_id in (select element_id from element where document_id = m_docs.document_id);

            delete from element where document_id = m_docs.document_id;
        

            delete from custom_role_used_on where custom_role_type_id in (select custom_role_type_id from custom_role_type where document_id = m_docs.document_id);

            delete from custom_role_type where document_id = m_docs.document_id;
    
            delete from custom_arcrole_used_on where custom_arcrole_type_id in (select custom_arcrole_type_id from custom_arcrole_type where document_id = m_docs.document_id);

            delete from custom_arcrole_type where document_id = m_docs.document_id;
            
            delete from accession_document_association WHERE document_id = m_docs.document_id and accession_id = in_report_id;

            delete from document where document_id = m_docs.document_id;
        END IF;
    END LOOP;
    DELETE FROM accession_document_association WHERE accession_id = in_report_id;

    DELETE FROM report WHERE report_id = in_report_id;
    
    --Rebuild entity_name_history
    DELETE FROM entity_name_history WHERE entity_id = m_entity_id;

    INSERT INTO entity_name_history (entity_id, accession_id, entity_name)
    SELECT entity_id, accession_id, entity_name
    FROM (
        SELECT entity_id, accession_id, coalesce(trim(both entity_name),'') as entity_name, TRIM(BOTH COALESCE(LEAD(entity_name) OVER (ORDER BY accepted_timestamp DESC, accession_id DESC),'*#@!')) as next_entity_name
        FROM accession
        WHERE entity_id = m_entity_id
        ORDER BY accepted_timestamp, accession_id
        ) AS x
    WHERE entity_name <> next_entity_name;

    --reset restatement_index, period_index, is_most_current
    UPDATE report r
    SET restatement_index = rn
    FROM (
	SELECT row_number() over(w) AS rn, report_id
	FROM report
	WHERE entity_id = m_entity_id
	WINDOW w AS (partition BY entity_id, reporting_period_end_date ORDER BY accepted_timestamp DESC)) x
    WHERE r.report_id = x.report_id 
      AND x.rn <> coalesce(r.restatement_index, 0);

    UPDATE report r
    SET period_index = rn
    FROM (
	SELECT row_number() over(w) AS rn, report_id
	FROM report
	WHERE entity_id = m_entity_id
	WINDOW w AS (partition BY entity_id ORDER BY reporting_period_end_date DESC, restatement_index ASC)) x
    WHERE r.report_id = x.report_id
      AND x.rn <> coalesce(r.period_index, 0);

    UPDATE report r
    SET is_most_current = x.is_most_current
    FROM (
	SELECT row_number() over (w) = 1 AS is_most_current, report_id
	FROM report
	WHERE entity_id = m_entity_id
	WINDOW w AS (ORDER BY accepted_timestamp DESC, source_report_identifier)) x
    WHERE r.report_id = x.report_id
      AND r.is_most_current != x.is_most_current;

    BEGIN
        DELETE FROM accession WHERE accession_id = in_report_id;
        --reset restatement_index, period_index and is_most_current on the accession table
    EXCEPTION WHEN undefined_table THEN
        --do nothing
    END;

    BEGIN
	m_source_function := 'delete_report_post_' || m_source_name;
	IF (pg_get_functiondef((m_source_function || '(bigint, bigint)')::regprocedure) IS NOT NULL) THEN
		EXECUTE 'SELECT ' || m_source_function || '($1, $2)' USING in_report_id, m_entity_id;
	END IF;
    EXCEPTION WHEN undefined_function THEN
    --do nothing
    END;    
    m_updated = 1;

    RETURN m_updated;
END $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;

DROP FUNCTION delete_accession(bigint);  

CREATE OR REPLACE FUNCTION delete_report_post_sec(in_report_id bigint, in_entity_id bigint) RETURNS void AS
$$
BEGIN
    DELETE FROM accession WHERE accession_id = in_report_id;
END
$$ LANGUAGE plpgsql;

SELECT clock_timestamp(), 'load namespace_source';

INSERT INTO namespace_source (namespace_id, source_id, is_base)
SELECT namespace_id, 1, is_base
FROM namespace;

SELECT clock_timestamp(), 'load report';

INSERT INTO report (
	report_id,
	source_id,
	entity_id,
	source_report_identifier,
	accepted_timestamp,
	is_most_current,
	entity_name,
	creation_software,
	entry_type,
	entry_url,
	entry_document_id,
	alternative_document_id,
	reporting_period_end_date,
	properties)
SELECT accession_id,
       source_id,
       entity_id,
       filing_accession_number,
       accepted_timestamp,
       is_most_current,
       entity_name,
       creation_software,
       entry_type,
       entry_url,
       entry_document_id,
       alternative_document_id,
       reporting_period_end_date,
       json_build_object('standard_industrial_classification', standard_industrial_classification,
			 'state_of_incorporation', state_of_incorporation,
			 'internal_revenue_service_number', internal_revenue_service_number,
			 'business_address', business_address,
			 'business_phone', business_phone,
			 'sec_html_url', sec_html_url,
			 'filing_accession_number', filing_accession_number,
			 'zip_url', zip_url,
			 'document_type', document_type,
			 'percent_extended', percent_extended)::JSONB
FROM accession;	

SELECT max(report_id) AS rid FROM report;
\gset
SELECT pg_catalog.setval('report_report_id_seq', :rid , true);

--build up the dts rows
SELECT clock_timestamp(), 'load dts_document';

INSERT INTO dts (dts_hash)
SELECT digest(d.document_uri, 'sha224')
FROM document d
JOIN accession_document_association ada
  ON d.document_id = ada.document_id
JOIN report r
  ON r.report_id = ada.accession_id
WHERE source_report_identifier != '0000950123-09-043574'
  AND d.document_uri like '%Archive%.xsd'; 
  
SELECT clock_timestamp(), 'load dts_document';  
  
INSERT INTO dts_document (dts_id, document_id)
SELECT dts.dts_id, d.document_id
FROM dts
JOIN document d
  ON dts.dts_hash = digest(d.document_uri, 'sha224');

SELECT clock_timestamp(), 'Fix for SEC filing 0000950123-09-043574';  

INSERT INTO dts (dts_hash)
SELECT digest('http://www.sec.gov/Archives/edgar/data/45288/000095012309043574/ssu-xbrl.xsd|http://www.sec.gov/Archives/edgar/data/45288/000095012309043574/jhnbx-20090531.xsd', 'sha224')
FROM report
WHERE source_report_identifier = '0000950123-09-043574';

INSERT INTO dts_document (dts_id, document_id)
SELECT dts.dts_id, d.document_id
FROM dts
CROSS JOIN document d
WHERE d.document_uri in ('http://www.sec.gov/Archives/edgar/data/45288/000095012309043574/ssu-xbrl.xsd','http://www.sec.gov/Archives/edgar/data/45288/000095012309043574/jhnbx-20090531.xsd')
  AND dts.dts_hash = digest('http://www.sec.gov/Archives/edgar/data/45288/000095012309043574/ssu-xbrl.xsd|http://www.sec.gov/Archives/edgar/data/45288/000095012309043574/jhnbx-20090531.xsd', 'sha224');

SELECT clock_timestamp(), 'update report with dts_id';
UPDATE report r
SET dts_id = dd.dts_id
FROM dts_document dd
JOIN accession_document_association ada
  ON dd.document_id = ada.document_id
WHERE r.report_id = ada.accession_id;

SELECT clock_timestamp(), 'load footnote dts';

INSERT INTO dts (dts_hash)
SELECT digest(r.entry_url, 'sha224')
FROM report r
WHERE EXISTS (
	SELECT 1
	FROM network n
	JOIN qname q
	  ON n.arc_qname_id = q.qname_id
	WHERE q.local_name = 'footnoteArc'
	  AND q.namespace = 'http://www.xbrl.org/2003/linkbase'
	  AND n.accession_id = r.report_id);

SELECT clock_timestamp(), 'load dts_document for footnote dts';

INSERT INTO dts_document (dts_id, document_id)
SELECT dts.dts_id, r.entry_document_id
FROM report r
JOIN dts 
  ON dts.dts_hash = digest(r.entry_url, 'sha224')
WHERE EXISTS (
	SELECT 1
	FROM network n
	JOIN qname q
	  ON n.arc_qname_id = q.qname_id
	WHERE q.local_name = 'footnoteArc'
	  AND q.namespace = 'http://www.xbrl.org/2003/linkbase'
	  AND n.accession_id = r.report_id);

SELECT clock_timestamp(), 'update report with instance_dts_id';
UPDATE report r
SET entry_dts_id = dts.dts_id
FROM dts
WHERE digest(r.entry_url, 'sha224') = dts.dts_hash;

/*
SELECT clock_timestamp(), 'update accession with dts_id';
UPDATE accession r
SET dts_id = dd.dts_id
FROM dts_document dd
JOIN accession_document_association ada
  ON dd.document_id = ada.document_id
WHERE r.accession_id = ada.accession_id;

SELECT clock_timestamp(), 'set dts_id on accession to not null';
ALTER TABLE accession
	ALTER COLUMN dts_id SET NOT NULL;
*/	
SELECT clock_timestamp(), 'load dts_network';
INSERT INTO dts_network
SELECT n.network_id
      ,CASE WHEN q.local_name = 'footnoteArc' AND q.namespace = 'http://www.xbrl.org/2003/linkbase' THEN r.entry_dts_id ELSE r.dts_id END
      ,n.extended_link_qname_id
      ,n.extended_link_role_uri_id
      ,n.arc_qname_id
      ,n.arcrole_uri_id
      ,n.description
FROM report r
JOIN network n
  ON r.report_id = n.accession_id
JOIN qname q
  ON n.arc_qname_id = q.qname_id;
 
SELECT setval(substring(column_default, 'nextval\(''([^'']+)'),dn.max_dts_network_id)
FROM information_schema.columns
CROSS JOIN (
	SELECT max(dts_network_id) AS max_dts_network_id
	FROM dts_network
	) dn
WHERE column_name = 'dts_network_id'
  AND table_schema = 'public'
  AND table_name = 'dts_network';

ALTER TABLE network
	RENAME TO network_original;

CREATE VIEW network AS
	SELECT dn.dts_network_id AS network_id
	      ,r.report_id AS accession_id
	      ,dn.extended_link_qname_id
	      ,dn.extended_link_role_uri_id
	      ,dn.arc_qname_id
	      ,dn.arcrole_uri_id
	      ,dn.description
	FROM report r
	JOIN dts_network dn
	  ON dn.dts_id in (r.dts_id, r.entry_dts_id);
	  

DROP TABLE IF EXISTS migration_unit_base;
SELECT u.unit_id
      ,u.unit_xml_id
      ,u.accession_id
      ,digest(coalesce(string_agg(CASE WHEN um.location_id = 1 THEN '{' || q.namespace || '}' || q.local_name end, '*')
	       ,concat_ws('/'
		      ,string_agg(CASE WHEN um.location_id = 2 THEN '{' || q.namespace || '}' || q.local_name end, '*')
		      ,string_agg(CASE WHEN um.location_id = 3 THEN '{' || q.namespace || '}' || q.local_name end, '*')
	       )), 'sha224') AS unit_hash
      ,coalesce(string_agg(CASE WHEN um.location_id = 1 THEN '{' || q.namespace || '}' || q.local_name end, '*')
	       ,concat_ws('/'
		      ,string_agg(CASE WHEN um.location_id = 2 THEN '{' || q.namespace || '}' || q.local_name end, '*')
		      ,string_agg(CASE WHEN um.location_id = 3 THEN '{' || q.namespace || '}' || q.local_name end, '*')
	       )
	) AS unit_hash_string
      ,coalesce(string_agg(CASE WHEN um.location_id = 1 THEN q.local_name end, '*')
	       ,concat_ws('/'
		      ,string_agg(CASE WHEN um.location_id = 2 THEN q.local_name end, '*')
		      ,string_agg(CASE WHEN um.location_id = 3 THEN q.local_name end, '*')
	       )
	) AS unit_string
INTO TEMP migration_unit_base	
FROM unit_measure um
JOIN qname q
  ON um.qname_id = q.qname_id
JOIN unit u
  ON um.unit_id = u.unit_id
GROUP BY u.unit_id, u.unit_xml_id;

CREATE INDEX migration_unit_base_index ON migration_unit_base (unit_hash);

INSERT INTO unit_base (unit_hash, unit_hash_string, unit_string)
SELECT DISTINCT ON (unit_hash) unit_hash, unit_hash_string, unit_string
FROM migration_unit_base;

CREATE UNIQUE INDEX unit_base_index01 ON unit_base (unit_hash);

INSERT INTO unit_report (unit_report_id, unit_base_id, unit_xml_id, report_id)
SELECT mub.unit_id
      ,ub.unit_base_id
      ,mub.unit_xml_id
      ,mub.accession_id
FROM migration_unit_base mub
JOIN unit_base ub
  ON mub.unit_hash = ub.unit_hash;

SELECT setval(substring(column_default, e'nextval\\(''([^'']+)'),dn.max_id)
FROM information_schema.columns
CROSS JOIN (
	SELECT max(unit_report_id) AS max_id
	FROM unit_report
	) dn
WHERE column_name = 'unit_report_id'
  AND table_schema = 'public'
  AND table_name = 'unit_report';
  

CREATE UNIQUE INDEX unit_report_index01 ON unit_report (report_id, unit_xml_id);
CREATE INDEX unit_report_index02 ON unit_report (unit_base_id);


INSERT INTO unit_measure_base (unit_base_id, qname_id, location_id)
SELECT x.unit_base_id, um.qname_id, um.location_id
FROM (
	SELECT DISTINCT ON (ub.unit_hash) ub.unit_base_id, mub.unit_id
	FROM unit_base ub
	JOIN migration_unit_base mub
	  ON ub.unit_hash = mub.unit_hash
) x
JOIN unit_measure um
  ON x.unit_id = um.unit_id


CREATE INDEX unit_measure_base_index01 ON unit_measure_base (unit_base_id);

/*
WITH unit_conversion AS (
	SELECT mub.unit_id, ub.unit_base_id
	FROM migration_unit_base mub
	JOIN unit_base ub
	  ON mub.unit_hash = ub.unit_hash
)
UPDATE fact f
SET unit_id = uc.unit_base_id
FROM unit_conversion uc
WHERE f.unit_id IS NOT NULL
  AND uc.unit_id = f.unit_id;
*/

--NEED TO ADD unit_base_id TO THE fact TABLE AND LEAVE unit_id AS THE unit_report_id

ALTER TABLE unit RENAME TO unit_previous;


CREATE VIEW unit AS
SELECT ur.unit_report_id AS unit_id
      ,ur.report_id AS accession_id
      ,ur.unit_xml_id
FROM unit_report ur;  

ALTER TABLE unit_measure RENAME TO unit_measure_previous;

CREATE VIEW unit_measure AS
SELECT umb.unit_measure_base_id AS unit_measure_id
      ,ur.unit_report_id AS unit_id
      ,umb.qname_id
      ,umb.location_id
FROM unit_measure_base umb
JOIN unit_report ur
  ON umb.unit_base_id = ur.unit_base_id;

CREATE OR REPLACE FUNCTION uom(unit_id_arg integer) RETURNS varchar AS
$$
SELECT ub.unit_string
FROM unit_base ub
JOIN unit_report ur
  ON ub.unit_base_id = ur.unit_base_id
WHERE ur.unit_report_id = unit_id_arg
$$ LANGUAGE sql;

DROP TABLE accession;

CREATE VIEW accession AS
SELECT report_id AS accession_id
      ,accepted_timestamp
      ,is_most_current
      ,(properties->>'filing_date')::date AS filing_date
      ,entity_id
      ,entity_name
      ,creation_software
      ,NULL::varchar AS creation_software_short
      ,(properties->>'standard_industrial_classification')::integer AS standard_industrial_classification
      ,properties->>'state_of_incorporation' As state_of_incorporation
      ,(properties->>'internal_revenue_service_number')::integer AS internal_revenue_service_number
      ,properties->>'business_address' AS business_address
      ,properties->>'business_phone' AS business_phone
      ,properties->>'sec_html_url' AS sec_html_url
      ,entry_url
      ,source_report_identifier As filing_accession_number
      ,properties->>'zip_url' AS zip_url
      ,properties->>'document_type' As document_type
      ,(properties->>'percent_extended')::integer AS percent_extended
      ,restatement_index
      ,period_index
      ,True::boolean AS is_complete
      ,entry_type
      ,entry_document_id
      ,alternative_document_id
      ,reporting_period_end_date
FROM report r
JOIN source s
  ON r.source_id = s.source_id
WHERE s.source_name = 'SEC';

DROP TABLE accession_timestamp;

CREATE VIEW accession_timestamp AS
SELECT report_id AS accession_id
      ,creation_timestamp AS creation_time
FROM report  






