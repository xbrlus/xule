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
	ADD COLUMN fiscal_ultimus_index integer;
	
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
	dts_hash bytea NOT NULL);

CREATE UNIQUE INDEX dts_index01 ON dts (dts_hash);

CREATE TABLE dts_document (
	dts_document_id SERIAL NOT NULL PRIMARY KEY,
	dts_id integer NOT NULL,
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

CREATE TABLE document_reference (
	document_reference_id SERIAL NOT NULL PRIMARY KEY,
	document_id integer NOT NULL,
	referenced_document_id integer NOT NULL);
	
CREATE INDEX document_reference_index01 ON document_reference (document_id);

ALTER TABLE document
	ADD COLUMN document_type character varying;

CREATE UNIQUE INDEX base_namespace_index01 ON base_namespace (source_id, preface);

CREATE UNIQUE INDEX fact_index17 ON fact (fiscal_ultimus_index, fact_id);
CREATE UNIQUE INDEX fact_index18 ON fact (fact_id, fiscal_ultimus_index);

COMMENT ON COLUMN namespace.is_base IS 'Deprecated, use is_base on table namespace_source. Value is used for SEC reports only.';
COMMENT ON COLUMN entity.entity_code IS 'Deprecated, use entity_identifier on table entity_identifier. Value is used for SEC reports only.';
COMMENT ON COLUMN entity.authority_scheme IS 'Deprecated, used scheme on table entity_identifier. Value is used for SEC reports only.';	


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




