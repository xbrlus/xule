USE [master]
GO
/****** Object:  Database [XBRL]    Script Date: 5/22/2020 1:58:37 PM ******/
/*
CREATE DATABASE [XBRL]
 CONTAINMENT = NONE
 ON  PRIMARY 
( NAME = N'XBRL5', FILENAME = N'F:\SQLData\XBRL.mdf' , SIZE = 4726784KB , MAXSIZE = UNLIMITED, FILEGROWTH = 65536KB )
 LOG ON 
( NAME = N'XBRL5_log', FILENAME = N'G:\SQLLogs\XBRL_log.ldf' , SIZE = 2105344KB , MAXSIZE = 2048GB , FILEGROWTH = 65536KB )
GO
*/
ALTER DATABASE [XBRL] SET COMPATIBILITY_LEVEL = 130
GO
IF (1 = FULLTEXTSERVICEPROPERTY('IsFullTextInstalled'))
begin
EXEC [XBRL].[dbo].[sp_fulltext_database] @action = 'enable'
end
GO
ALTER DATABASE [XBRL] COLLATE SQL_Latin1_General_CP1_CS_AS
GO
ALTER DATABASE [XBRL] SET ANSI_NULL_DEFAULT OFF 
GO
ALTER DATABASE [XBRL] SET ANSI_NULLS OFF 
GO
ALTER DATABASE [XBRL] SET ANSI_PADDING OFF 
GO
ALTER DATABASE [XBRL] SET ANSI_WARNINGS OFF 
GO
ALTER DATABASE [XBRL] SET ARITHABORT OFF 
GO
ALTER DATABASE [XBRL] SET AUTO_CLOSE OFF 
GO
ALTER DATABASE [XBRL] SET AUTO_SHRINK OFF 
GO
ALTER DATABASE [XBRL] SET AUTO_UPDATE_STATISTICS ON 
GO
ALTER DATABASE [XBRL] SET CURSOR_CLOSE_ON_COMMIT OFF 
GO
ALTER DATABASE [XBRL] SET CURSOR_DEFAULT  GLOBAL 
GO
ALTER DATABASE [XBRL] SET CONCAT_NULL_YIELDS_NULL OFF 
GO
ALTER DATABASE [XBRL] SET NUMERIC_ROUNDABORT OFF 
GO
ALTER DATABASE [XBRL] SET QUOTED_IDENTIFIER OFF 
GO
ALTER DATABASE [XBRL] SET RECURSIVE_TRIGGERS OFF 
GO
ALTER DATABASE [XBRL] SET  DISABLE_BROKER 
GO
ALTER DATABASE [XBRL] SET AUTO_UPDATE_STATISTICS_ASYNC OFF 
GO
ALTER DATABASE [XBRL] SET DATE_CORRELATION_OPTIMIZATION OFF 
GO
ALTER DATABASE [XBRL] SET TRUSTWORTHY OFF 
GO
ALTER DATABASE [XBRL] SET ALLOW_SNAPSHOT_ISOLATION OFF 
GO
ALTER DATABASE [XBRL] SET PARAMETERIZATION SIMPLE 
GO
ALTER DATABASE [XBRL] SET READ_COMMITTED_SNAPSHOT OFF 
GO
ALTER DATABASE [XBRL] SET HONOR_BROKER_PRIORITY OFF 
GO
ALTER DATABASE [XBRL] SET RECOVERY FULL 
GO
ALTER DATABASE [XBRL] SET  MULTI_USER 
GO
ALTER DATABASE [XBRL] SET PAGE_VERIFY CHECKSUM  
GO
ALTER DATABASE [XBRL] SET DB_CHAINING OFF 
GO
ALTER DATABASE [XBRL] SET FILESTREAM( NON_TRANSACTED_ACCESS = OFF ) 
GO
ALTER DATABASE [XBRL] SET TARGET_RECOVERY_TIME = 60 SECONDS 
GO
ALTER DATABASE [XBRL] SET DELAYED_DURABILITY = DISABLED 
GO
EXEC sys.sp_db_vardecimal_storage_format N'XBRL', N'ON'
GO
ALTER DATABASE [XBRL] SET QUERY_STORE = OFF
GO
USE [XBRL]
GO
ALTER DATABASE SCOPED CONFIGURATION SET LEGACY_CARDINALITY_ESTIMATION = OFF;
GO
ALTER DATABASE SCOPED CONFIGURATION SET MAXDOP = 0;
GO
ALTER DATABASE SCOPED CONFIGURATION SET PARAMETER_SNIFFING = ON;
GO
ALTER DATABASE SCOPED CONFIGURATION SET QUERY_OPTIMIZER_HOTFIXES = OFF;
GO
USE [XBRL]
GO
/****** Object:  User [XBRLSQLAdmin]    Script Date: 5/22/2020 1:58:39 PM ******/
/*
CREATE USER [XBRLSQLAdmin] FOR LOGIN [XBRLSQLAdmin] WITH DEFAULT_SCHEMA=[dbo]
GO
*/
/****** Object:  User [ADFERC\XBRLSQLAdmins]    Script Date: 5/22/2020 1:58:39 PM ******/
/*
CREATE USER [ADFERC\XBRLSQLAdmins] FOR LOGIN [ADFERC\XBRLSQLAdmins]
GO
ALTER ROLE [db_owner] ADD MEMBER [XBRLSQLAdmin]
GO
ALTER ROLE [db_owner] ADD MEMBER [ADFERC\XBRLSQLAdmins]
GO
*/
/****** Object:  FullTextCatalog [entity_ts_index03Catalog]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE FULLTEXT CATALOG [entity_ts_index03Catalog] WITH ACCENT_SENSITIVITY = ON
AS DEFAULT
GO
/****** Object:  FullTextCatalog [fact_ts_index03Catalog]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE FULLTEXT CATALOG [fact_ts_index03Catalog] WITH ACCENT_SENSITIVITY = ON
GO
/****** Object:  FullTextCatalog [label_resource_ts_index02Catalog]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE FULLTEXT CATALOG [label_resource_ts_index02Catalog] WITH ACCENT_SENSITIVITY = ON
GO
/****** Object:  FullTextCatalog [qnameindexCatalog]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE FULLTEXT CATALOG [qnameindexCatalog] WITH ACCENT_SENSITIVITY = ON
GO
/****** Object:  FullTextCatalog [report_ts_index03]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE FULLTEXT CATALOG [report_ts_index03] WITH ACCENT_SENSITIVITY = ON
GO
/****** Object:  FullTextCatalog [reportindexCatalog]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE FULLTEXT CATALOG [reportindexCatalog] WITH ACCENT_SENSITIVITY = ON
GO
/****** Object:  UserDefinedFunction [dbo].[base_taxonomy_name]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE FUNCTION [dbo].[base_taxonomy_name]
(@accession_id_arg integer) 
RETURNS varchar
AS
BEGIN
			
			DECLARE  @result  varchar;
             SELECT @result = t.name +' '+ tv.version
             FROM taxonomy t
             JOIN taxonomy_version tv
             ON t.taxonomy_id = tv.taxonomy_id
             WHERE tv.taxonomy_version_id = dbo.base_taxonomy_version(@accession_id_arg);
 
             RETURN @result;
END

--SELECT dbo.base_taxonomy_name(1);
--drop function dbo.base_taxonomy_name
GO
/****** Object:  UserDefinedFunction [dbo].[base_taxonomy_version]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE FUNCTION [dbo].[base_taxonomy_version](
    @accession_id_arg INT
)
RETURNS INT
AS 
BEGIN

DECLARE @return_taxonomy_version integer

SELECT @return_taxonomy_version = tv.taxonomy_version_id
FROM taxonomy_version tv
JOIN accession_document_association ada
ON tv.identifier_document_id = ada.document_id
WHERE ada.accession_id = @accession_id_arg;


RETURN @accession_id_arg
END;
GO
/****** Object:  UserDefinedFunction [dbo].[get_simple_fact_by_accession]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE FUNCTION [dbo].[get_simple_fact_by_accession](@prefix_arg VARCHAR, @local_name_arg VARCHAR, @accession_id_arg integer) RETURNS VARCHAR
AS
BEGIN
	DECLARE @VAR varchar;
	DECLARE	@prefix_var varchar;
	DECLARE @result_row TABLE
	(
	[effective_value] [numeric](30, 6) NULL,
	[fact_value] [nvarchar](max) NULL)
	
	INSERT INTO @result_row
	SELECT TOP 1 f.effective_value, f.fact_value
	FROM accession a
	JOIN fact f
	  ON a.accession_id = f.accession_id
	JOIN element e
	  ON f.element_id = e.element_id
	JOIN qname q
	  ON e.qname_id = q.qname_id
	JOIN namespace n
	  ON q.namespace = n.uri
	JOIN context c
	  ON f.context_id = c.context_id
	WHERE  c.specifies_dimensions = 0
	  AND a.accession_id = @accession_id_arg
	  AND q.local_name = @local_name_arg
	  AND n.prefix = 
	   CASE WHEN @prefix_arg = 'extension' THEN  NULL 
	         WHEN @prefix_arg IS NULL THEN  'us-gaap'  
	         ELSE  @prefix_arg
	         END
	ORDER BY f.fact_id
	

	IF EXISTS(Select 1 from @result_row where effective_value IS NULL)
	BEGIN
		(SELECT @VAR = cast(fact_value as varchar) from @result_row)
	END
	ELSE
	BEGIN
		 (SELECT @VAR = cast(effective_value as varchar) from @result_row);
	END 

	RETURN @VAR
END;

GO
/****** Object:  UserDefinedFunction [dbo].[is_base]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE FUNCTION [dbo].[is_base](@namespace_arg varchar) RETURNS BIT
    AS

BEGIN
	DECLARE @IsBase BIT  
	DECLARE  @namespace_row TABLE
	(
	[uri] [nvarchar](max) NOT NULL,
	[is_base] [bit] NOT NULL,
	[taxonomy_version_id] [int] NULL,
	[prefix] [nvarchar](max) NULL,
	[name] [nvarchar](max) NULL
	)

	INSERT INTO @namespace_row 
	SELECT uri, is_base, taxonomy_version_id, prefix, name FROM namespace WHERE uri = @namespace_arg;
	
	IF EXISTS( SELECT is_base from @namespace_row where is_base = 1)
	BEGIN
	SET @IsBase = 1
	END

	IF EXISTS( SELECT is_base from @namespace_row where is_base = 0)
	BEGIN
	SET @IsBase = 0
	END



	RETURN @IsBase
	
END;





GO
/****** Object:  UserDefinedFunction [dbo].[list_dimensional_qualifications]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE FUNCTION [dbo].[list_dimensional_qualifications](@context_id_arg integer) RETURNS VARCHAR
AS 

BEGIN
	DECLARE @context_id_var integer;
	DECLARE	@cd_record TABLE 
	( [id] [int] IDENTITY(1,1) NOT NULL,
	[dim_namespace] [nvarchar](max) NULL,
	[dim_local_name] [nvarchar](max) NOT NULL,
	[mem_namespace] [nvarchar](max) NULL,
	[mem_local_name] [nvarchar](max) NULL	
	);
	DECLARE @dimension_list varchar(max) = '';
	DECLARE @dimension_row  varchar(max) = '';
	DECLARE @CNT integer = 1; 
	DECLARE @TEMP VARCHAR(MAX);

	INSERT INTO @cd_record
	SELECT qa.namespace as dim_namespace
	,qa.local_name as dim_local_name
	,qm.namespace as mem_namespace
	,COALESCE(qm.local_name, cd.typed_text_content) as mem_local_name
	FROM context_dimension cd
	JOIN qname qa
		ON cd.dimension_qname_id = qa.qname_id
	LEFT JOIN qname qm
		ON cd.member_qname_id = qm.qname_id
	WHERE context_id = @context_id_arg
		AND is_default = 0
	ORDER BY 2, 1, 4, 3
	
	WHILE(@CNT <= (SELECT COUNT(*) FROM @cd_record))
	BEGIN
		SELECT @TEMP =  (''+ cd_record.dim_local_name+ ''+ cd_record.mem_local_name) from @cd_record cd_record where id = @CNT
		SET @dimension_row =  @TEMP;
		SET @dimension_list = @dimension_list + @dimension_row;
		SET @CNT = @CNT + 1;
		SET @TEMP = ''
	END 

	
	return @dimension_list;

END;
GO
/****** Object:  UserDefinedFunction [dbo].[list_dimensional_qualifications_for_fact]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE FUNCTION [dbo].[list_dimensional_qualifications_for_fact](@fact_id_arg integer) RETURNS varchar
AS 
BEGIN
	DECLARE @context_id_var integer;
	DECLARE	@cd_record TABLE 
	( [id] [int] IDENTITY(1,1) NOT NULL,
	[dim_namespace] [nvarchar](max) NULL,
	[dim_local_name] [nvarchar](max) NOT NULL,
	[mem_namespace] [nvarchar](max) NULL,
	[mem_local_name] [nvarchar](max) NULL	
	);
	DECLARE @dimension_list varchar(max) = '';
	DECLARE @dimension_row  varchar(max) = '';
	DECLARE @CNT integer = 1; 
	DECLARE @TEMP VARCHAR(MAX);
	
	SELECT @context_id_var = context_id FROM fact WHERE fact_id = @fact_id_arg;
	
	INSERT INTO @cd_record 
	SELECT qa.namespace as dim_namespace
		,qa.local_name as dim_local_name
	,qm.namespace as mem_namespace
	,COALESCE(qm.local_name, cd.typed_text_content) as mem_local_name
	FROM context_dimension cd
	JOIN qname qa
		ON cd.dimension_qname_id = qa.qname_id
	LEFT JOIN qname qm
		ON cd.member_qname_id = qm.qname_id
	WHERE context_id = @context_id_var
		AND is_default = 0
	ORDER BY 2, 1, 4, 3


	WHILE(@CNT <= (SELECT COUNT(*) FROM @cd_record))
	BEGIN
		SELECT @TEMP =  (''+ [dim_local_name]+ ''+ [mem_local_name]) from @cd_record where id = @CNT
		SET @dimension_row =  @TEMP;
		SET @dimension_list = @dimension_list + @dimension_row;
		SET @CNT = @CNT + 1;
		SET @TEMP = ''
	END 

	
	return @dimension_list;
END;
GO
/****** Object:  UserDefinedFunction [dbo].[list_dimensional_qualifications_for_fact2]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE FUNCTION [dbo].[list_dimensional_qualifications_for_fact2](@fact_id_arg integer) RETURNS varchar
AS

BEGIN
	DECLARE @context_id_var integer;
	DECLARE	@cd_record TABLE 
	( [id] [int] IDENTITY(1,1) NOT NULL,
	[dim_namespace] [nvarchar](max) NULL,
	[dim_local_name] [nvarchar](max) NOT NULL,
	[mem_namespace] [nvarchar](max) NULL,
	[mem_local_name] [nvarchar](max) NULL	
	);
	DECLARE @dimension_list varchar(max) = '';
	DECLARE @dimension_row  varchar(max) = '';
	DECLARE @CNT integer = 1; 
	DECLARE @TEMP VARCHAR(MAX);
	
	SELECT @context_id_var = context_id FROM fact WHERE fact_id = @fact_id_arg;

	INSERT INTO @cd_record 
	SELECT qa.namespace as dim_namespace
		,qa.local_name as dim_local_name
	,qm.namespace as mem_namespace
	,COALESCE(qm.local_name, cd.typed_text_content) as mem_local_name
	FROM context_dimension cd
	JOIN qname qa
		ON cd.dimension_qname_id = qa.qname_id
	LEFT JOIN qname qm
		ON cd.member_qname_id = qm.qname_id
	WHERE context_id = @context_id_var
		AND is_default = 0
	ORDER BY 2, 1, 4, 3
	
	WHILE(@CNT <= (SELECT COUNT(*) FROM @cd_record))
	BEGIN
		SELECT @TEMP =  (dim_namespace + '|' + dim_local_name + '|' + COALESCE(mem_namespace,'') + '|' + mem_local_name + '|') from @cd_record where id = @CNT
		SET @dimension_row =  @TEMP;
		SET @dimension_list = @dimension_list + @dimension_row;
		SET @CNT = @CNT + 1;
		SET @TEMP = ''
	END 

	
	return @dimension_list;
END;
GO
/****** Object:  UserDefinedFunction [dbo].[list_dimensional_qualifications_string]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE FUNCTION [dbo].[list_dimensional_qualifications_string](@context_id_arg integer) RETURNS VARCHAR
AS 

BEGIN
	DECLARE	@cd_record TABLE 
	( [id] [int] IDENTITY(1,1) NOT NULL,
	[dim_namespace] [nvarchar](max) NULL,
	[dim_local_name] [nvarchar](max) NOT NULL,
	[mem_namespace] [nvarchar](max) NULL,
	[mem_local_name] [nvarchar](max) NULL	
	);

	DECLARE @dimension_list varchar = '';
	DECLARE @dimension_row  varchar = '';
	DECLARE @CNT integer = 1; 
	DECLARE @TEMP VARCHAR(MAX);

	INSERT INTO @cd_record 
	SELECT qa.namespace as dim_namespace
	,qa.local_name as dim_local_name
	,qm.namespace as mem_namespace
	,COALESCE(qm.local_name, cd.typed_text_content) as mem_local_name
	FROM context_dimension cd
	JOIN qname qa
		ON cd.dimension_qname_id = qa.qname_id
	LEFT JOIN qname qm
		ON cd.member_qname_id = qm.qname_id
	WHERE context_id = @context_id_arg
		AND is_default = 0
	ORDER BY 2, 1, 4, 3
  
	WHILE(@CNT <= (SELECT COUNT(*) FROM @cd_record))
	BEGIN
		SELECT @TEMP =  (dim_namespace + '|' + dim_local_name + '|' + COALESCE(mem_namespace,'') + '|' + mem_local_name + '|') from @cd_record where id = @CNT
		SET @dimension_row =  @TEMP;
		SET @dimension_list = @dimension_list + @dimension_row;
		SET @CNT = @CNT + 1;
		SET @TEMP = ''
	END 
	return @dimension_list;
END;


GO
/****** Object:  UserDefinedFunction [dbo].[list_dimensional_qualifications_string2]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE FUNCTION [dbo].[list_dimensional_qualifications_string2](@context_id_arg integer) RETURNS VARCHAR
    AS 
BEGIN
	DECLARE	@cd_record TABLE 
	( [id] [int] IDENTITY(1,1) NOT NULL,
	[dim_namespace] [nvarchar](max) NULL,
	[dim_local_name] [nvarchar](max) NOT NULL,
	[mem_namespace] [nvarchar](max) NULL,
	[mem_local_name] [nvarchar](max) NULL	
	);

	DECLARE @dimension_list varchar = '';
	DECLARE @dimension_row  varchar = '';
	DECLARE @first_iteration bit = 1;
	DECLARE @newline varchar =  '';
	DECLARE @CNT integer = 1; 
	DECLARE @TEMP VARCHAR(MAX);

	INSERT INTO @cd_record
	SELECT qa.namespace as dim_namespace
	,qa.local_name as dim_local_name
	,qm.namespace as mem_namespace
	,COALESCE(qm.local_name, cd.typed_text_content) as mem_local_name
	FROM context_dimension cd
	JOIN qname qa
		ON cd.dimension_qname_id = qa.qname_id
	LEFT JOIN qname qm
		ON cd.member_qname_id = qm.qname_id
	WHERE context_id = @context_id_arg
		AND is_default = 0
	ORDER BY 2, 1, 4, 3
  
	WHILE(@CNT <= (SELECT COUNT(*) FROM @cd_record))
	BEGIN
		SELECT @TEMP =  ('{' + dim_namespace + '}' + dim_local_name + '=' + COALESCE('{' + mem_namespace + '}', '') + mem_local_name) from @cd_record where id = @CNT
		SET @dimension_row =  @newline + @TEMP;
		SET @dimension_list = @dimension_list + @dimension_row;
		
		IF (@first_iteration = 1)
		BEGIN
			SET @first_iteration = 0;
			SET @newline = '\n';
		END;
		SET @CNT = @CNT + 1;
		SET @TEMP = ''
	END

	return @dimension_list;

END;








GO
/****** Object:  UserDefinedFunction [dbo].[list_dimensional_qualifications2]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE FUNCTION [dbo].[list_dimensional_qualifications2](@context_id_arg integer) RETURNS VARCHAR
AS 
BEGIN
	DECLARE @context_id_var integer;
	DECLARE	@cd_record TABLE 
	( [id] [int] IDENTITY(1,1) NOT NULL,
	[dim_namespace] [nvarchar](max) NULL,
	[dim_local_name] [nvarchar](max) NOT NULL,
	[mem_namespace] [nvarchar](max) NULL,
	[mem_local_name] [nvarchar](max) NULL	
	);
	DECLARE @dimension_list varchar(max) = '';
	DECLARE @dimension_row  varchar(max) = '';
	DECLARE @CNT integer = 1; 
	DECLARE @TEMP VARCHAR(MAX);

	INSERT INTO @cd_record
	SELECT qa.namespace as dim_namespace
	,qa.local_name as dim_local_name
	,qm.namespace as mem_namespace
	,COALESCE(qm.local_name, cd.typed_text_content) as mem_local_name
	FROM context_dimension cd
	JOIN qname qa
		ON cd.dimension_qname_id = qa.qname_id
	LEFT JOIN qname qm
		ON cd.member_qname_id = qm.qname_id
	WHERE context_id = @context_id_arg
		AND is_default = 0
	ORDER BY 2, 1, 4, 3
  

	
	WHILE(@CNT <= (SELECT COUNT(*) FROM @cd_record))
	BEGIN
		SELECT @TEMP =  (cd_record.dim_namespace+ cd_record.dim_local_name + cd_record.mem_namespace + cd_record.mem_local_name) from @cd_record cd_record where id = @CNT
		SET @dimension_row =  @TEMP;
		SET @dimension_list = @dimension_list + @dimension_row;
		SET @CNT = @CNT + 1;
		SET @TEMP = ''
	END 

	
	return @dimension_list;
END;
GO
/****** Object:  UserDefinedFunction [dbo].[update_all_period_index]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE FUNCTION [dbo].[update_all_period_index]() RETURNS integer
    
    AS

BEGIN
	DECLARE @m_updated integer;
	UPDATE accession 
	SET period_index = rn
	   ,is_most_current = CASE WHEN rn = 1 THEN 1 ELSE 0 END
	FROM (SELECT row_number() over(partition BY entity_id ORDER BY period_end DESC, restatement_index ASC) AS rn, entity_id, accepted_timestamp, period_end, accession_id, restatement_index
	      FROM (SELECT entity_id, accepted_timestamp, accession.accession_id, period_end, restatement_index
		    FROM accession
		    JOIN (SELECT f.accession_id, max(c.period_end) period_end
			  FROM fact f
			  JOIN element e
			    ON f.element_id = e.element_id
			  JOIN qname q
			    ON e.qname_id = q.qname_id
			  JOIN context c
			    ON f.context_id = c.context_id
			  JOIN accession a
			    ON f.accession_id = a.accession_id
			  WHERE q.namespace like '%/dei/%'
			    AND q.local_name = 'DocumentPeriodEndDate'
			  GROUP BY f.accession_id) accession_period_end
		      ON accession.accession_id = accession_period_end.accession_id) accession_list

	) AS x
	WHERE accession.accession_id = x.accession_id;

	set @m_updated = @@rowcount;
	
	UPDATE entity 
		SET entity_name = a.entity_name 
		FROM (SELECT entity_id, entity_name FROM accession WHERE period_index = 1) as a
		WHERE entity.entity_id = a.entity_id;
		
	RETURN @m_updated;

END;
GO
/****** Object:  UserDefinedFunction [dbo].[update_all_restatement_index]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE FUNCTION [dbo].[update_all_restatement_index]() RETURNS integer
AS
BEGIN

	UPDATE accession   
	SET restatement_index = rn
	FROM (SELECT row_number() over(partition BY entity_id, period_end ORDER BY accepted_timestamp DESC) AS rn, entity_id, accepted_timestamp, period_end, accession_id  
	      FROM (SELECT entity_id, accepted_timestamp, accession.accession_id, period_end  
		    FROM accession  
		    JOIN (SELECT f.accession_id, max(c.period_end) period_end
			  FROM fact f
			  JOIN element e
			    ON f.element_id = e.element_id
			  JOIN qname q
			    ON e.qname_id = q.qname_id
			  JOIN context c
			    ON f.context_id = c.context_id
			  JOIN accession a
			    ON f.accession_id = a.accession_id
			  WHERE q.namespace like '%/dei/%'  
			    AND q.local_name = 'DocumentPeriodEndDate'
			  GROUP BY f.accession_id) accession_period_end
		      ON accession.accession_id = accession_period_end.accession_id) accession_list  

	) AS x  
	WHERE accession.accession_id = x.accession_id
	  AND coalesce(restatement_index,0) <> rn;



	RETURN @@rowcount

END;
GO
/****** Object:  UserDefinedFunction [dbo].[update_calendar_index]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
	CREATE FUNCTION [dbo].[update_calendar_index](@hash_string VARBINARY) RETURNS integer
	AS 
	BEGIN
   
        UPDATE fact 
        SET calendar_ultimus_index = x.rn
        FROM (
            SELECT row_number() OVER (PARTITION BY f2.calendar_hash ORDER BY a.accepted_timestamp DESC, a.accession_id DESC, abs(c.calendar_period_size_diff_percentage), abs(c.calendar_end_offset), f2.fact_id DESC) as rn
                  ,f2.fact_id
            FROM accession a
            JOIN fact f2
              ON a.accession_id = f2.accession_id
            JOIN context c
              ON f2.context_id = c.context_id
            WHERE f2.calendar_hash = @hash_string
             ) AS x
        WHERE fact.fact_id = x.fact_id
          AND fact.calendar_ultimus_index <> x.rn


	return @@rowcount

	END;
GO
/****** Object:  UserDefinedFunction [dbo].[update_ultimus_index]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE FUNCTION [dbo].[update_ultimus_index](@hash_string VARBINARY) RETURNS integer
    AS 
	BEGIN

 		UPDATE fact 
		SET ultimus_index = x.rn
		FROM (
			SELECT row_number() OVER (PARTITION BY f2.fact_hash ORDER BY a.accepted_timestamp DESC, a.accession_id DESC, f2.fact_id DESC) as rn
					,f2.fact_id
			FROM accession a
			JOIN fact f2
				ON a.accession_id = f2.accession_id
			WHERE f2.fact_hash = @hash_string
				) AS x
		WHERE fact.fact_id = x.fact_id
			AND fact.ultimus_index <> x.rn
          
		return @@rowcount

	END;


GO
/****** Object:  Table [dbo].[dts_element]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[dts_element](
	[dts_element_id] [int] IDENTITY(1,1) NOT NULL,
	[dts_id] [int] NOT NULL,
	[element_id] [int] NOT NULL,
	[is_base] [bit] NOT NULL,
	[in_relationship] [bit] NOT NULL,
 CONSTRAINT [dts_element_pkey] PRIMARY KEY NONCLUSTERED 
(
	[dts_element_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[report_element]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[report_element](
	[report_element_id] [int] IDENTITY(1,1) NOT NULL,
	[report_id] [int] NOT NULL,
	[element_id] [int] NOT NULL,
	[is_base] [bit] NOT NULL,
	[primary_count] [int] NULL,
	[dimension_count] [int] NULL,
	[member_count] [int] NULL,
 CONSTRAINT [report_element_pkey] PRIMARY KEY NONCLUSTERED 
(
	[report_element_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[report]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[report](
	[report_id] [int] IDENTITY(1,1) NOT NULL,
	[source_id] [int] NOT NULL,
	[entity_id] [int] NOT NULL,
	[source_report_identifier] [nvarchar](800) NULL,
	[dts_id] [int] NOT NULL,
	[entry_dts_id] [int] NULL,
	[creation_timestamp] [datetime] NOT NULL,
	[accepted_timestamp] [datetime] NOT NULL,
	[is_most_current] [bit] NOT NULL,
	[entity_name] [varchar](max) NULL,
	[creation_software] [nvarchar](800) NULL,
	[entry_type] [nvarchar](300) NULL,
	[entry_url] [nvarchar](1000) NULL,
	[entry_document_id] [int] NOT NULL,
	[alternative_document_id] [int] NULL,
	[reporting_period_end_date] [datetime] NULL,
	[restatement_index] [int] NULL,
	[period_index] [int] NULL,
	[properties] [nvarchar](800) NULL,
 CONSTRAINT [report_pkey] PRIMARY KEY NONCLUSTERED 
(
	[report_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  View [dbo].[accession_element]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[accession_element] AS
 SELECT DISTINCT x.report_id, x.element_id, x.accession_element_id,
    x.report_id AS accession_id,

    x.is_base,
    x.primary_count,
    x.dimension_count,
    x.member_count
   FROM ( SELECT 1 AS sort_order,
            re.report_element_id AS accession_element_id,
            re.report_id,
            re.element_id,
            re.is_base,
            re.primary_count,
            re.dimension_count,
            re.member_count
           FROM dbo.report_element re
        UNION ALL
         SELECT 2 AS sort_order,
            de.dts_element_id AS accession_element_id,
            r.report_id,
            de.element_id,
            de.is_base,
            NULL AS int4,
            NULL AS int4,
            NULL AS int4
           FROM (dbo.report r
             JOIN dbo.dts_element de ON ((r.dts_id = de.dts_id)))
          WHERE de.in_relationship = 1) x

GO
/****** Object:  View [dbo].[accession_timestamp]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[accession_timestamp] AS
 SELECT report.report_id AS accession_id,
    report.creation_timestamp AS creation_time
   FROM dbo.report;
GO
/****** Object:  Table [dbo].[label_resource]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[label_resource](
	[resource_id] [int] NOT NULL,
	[label] [varchar](max) NULL,
	[xml_lang] [nvarchar](100) NULL,
 CONSTRAINT [label_resource_pk_label_resouce] PRIMARY KEY NONCLUSTERED 
(
	[resource_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[element]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[element](
	[element_id] [int] IDENTITY(1,1) NOT NULL,
	[qname_id] [int] NOT NULL,
	[datatype_qname_id] [int] NULL,
	[xbrl_base_datatype_qname_id] [int] NULL,
	[balance_id] [int] NULL,
	[period_type_id] [int] NULL,
	[substitution_group_qname_id] [int] NULL,
	[abstract] [bit] NOT NULL,
	[nillable] [bit] NOT NULL,
	[document_id] [int] NOT NULL,
	[is_numeric] [bit] NOT NULL,
	[is_monetary] [bit] NOT NULL,
	[is_tuple] [bit] NOT NULL,
 CONSTRAINT [element_pkey] PRIMARY KEY NONCLUSTERED 
(
	[element_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[qname]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[qname](
	[qname_id] [int] IDENTITY(1,1) NOT NULL,
	[namespace] [nvarchar](800) NULL,
	[local_name] [nvarchar](800) NULL,
 CONSTRAINT [qname_pkey] PRIMARY KEY NONCLUSTERED 
(
	[qname_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[dts_network]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[dts_network](
	[dts_network_id] [int] IDENTITY(1,1) NOT NULL,
	[dts_id] [int] NOT NULL,
	[extended_link_qname_id] [int] NOT NULL,
	[extended_link_role_uri_id] [int] NOT NULL,
	[arc_qname_id] [int] NOT NULL,
	[arcrole_uri_id] [int] NOT NULL,
	[description] [nvarchar](1000) NULL,
 CONSTRAINT [dts_network_pkey] PRIMARY KEY NONCLUSTERED 
(
	[dts_network_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[dts_relationship]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[dts_relationship](
	[dts_relationship_id] [int] IDENTITY(1,1) NOT NULL,
	[dts_network_id] [int] NOT NULL,
	[from_element_id] [int] NULL,
	[to_element_id] [int] NULL,
	[reln_order] [real] NULL,
	[from_resource_id] [int] NULL,
	[to_resource_id] [int] NULL,
	[calculation_weight] [real] NULL,
	[tree_sequence] [int] NOT NULL,
	[tree_depth] [int] NOT NULL,
	[preferred_label_role_uri_id] [int] NULL,
	[to_fact_id] [int] NULL,
	[from_fact_id] [int] NULL,
	[target_role_id] [int] NULL,
 CONSTRAINT [dts_relationship_relationship_pkey] PRIMARY KEY NONCLUSTERED 
(
	[dts_relationship_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[uri]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[uri](
	[uri_id] [int] IDENTITY(1,1) NOT NULL,
	[uri] [nvarchar](1000) NULL,
 CONSTRAINT [uri_pkey] PRIMARY KEY NONCLUSTERED 
(
	[uri_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[resource]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[resource](
	[resource_id] [int] IDENTITY(1,1) NOT NULL,
	[role_uri_id] [int] NULL,
	[qname_id] [int] NOT NULL,
	[document_id] [int] NOT NULL,
	[document_line_number] [int] NOT NULL,
	[document_column_number] [int] NOT NULL,
	[xml_location] [nvarchar](800) NULL,
 CONSTRAINT [resource_pkey] PRIMARY KEY NONCLUSTERED 
(
	[resource_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  View [dbo].[element_labels_view]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[element_labels_view] AS
 SELECT r.entity_id,
    r.entity_name,
    r.report_id,
    r.source_report_identifier AS filing_accession_number,
    r.dts_id,
    e.element_id,
    element_qname.namespace AS element_namespace,
    element_qname.local_name AS element_local_name,
    rel.dts_relationship_id,
    label_resource.resource_id AS label_resource_id,
    resource.role_uri_id AS label_role_uri_id,
    uri.uri AS label_role_uri,
    label_resource.label AS element_label,
    label_resource.xml_lang AS element_label_lang
   FROM (((((((dbo.dts_relationship rel
     JOIN dbo.dts_network n ON ((n.dts_network_id = rel.dts_network_id)))
     JOIN dbo.report r ON ((n.dts_id = r.dts_id)))
     JOIN dbo.element e ON ((rel.from_element_id = e.element_id)))
     JOIN dbo.qname element_qname ON ((element_qname.qname_id = e.qname_id)))
     JOIN dbo.label_resource ON ((rel.to_resource_id = label_resource.resource_id)))
     JOIN dbo.resource ON ((rel.to_resource_id = resource.resource_id)))
     JOIN dbo.uri ON ((uri.uri_id = resource.role_uri_id)));
GO
/****** Object:  Table [dbo].[fact]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[fact](
	[fact_id] [int] IDENTITY(1,1) NOT NULL,
	[accession_id] [int] NOT NULL,
	[context_id] [int] NULL,
	[unit_id] [int] NULL,
	[unit_base_id] [int] NULL,
	[element_id] [int] NOT NULL,
	[effective_value] [numeric](30, 6) NULL,
	[fact_value] [nvarchar](max) NULL,
	[xml_id] [nvarchar](800) NULL,
	[precision_value] [int] NULL,
	[decimals_value] [int] NULL,
	[is_precision_infinity] [bit] NOT NULL,
	[is_decimals_infinity] [bit] NOT NULL,
	[ultimus_index] [int] NULL,
	[calendar_ultimus_index] [int] NULL,
	[fiscal_ultimus_index] [int] NULL,
	[uom] [nvarchar](100) NULL,
	[is_extended] [bit] NULL,
	[fiscal_year] [int] NULL,
	[fiscal_period] [nvarchar](100) NULL,
	[calendar_year] [int] NULL,
	[calendar_period] [nvarchar](50) NULL,
	[tuple_fact_id] [int] NULL,
	[fact_hash] [varbinary](800) NULL,
	[calendar_hash] [varbinary](800) NULL,
	[fiscal_hash] [varbinary](800) NULL,
	[entity_id] [int] NULL,
	[element_namespace] [nvarchar](800) NULL,
	[element_local_name] [nvarchar](800) NULL,
	[dimension_count] [int] NULL,
	[inline_display_value] [nvarchar](800) NULL,
	[inline_scale] [int] NULL,
	[inline_negated] [bit] NULL,
	[inline_is_hidden] [bit] NULL,
	[inline_format_qname_id] [int] NULL,
	[access_level] [int] NULL,
 CONSTRAINT [fact_pkey1] PRIMARY KEY NONCLUSTERED 
(
	[fact_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  View [dbo].[fact_aug]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[fact_aug] AS
 SELECT fact.fact_id,
    fact.fact_hash,
    fact.ultimus_index,
    NULL AS current_index,
    fact.calendar_hash,
    fact.calendar_ultimus_index,
    fact.uom,
    fact.is_extended
   FROM dbo.fact;
GO
/****** Object:  Table [dbo].[context]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[context](
	[context_id] [int] IDENTITY(1,1) NOT NULL,
	[accession_id] [int] NOT NULL,
	[period_start] [datetime] NULL,
	[period_end] [datetime] NULL,
	[period_instant] [datetime] NULL,
	[specifies_dimensions] [bit] NOT NULL,
	[context_xml_id] [nvarchar](800) NULL,
	[entity_scheme] [nvarchar](800) NULL,
	[entity_identifier] [nvarchar](800) NULL,
	[fiscal_year] [int] NULL,
	[fiscal_period] [nvarchar](800) NULL,
	[context_hash] [varbinary](800) NULL,
	[dimension_hash] [varbinary](800) NULL,
	[calendar_year] [int] NULL,
	[calendar_period] [nvarchar](800) NULL,
	[calendar_start_offset] [numeric](30, 6) NULL,
	[calendar_end_offset] [numeric](30, 6) NULL,
	[calendar_period_size_diff_percentage] [real] NULL,
	[dimension_count] [int] NULL,
 CONSTRAINT [context_pkey] PRIMARY KEY NONCLUSTERED 
(
	[context_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  View [dbo].[context_aug]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[context_aug] AS
 SELECT context.context_id,
    context.fiscal_year,
    context.fiscal_period,
    context.context_hash,
    context.dimension_hash,
    context.calendar_year,
    context.calendar_period,
    context.calendar_start_offset,
    context.calendar_end_offset,
    context.calendar_period_size_diff_percentage
   FROM dbo.context;
GO
/****** Object:  Table [dbo].[source]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[source](
	[source_id] [int] IDENTITY(1,1) NOT NULL,
	[source_name] [nvarchar](50) NULL,
 CONSTRAINT [source_pkey] PRIMARY KEY NONCLUSTERED 
(
	[source_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  View [dbo].[accession]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[accession] AS
 SELECT r.report_id AS accession_id,
    r.accepted_timestamp,
    r.is_most_current,
    --((r.properties ->> 'filing_date'::text))::date AS filing_date,
	JSON_VALUE(r.properties,'$.filings_date') as filing_date ,
    r.entity_id,
    r.entity_name,
    r.creation_software,
    NULL AS creation_software_short,
    --((r.properties ->> 'standard_industrial_classification'::text))::integer AS standard_industrial_classification,
	JSON_VALUE(r.properties,'$.standard_industrial_classification') as standard_industrial_classification ,
    --(r.properties ->> 'state_of_incorporation'::text) AS state_of_incorporation,
	JSON_VALUE(r.properties,'$.state_of_incorporation') as state_of_incorporation ,
    --((r.properties ->> 'internal_revenue_service_number'::text))::integer AS internal_revenue_service_number,
	JSON_VALUE(r.properties,'$.internal_revenue_service_number') as internal_revenue_service_number ,
    --(r.properties ->> 'business_address'::text) AS business_address,
	JSON_VALUE(r.properties,'$.business_address') as business_address ,
    --(r.properties ->> 'business_phone'::text) AS business_phone,
	JSON_VALUE(r.properties,'$.business_phone') as business_phone ,
    --(r.properties ->> 'sec_html_url'::text) AS sec_html_url,
	JSON_VALUE(r.properties,'$.sec_html_url') as sec_html_url ,
    r.entry_url,
    r.source_report_identifier AS filing_accession_number,
    --(r.properties ->> 'zip_url'::text) AS zip_url,
	JSON_VALUE(r.properties,'$.zip_url') as zip_url ,
    --(r.properties ->> 'document_type'::text) AS document_type,
	JSON_VALUE(r.properties,'$.document_type') as document_type ,
    --((r.properties ->> 'percent_extended'::text))::integer AS percent_extended,
	JSON_VALUE(r.properties,'$.percent_extended') as percent_extended ,
    r.restatement_index,
    r.period_index,
    1 AS is_complete,
    r.entry_type,
    r.entry_document_id,
    r.alternative_document_id,
    r.reporting_period_end_date
   FROM (dbo.report r
     JOIN dbo.source s ON ((r.source_id = s.source_id)))
  WHERE (s.source_name = 'SEC');


GO
/****** Object:  View [dbo].[network]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[network] AS
 SELECT dn.dts_network_id AS network_id,
    r.report_id AS accession_id,
    dn.extended_link_qname_id,
    dn.extended_link_role_uri_id,
    dn.arc_qname_id,
    dn.arcrole_uri_id,
    dn.description
   FROM (dbo.report r
     JOIN dbo.dts_network dn ON (((dn.dts_id = r.dts_id) OR (dn.dts_id = r.entry_dts_id))));
GO
/****** Object:  Table [dbo].[dts_document]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[dts_document](
	[dts_document_id] [int] IDENTITY(1,1) NOT NULL,
	[dts_id] [int] NOT NULL,
	[top_level] [bit] NOT NULL,
	[document_id] [int] NOT NULL,
 CONSTRAINT [dts_document_pkey] PRIMARY KEY NONCLUSTERED 
(
	[dts_document_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[report_document]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[report_document](
	[report_document_id] [int] IDENTITY(1,1) NOT NULL,
	[report_id] [int] NOT NULL,
	[document_id] [int] NOT NULL,
 CONSTRAINT [report_document_pkey] PRIMARY KEY NONCLUSTERED 
(
	[report_document_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  View [dbo].[accession_document_association]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[accession_document_association] AS
 SELECT rd.report_document_id AS accession_document_association_id,
    r.report_id AS accession_id,
    rd.document_id
   FROM (dbo.report_document rd
     JOIN dbo.report r ON ((rd.report_id = r.report_id)))
UNION ALL
 SELECT dd.dts_document_id AS accession_document_association_id,
    r.report_id AS accession_id,
    dd.document_id
   FROM (dbo.report r
     JOIN dbo.dts_document dd ON ((r.dts_id = dd.dts_id)));
GO
/****** Object:  View [dbo].[relationship]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[relationship] AS
 SELECT dts_relationship.dts_relationship_id AS relationship_id,
    dts_relationship.dts_network_id AS network_id,
    dts_relationship.from_element_id,
    dts_relationship.to_element_id,
    dts_relationship.reln_order,
    dts_relationship.from_resource_id,
    dts_relationship.to_resource_id,
    dts_relationship.calculation_weight,
    dts_relationship.tree_sequence,
    dts_relationship.tree_depth,
    dts_relationship.preferred_label_role_uri_id,
    dts_relationship.to_fact_id,
    dts_relationship.from_fact_id,
    dts_relationship.target_role_id
   FROM dbo.dts_relationship;
GO
/****** Object:  Table [dbo].[entity]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[entity](
	[entity_id] [int] IDENTITY(1,1) NOT NULL,
	[entity_code] [nvarchar](800) NULL,
	[authority_scheme] [nvarchar](800) NULL,
	[entity_name] [nvarchar](max) NOT NULL,
 CONSTRAINT [entity_pkey] PRIMARY KEY NONCLUSTERED 
(
	[entity_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[custom_role_type]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[custom_role_type](
	[custom_role_type_id] [int] IDENTITY(1,1) NOT NULL,
	[uri_id] [int] NOT NULL,
	[definition] [nvarchar](800) NULL,
	[document_id] [int] NOT NULL,
 CONSTRAINT [custom_role_type_pkey] PRIMARY KEY NONCLUSTERED 
(
	[custom_role_type_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[document]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[document](
	[document_id] [int] IDENTITY(1,1) NOT NULL,
	[document_uri] [nvarchar](1000) NULL,
	[document_loaded] [bit] NOT NULL,
	[content] [nvarchar](800) NULL,
	[document_type] [nvarchar](800) NULL,
	[target_namespace] [nvarchar](800) NULL,
 CONSTRAINT [document_pkey] PRIMARY KEY NONCLUSTERED 
(
	[document_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  View [dbo].[calculation_view]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[calculation_view] AS
 SELECT entity.entity_id,
    entity.entity_name,
    accession.accession_id,
    accession.filing_accession_number,
    to_document.document_id,
    to_document.document_uri,
    elqname.namespace AS extended_link_namespace,
    elqname.local_name AS extended_link_local_name,
    elruri.uri AS extended_link_role_uri,
    custom_role_type.definition AS extended_link_role_title,
    arcqname.namespace AS arc_namespace,
    arcqname.local_name AS arc_local_name,
    arcroleuri.uri AS arcrole_uri,
    from_qname.namespace AS from_namespace,
    from_qname.local_name AS from_local_name,
    to_qname.namespace AS to_namespace,
    to_qname.local_name AS to_local_name,
    relationship.reln_order,
    relationship.tree_sequence,
    relationship.tree_depth
   FROM ((((((((((((((((dbo.relationship
     JOIN dbo.network ON ((network.network_id = relationship.network_id)))
     JOIN dbo.accession ON ((network.accession_id = accession.accession_id)))
     JOIN dbo.accession_document_association from_ada ON ((from_ada.accession_id = accession.accession_id)))
     JOIN dbo.accession_document_association to_ada ON ((to_ada.accession_id = accession.accession_id)))
     JOIN dbo.document to_document ON ((to_ada.document_id = to_document.document_id)))
     JOIN dbo.qname elqname ON ((network.extended_link_qname_id = elqname.qname_id)))
     JOIN dbo.uri elruri ON ((network.extended_link_role_uri_id = elruri.uri_id)))
     JOIN dbo.qname arcqname ON ((network.arc_qname_id = arcqname.qname_id)))
     JOIN dbo.uri arcroleuri ON ((network.arcrole_uri_id = arcroleuri.uri_id)))
     JOIN dbo.element from_element ON (((from_element.document_id = from_ada.document_id) AND (relationship.from_element_id = from_element.element_id))))
     JOIN dbo.qname from_qname ON ((from_element.qname_id = from_qname.qname_id)))
     JOIN dbo.element to_element ON (((to_element.document_id = to_ada.document_id) AND (relationship.to_element_id = to_element.element_id))))
     JOIN dbo.qname to_qname ON ((to_element.qname_id = to_qname.qname_id)))
     JOIN dbo.entity ON ((accession.entity_id = entity.entity_id)))
     JOIN dbo.accession_document_association cr_ada ON ((cr_ada.accession_id = accession.accession_id)))
     JOIN dbo.custom_role_type ON (((custom_role_type.uri_id = network.extended_link_role_uri_id) AND (custom_role_type.document_id = cr_ada.document_id))))
  WHERE ((arcqname.local_name) = 'calculationArc')

GO
/****** Object:  View [dbo].[relationship_view]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[relationship_view] AS
 SELECT relationship.relationship_id,
    network.extended_link_qname_id AS elqname_id,
    elqname.local_name AS el_local_name,
    network.extended_link_role_uri_id AS elroleuri_id,
    elroleuri.uri AS el_role_uri,
    network.arc_qname_id AS arcqname_id,
    arcqname.local_name AS arc_local_name,
    network.arcrole_uri_id AS arcroleuri_id,
    arcroleuri.uri AS arcroleuri,
    relationship.from_element_id,
    from_element_qname.local_name AS from_element_name,
    relationship.to_element_id,
    to_element_qname.local_name AS to_element_name,
    relationship.from_resource_id,
    from_resource_qname.local_name AS from_resource_name,
    relationship.to_resource_id,
    to_resource_qname.local_name AS to_resource_name,
    accession.accession_id,
    entity.entity_id,
    entity.entity_name
   FROM (((((((((((((((dbo.relationship
     JOIN dbo.network ON ((network.network_id = relationship.network_id)))
     JOIN dbo.accession ON ((network.accession_id = accession.accession_id)))
     JOIN dbo.qname elqname ON ((network.extended_link_qname_id = elqname.qname_id)))
     JOIN dbo.uri elroleuri ON ((network.extended_link_role_uri_id = elroleuri.uri_id)))
     JOIN dbo.qname arcqname ON ((network.arc_qname_id = arcqname.qname_id)))
     JOIN dbo.uri arcroleuri ON ((network.arcrole_uri_id = arcroleuri.uri_id)))
     LEFT JOIN dbo.element from_element ON ((relationship.from_element_id = from_element.element_id)))
     JOIN dbo.qname from_element_qname ON ((from_element.qname_id = from_element_qname.qname_id)))
     FULL JOIN dbo.element to_element ON ((relationship.to_element_id = to_element.element_id)))
     LEFT JOIN dbo.qname to_element_qname ON ((to_element.qname_id = to_element_qname.qname_id)))
     FULL JOIN dbo.resource from_resource ON ((relationship.from_resource_id = from_resource.resource_id)))
     LEFT JOIN dbo.qname from_resource_qname ON ((from_resource.qname_id = from_resource_qname.qname_id)))
     FULL JOIN dbo.resource to_resource ON ((relationship.to_resource_id = to_resource.resource_id)))
     LEFT JOIN dbo.qname to_resource_qname ON ((to_resource.qname_id = to_resource_qname.qname_id)))
     JOIN dbo.entity ON ((accession.entity_id = entity.entity_id)))

GO
/****** Object:  View [dbo].[relationship_full_view]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[relationship_full_view] AS
 SELECT relationship.relationship_id,
    network.extended_link_qname_id AS elqname_id,
    elqname.namespace AS el_namespace,
    elqname.local_name AS el_local_name,
    network.extended_link_role_uri_id AS elroleuri_id,
    elroleuri.uri AS el_role_uri,
    network.arc_qname_id AS arcqname_id,
    arcqname.namespace AS arc_namespace,
    arcqname.local_name AS arc_local_name,
    network.arcrole_uri_id AS arcroleuri_id,
    arcroleuri.uri AS arcroleuri,
    relationship.from_element_id,
    from_element_qname.namespace AS from_element_namespace,
    from_element_qname.local_name AS from_element_name,
    relationship.to_element_id,
    to_element_qname.namespace AS to_element_namespace,
    to_element_qname.local_name AS to_element_name,
    relationship.from_resource_id,
    from_resource_qname.namespace AS from_resource_namespace,
    from_resource_qname.local_name AS from_resource_name,
    relationship.to_resource_id,
    to_resource_qname.namespace AS to_resource_namespace,
    to_resource_qname.local_name AS to_resource_name,
    relationship.reln_order AS relationship_order,
    relationship.calculation_weight,
    relationship.tree_sequence,
    relationship.tree_depth,
    accession.accession_id,
    entity.entity_id,
    entity.entity_name
   FROM (((((((((((((((dbo.relationship
     JOIN dbo.network ON ((network.network_id = relationship.network_id)))
     JOIN dbo.accession ON ((network.accession_id = accession.accession_id)))
     JOIN dbo.qname elqname ON ((network.extended_link_qname_id = elqname.qname_id)))
     JOIN dbo.uri elroleuri ON ((network.extended_link_role_uri_id = elroleuri.uri_id)))
     JOIN dbo.qname arcqname ON ((network.arc_qname_id = arcqname.qname_id)))
     JOIN dbo.uri arcroleuri ON ((network.arcrole_uri_id = arcroleuri.uri_id)))
     LEFT JOIN dbo.element from_element ON ((relationship.from_element_id = from_element.element_id)))
     JOIN dbo.qname from_element_qname ON ((from_element.qname_id = from_element_qname.qname_id)))
     FULL JOIN dbo.element to_element ON ((relationship.to_element_id = to_element.element_id)))
     LEFT JOIN dbo.qname to_element_qname ON ((to_element.qname_id = to_element_qname.qname_id)))
     FULL JOIN dbo.resource from_resource ON ((relationship.from_resource_id = from_resource.resource_id)))
     LEFT JOIN dbo.qname from_resource_qname ON ((from_resource.qname_id = from_resource_qname.qname_id)))
     FULL JOIN dbo.resource to_resource ON ((relationship.to_resource_id = to_resource.resource_id)))
     LEFT JOIN dbo.qname to_resource_qname ON ((to_resource.qname_id = to_resource_qname.qname_id)))
     JOIN dbo.entity ON ((accession.entity_id = entity.entity_id)))
GO
/****** Object:  View [dbo].[presentation_view]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[presentation_view] AS
 SELECT entity.entity_id,
    entity.entity_name,
    accession.accession_id,
    accession.filing_accession_number,
    to_document.document_id,
    to_document.document_uri,
    elqname.namespace AS extended_link_namespace,
    elqname.local_name AS extended_link_local_name,
    elruri.uri AS extended_link_role_uri,
    custom_role_type.definition AS extended_link_role_title,
    arcqname.namespace AS arc_namespace,
    arcqname.local_name AS arc_local_name,
    arcroleuri.uri AS arcrole_uri,
    from_qname.namespace AS from_namespace,
    from_qname.local_name AS from_local_name,
    to_qname.namespace AS to_namespace,
    to_qname.local_name AS to_local_name,
    relationship.reln_order,
    relationship.tree_sequence,
    relationship.tree_depth
   FROM ((((((((((((((((dbo.relationship
     JOIN dbo.network ON ((network.network_id = relationship.network_id)))
     JOIN dbo.accession ON ((network.accession_id = accession.accession_id)))
     JOIN dbo.accession_document_association from_ada ON ((from_ada.accession_id = accession.accession_id)))
     JOIN dbo.accession_document_association to_ada ON ((to_ada.accession_id = accession.accession_id)))
     JOIN dbo.document to_document ON ((to_ada.document_id = to_document.document_id)))
     JOIN dbo.qname elqname ON ((network.extended_link_qname_id = elqname.qname_id)))
     JOIN dbo.uri elruri ON ((network.extended_link_role_uri_id = elruri.uri_id)))
     JOIN dbo.qname arcqname ON ((network.arc_qname_id = arcqname.qname_id)))
     JOIN dbo.uri arcroleuri ON ((network.arcrole_uri_id = arcroleuri.uri_id)))
     JOIN dbo.element from_element ON (((from_element.document_id = from_ada.document_id) AND (relationship.from_element_id = from_element.element_id))))
     JOIN dbo.qname from_qname ON ((from_element.qname_id = from_qname.qname_id)))
     JOIN dbo.element to_element ON (((to_element.document_id = to_ada.document_id) AND (relationship.to_element_id = to_element.element_id))))
     JOIN dbo.qname to_qname ON ((to_element.qname_id = to_qname.qname_id)))
     JOIN dbo.entity ON ((accession.entity_id = entity.entity_id)))
     JOIN dbo.accession_document_association cr_ada ON ((cr_ada.accession_id = accession.accession_id)))
     JOIN dbo.custom_role_type ON (((custom_role_type.uri_id = network.extended_link_role_uri_id) AND (custom_role_type.document_id = cr_ada.document_id))))
  WHERE ((arcqname.local_name) = 'presentationArc')

GO
/****** Object:  Table [dbo].[unit_report]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[unit_report](
	[unit_report_id] [int] IDENTITY(1,1) NOT NULL,
	[report_id] [int] NOT NULL,
	[unit_base_id] [int] NOT NULL,
	[unit_xml_id] [nvarchar](300) NULL,
 CONSTRAINT [unit_report_pkey] PRIMARY KEY NONCLUSTERED 
(
	[unit_report_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  View [dbo].[unit]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[unit] AS
 SELECT ur.unit_report_id AS unit_id,
    ur.report_id AS accession_id,
    ur.unit_xml_id
   FROM dbo.unit_report ur;

GO
/****** Object:  Table [dbo].[unit_measure_base]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[unit_measure_base](
	[unit_measure_base_id] [int] IDENTITY(1,1) NOT NULL,
	[unit_base_id] [int] NOT NULL,
	[qname_id] [int] NOT NULL,
	[location_id] [int] NULL,
 CONSTRAINT [unit_measure_base_pkey] PRIMARY KEY NONCLUSTERED 
(
	[unit_measure_base_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  View [dbo].[unit_measure]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[unit_measure] AS
 SELECT umb.unit_measure_base_id AS unit_measure_id,
    ur.unit_report_id AS unit_id,
    umb.qname_id,
    umb.location_id
   FROM (dbo.unit_measure_base umb
     JOIN dbo.unit_report ur ON ((umb.unit_base_id = ur.unit_base_id)));
GO
/****** Object:  Table [dbo].[context_dimension]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[context_dimension](
	[context_dimension_id] [int] IDENTITY(1,1) NOT NULL,
	[context_id] [int] NOT NULL,
	[dimension_qname_id] [int] NOT NULL,
	[member_qname_id] [int] NULL,
	[typed_qname_id] [int] NULL,
	[is_default] [bit] NOT NULL,
	[is_segment] [bit] NULL,
	[typed_text_content] [nvarchar](800) NULL,
 CONSTRAINT [context_dimension_pkey] PRIMARY KEY NONCLUSTERED 
(
	[context_dimension_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[enumeration_element_balance]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[enumeration_element_balance](
	[enumeration_element_balance_id] [int] IDENTITY(1,1) NOT NULL,
	[description] [nvarchar](800) NULL,
 CONSTRAINT [enumeration_element_balance_pkey] PRIMARY KEY NONCLUSTERED 
(
	[enumeration_element_balance_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[enumeration_element_period_type]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[enumeration_element_period_type](
	[enumeration_element_period_type_id] [int] IDENTITY(1,1) NOT NULL,
	[description] [nvarchar](800) NULL,
 CONSTRAINT [enumeration_element_period_type_pkey] PRIMARY KEY NONCLUSTERED 
(
	[enumeration_element_period_type_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[enumeration_unit_measure_location]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[enumeration_unit_measure_location](
	[enumeration_unit_measure_location_id] [int] IDENTITY(1,1) NOT NULL,
	[description] [nvarchar](800) NULL,
 CONSTRAINT [enumeration_unit_measure_location_pkey] PRIMARY KEY NONCLUSTERED 
(
	[enumeration_unit_measure_location_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  View [dbo].[fact_element_view]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[fact_element_view] AS
 SELECT entity.entity_id,
    entity.entity_name,
    accession.accession_id,
    accession.filing_accession_number,
    context.context_id,
    context.context_xml_id,
    context.period_start,
    context.period_end,
    context.period_instant,
    context_dimension.context_dimension_id,
    contextdimensionqname.local_name AS context_dimension_qname,
    contextdimensionmemberqname.local_name AS dimension_member_qname,
    element.element_id,
    elementqname.local_name AS element_qname,
    elementbasedatatypeqname.local_name AS element_base_datatype,
    elementdatatypeqname.local_name AS element_datatype,
    elementsubgroupqname.local_name AS element_substitution_group,
    enumeration_element_balance.description AS balance,
    enumeration_element_period_type.description AS period_type,
    element.abstract,
    element.nillable,
    fact.fact_id,
    fact.fact_value,
    unit.unit_id,
    unit.unit_xml_id,
    unit_measure.unit_measure_id,
    unitmeasureqname.local_name AS unit_measure_qname,
    enumeration_unit_measure_location.description AS location
   FROM (((((((((((((((((dbo.fact
     JOIN dbo.accession ON ((fact.accession_id = accession.accession_id)))
     JOIN dbo.entity ON ((accession.entity_id = entity.entity_id)))
     JOIN dbo.element ON ((fact.element_id = element.element_id)))
     JOIN dbo.qname elementqname ON ((element.qname_id = elementqname.qname_id)))
     JOIN dbo.qname elementbasedatatypeqname ON ((element.xbrl_base_datatype_qname_id = elementbasedatatypeqname.qname_id)))
     JOIN dbo.qname elementdatatypeqname ON ((element.datatype_qname_id = elementdatatypeqname.qname_id)))
     JOIN dbo.qname elementsubgroupqname ON ((element.substitution_group_qname_id = elementsubgroupqname.qname_id)))
     JOIN dbo.context ON ((fact.context_id = context.context_id)))
     JOIN dbo.enumeration_element_balance ON ((enumeration_element_balance.enumeration_element_balance_id = element.balance_id)))
     JOIN dbo.enumeration_element_period_type ON ((enumeration_element_period_type.enumeration_element_period_type_id = element.period_type_id)))
     LEFT JOIN dbo.context_dimension ON ((context_dimension.context_id = context.context_id)))
     LEFT JOIN dbo.qname contextdimensionqname ON ((context_dimension.dimension_qname_id = contextdimensionqname.qname_id)))
     LEFT JOIN dbo.qname contextdimensionmemberqname ON ((context_dimension.member_qname_id = contextdimensionmemberqname.qname_id)))
     LEFT JOIN dbo.unit ON ((fact.unit_id = unit.unit_id)))
     LEFT JOIN dbo.unit_measure ON ((unit_measure.unit_id = unit.unit_id)))
     LEFT JOIN dbo.qname unitmeasureqname ON ((unit_measure.qname_id = unitmeasureqname.qname_id)))
     LEFT JOIN dbo.enumeration_unit_measure_location ON ((enumeration_unit_measure_location.enumeration_unit_measure_location_id = unit_measure.location_id)))

GO
/****** Object:  View [dbo].[fact_dei_view]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[fact_dei_view] AS
 SELECT qname.local_name,
    qname.namespace,
    entity.entity_name,
    entity.entity_code,
    entity.entity_id,
    dimension.axis,
    dimension.member,
    fact.fact_value,
    fact.effective_value AS amount,
    context.period_start,
    context.period_end,
    context.period_instant,
    accession.filing_date,
    accession.filing_accession_number,
    accession.accession_id
   FROM dbo.qname,
    dbo.element,
    dbo.fact,
    dbo.entity,
    dbo.accession,
    (dbo.context
     LEFT JOIN ( SELECT axis_qname.local_name AS axis,
            member_qname.local_name AS member,
            context_dimension.context_id
           FROM dbo.context_dimension,
            dbo.qname axis_qname,
            dbo.qname member_qname
          WHERE (((context_dimension.is_segment = 1) AND (axis_qname.qname_id = context_dimension.dimension_qname_id)) AND (member_qname.qname_id = context_dimension.member_qname_id))) dimension ON ((context.context_id = dimension.context_id)))
  WHERE (((((
  (qname.qname_id = element.qname_id) 
 -- AND (substring(qname.namespace, '[^0-9]*', 'http://xbrl.us/dei/'))
 ) 
  AND (element.element_id = fact.element_id)) AND (fact.accession_id = accession.accession_id)) 
  AND (accession.entity_id = entity.entity_id)) 
  AND (fact.context_id = context.context_id));

GO
/****** Object:  View [dbo].[definition_view]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[definition_view] AS
 SELECT entity.entity_id,
    entity.entity_name,
    accession.accession_id,
    accession.filing_accession_number,
    to_document.document_id,
    to_document.document_uri,
    elqname.namespace AS extended_link_namespace,
    elqname.local_name AS extended_link_local_name,
    elruri.uri AS extended_link_role_uri,
    custom_role_type.definition AS extended_link_role_title,
    arcqname.namespace AS arc_namespace,
    arcqname.local_name AS arc_local_name,
    arcroleuri.uri AS arcrole_uri,
    from_qname.namespace AS from_namespace,
    from_qname.local_name AS from_local_name,
    to_qname.namespace AS to_namespace,
    to_qname.local_name AS to_local_name,
    relationship.reln_order,
    relationship.tree_sequence,
    relationship.tree_depth
   FROM ((((((((((((((((dbo.relationship
     JOIN dbo.network ON ((network.network_id = relationship.network_id)))
     JOIN dbo.accession ON ((network.accession_id = accession.accession_id)))
     JOIN dbo.accession_document_association from_ada ON ((from_ada.accession_id = accession.accession_id)))
     JOIN dbo.accession_document_association to_ada ON ((to_ada.accession_id = accession.accession_id)))
     JOIN dbo.document to_document ON ((to_ada.document_id = to_document.document_id)))
     JOIN dbo.qname elqname ON ((network.extended_link_qname_id = elqname.qname_id)))
     JOIN dbo.uri elruri ON ((network.extended_link_role_uri_id = elruri.uri_id)))
     JOIN dbo.qname arcqname ON ((network.arc_qname_id = arcqname.qname_id)))
     JOIN dbo.uri arcroleuri ON ((network.arcrole_uri_id = arcroleuri.uri_id)))
     JOIN dbo.element from_element ON (((from_element.document_id = from_ada.document_id) AND (relationship.from_element_id = from_element.element_id))))
     JOIN dbo.qname from_qname ON ((from_element.qname_id = from_qname.qname_id)))
     JOIN dbo.element to_element ON (((to_element.document_id = to_ada.document_id) AND (relationship.to_element_id = to_element.element_id))))
     JOIN dbo.qname to_qname ON ((to_element.qname_id = to_qname.qname_id)))
     JOIN dbo.entity ON ((accession.entity_id = entity.entity_id)))
     JOIN dbo.accession_document_association cr_ada ON ((cr_ada.accession_id = accession.accession_id)))
     JOIN dbo.custom_role_type ON (((custom_role_type.uri_id = network.extended_link_role_uri_id) AND (custom_role_type.document_id = cr_ada.document_id))))
  WHERE (((arcqname.local_name) <> 'calculationArc') AND ((arcqname.local_name) <> 'presentationArc'))


GO
/****** Object:  View [dbo].[accession_industry_div]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE VIEW [dbo].[accession_industry_div] AS
 SELECT accession.accession_id,
    accession.filing_date,
    accession.entity_id,
    accession.creation_software,
    accession.standard_industrial_classification,
    accession.state_of_incorporation,
    accession.internal_revenue_service_number,
    accession.business_address,
    accession.business_phone,
    accession.sec_html_url,
    accession.entry_url,
    accession.filing_accession_number,
    foo2.sic_l1,
    foo2.division_no
   FROM dbo.accession,
    ( SELECT accession_1.standard_industrial_classification,
            accession_1.accession_id,
            foo.sic_l1,
                CASE
                    WHEN ((foo.sic_l1 < (10)) AND (foo.sic_l1 >= (1))) THEN '1'
                    WHEN ((foo.sic_l1 < (15)) AND (foo.sic_l1 >= (10))) THEN '2'
                    WHEN ((foo.sic_l1 < (18)) AND (foo.sic_l1 >= (15))) THEN '3'
                    WHEN ((foo.sic_l1 < (22)) AND (foo.sic_l1 >= (20))) THEN '4'
                    WHEN ((foo.sic_l1 < (40)) AND (foo.sic_l1 >= (22))) THEN '5'
                    WHEN ((foo.sic_l1 < (50)) AND (foo.sic_l1 >= (40))) THEN '6'
                    WHEN ((foo.sic_l1 < (52)) AND (foo.sic_l1 >= (50))) THEN '7'
                    WHEN ((foo.sic_l1 < (60)) AND (foo.sic_l1 >= (52))) THEN '8'
                    WHEN ((foo.sic_l1 < (68)) AND (foo.sic_l1 >= (60))) THEN '9'
                    WHEN ((foo.sic_l1 < (89)) AND (foo.sic_l1 >= (70))) THEN '10 '
                    WHEN (foo.sic_l1 < (1)) THEN '11'
                    WHEN (foo.sic_l1 >= (89)) THEN '12'
                    ELSE NULL
                END AS division_no
           FROM dbo.accession accession_1,
            ( SELECT 
				(accession_2.standard_industrial_classification / 100) AS sic_l1,
                accession_2.accession_id
                FROM dbo.accession accession_2) 
				   foo
          WHERE (accession_1.accession_id = foo.accession_id)) foo2
  WHERE (foo2.accession_id = accession.accession_id);

GO
/****** Object:  Table [dbo].[attribute_value]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[attribute_value](
	[attribute_value_id] [int] IDENTITY(1,1) NOT NULL,
	[qname_id] [int] NOT NULL,
	[text_value] [nvarchar](800) NULL,
 CONSTRAINT [attribute_value_pkey] PRIMARY KEY NONCLUSTERED 
(
	[attribute_value_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[base_namespace]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[base_namespace](
	[base_namespace_id] [int] IDENTITY(1,1) NOT NULL,
	[preface] [nvarchar](800) NULL,
	[prefix_expression] [nvarchar](800) NULL,
	[source_id] [int] NOT NULL,
 CONSTRAINT [base_namespace_pkey] PRIMARY KEY NONCLUSTERED 
(
	[base_namespace_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[config]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[config](
	[keyword] [varchar](1) NOT NULL,
	[value_numeric] [numeric](18, 0) NULL,
	[value_string] [varchar](1) NULL
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[context_dimension_explicit]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[context_dimension_explicit](
	[context_dimension_id] [int] NOT NULL,
	[context_id] [int] NOT NULL,
	[dimension_qname_id] [int] NOT NULL,
	[member_qname_id] [int] NULL,
	[typed_qname_id] [int] NULL,
	[is_default] [bit] NOT NULL,
	[is_segment] [bit] NULL,
	[typed_text_content] [nvarchar](800) NULL,
	[dimension_namespace] [nvarchar](300) NULL,
	[dimension_local_name] [nvarchar](800) NULL,
	[member_namespace] [nvarchar](300) NULL,
	[member_local_name] [nvarchar](300) NULL,
 CONSTRAINT [context_dimension_explicit_pkey] PRIMARY KEY NONCLUSTERED 
(
	[context_dimension_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[custom_arcrole_type]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[custom_arcrole_type](
	[custom_arcrole_type_id] [int] IDENTITY(1,1) NOT NULL,
	[document_id] [int] NOT NULL,
	[uri_id] [int] NOT NULL,
	[definition] [nvarchar](800) NULL,
	[cycles_allowed] [int] NOT NULL,
 CONSTRAINT [custom_arcrole_type_pkey] PRIMARY KEY NONCLUSTERED 
(
	[custom_arcrole_type_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[custom_arcrole_used_on]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[custom_arcrole_used_on](
	[custom_arcrole_used_on_id] [int] IDENTITY(1,1) NOT NULL,
	[custom_arcrole_type_id] [int] NOT NULL,
	[qname_id] [int] NOT NULL,
 CONSTRAINT [custom_arcrole_used_on_pkey] PRIMARY KEY NONCLUSTERED 
(
	[custom_arcrole_used_on_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[custom_role_used_on]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[custom_role_used_on](
	[custom_role_used_on_id] [int] IDENTITY(1,1) NOT NULL,
	[custom_role_type_id] [int] NOT NULL,
	[qname_id] [int] NOT NULL,
 CONSTRAINT [custom_role_used_on_used_on_pkey] PRIMARY KEY NONCLUSTERED 
(
	[custom_role_used_on_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[document_structure]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[document_structure](
	[document_structure_id] [int] IDENTITY(1,1) NOT NULL,
	[parent_document_id] [int] NOT NULL,
	[child_document_id] [int] NOT NULL,
 CONSTRAINT [document_structure_pkey] PRIMARY KEY NONCLUSTERED 
(
	[document_structure_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[dts]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[dts](
	[dts_id] [int] IDENTITY(1,1) NOT NULL,
	[dts_hash] [varbinary](800) NULL,
	[dts_name] [nvarchar](300) NULL,
 CONSTRAINT [dts_pkey] PRIMARY KEY NONCLUSTERED 
(
	[dts_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[element_attribute_value_association]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[element_attribute_value_association](
	[element_attribute_value_association_id] [int] IDENTITY(1,1) NOT NULL,
	[element_id] [int] NOT NULL,
	[attribute_value_id] [int] NOT NULL,
 CONSTRAINT [element_attribute_value_association_element_attribute_association_pkey] PRIMARY KEY NONCLUSTERED 
(
	[element_attribute_value_association_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[entity_identifier]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[entity_identifier](
	[entity_identifier_id] [int] IDENTITY(1,1) NOT NULL,
	[entity_id] [int] NOT NULL,
	[scheme] [nvarchar](800) NULL,
	[entity_identifier] [nvarchar](800) NULL,
 CONSTRAINT [entity_identifier_pkey] PRIMARY KEY NONCLUSTERED 
(
	[entity_identifier_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[entity_name_history]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[entity_name_history](
	[entity_name_history_id] [int] IDENTITY(1,1) NOT NULL,
	[entity_id] [int] NOT NULL,
	[accession_id] [int] NOT NULL,
	[entity_name] [nvarchar](800) NULL,
 CONSTRAINT [entity_name_history_pkey] PRIMARY KEY NONCLUSTERED 
(
	[entity_name_history_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[entity_source]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[entity_source](
	[entity_source_id] [int] IDENTITY(1,1) NOT NULL,
	[entity_id] [int] NOT NULL,
	[source_id] [int] NOT NULL,
 CONSTRAINT [entity_source_pkey] PRIMARY KEY NONCLUSTERED 
(
	[entity_source_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[enumeration_arcrole_cycles_allowed]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[enumeration_arcrole_cycles_allowed](
	[enumeration_arcrole_cycles_allowed_id] [int] IDENTITY(1,1) NOT NULL,
	[description] [nvarchar](800) NULL,
 CONSTRAINT [enumeration_arcrole_cycles_allowed_pkey] PRIMARY KEY NONCLUSTERED 
(
	[enumeration_arcrole_cycles_allowed_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[footnote_resource]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[footnote_resource](
	[resource_id] [int] NOT NULL,
	[footnote] [nvarchar](max) NULL,
	[xml_lang] [nvarchar](100) NULL,
	[access_level] [int] NULL,
 CONSTRAINT [footnote_resource_pk_footnote_resouce] PRIMARY KEY NONCLUSTERED 
(
	[resource_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[namespace]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[namespace](
	[namespace_id] [int] IDENTITY(1,1) NOT NULL,
	[uri] [nvarchar](1000) NULL,
	[is_base] [bit] NOT NULL,
	[taxonomy_version_id] [int] NULL,
	[prefix] [nvarchar](1000) NULL,
	[name] [nvarchar](800) NULL,
 CONSTRAINT [namespace_pkey] PRIMARY KEY NONCLUSTERED 
(
	[namespace_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[namespace_source]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[namespace_source](
	[namespace_source_id] [int] IDENTITY(1,1) NOT NULL,
	[namespace_id] [int] NOT NULL,
	[source_id] [int] NOT NULL,
	[is_base] [bit] NOT NULL,
 CONSTRAINT [namespace_source_pkey] PRIMARY KEY NONCLUSTERED 
(
	[namespace_source_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[reference_part]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[reference_part](
	[reference_part_id] [int] IDENTITY(1,1) NOT NULL,
	[resource_id] [int] NOT NULL,
	[value] [nvarchar](800) NULL,
	[qname_id] [int] NOT NULL,
	[ref_order] [int] NULL,
 CONSTRAINT [reference_part_pkey] PRIMARY KEY NONCLUSTERED 
(
	[reference_part_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[standard_role_definition]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[standard_role_definition](
	[standard_role_definition_id] [int] IDENTITY(1,1) NOT NULL,
	[uri] [nvarchar](800) NULL,
	[label] [nvarchar](800) NULL,
	[definition] [nvarchar](800) NULL,
 CONSTRAINT [standard_role_definition_pkey] PRIMARY KEY NONCLUSTERED 
(
	[standard_role_definition_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[taxonomy]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[taxonomy](
	[taxonomy_id] [int] IDENTITY(1,1) NOT NULL,
	[name] [nvarchar](800) NULL,
	[rank] [int] NULL,
 CONSTRAINT [taxonomy_pkey] PRIMARY KEY NONCLUSTERED 
(
	[taxonomy_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[taxonomy_version]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[taxonomy_version](
	[taxonomy_version_id] [int] IDENTITY(1,1) NOT NULL,
	[taxonomy_id] [int] NOT NULL,
	[version] [nvarchar](800) NULL,
	[identifier_document_id] [int] NULL,
 CONSTRAINT [taxonomy_version_pkey] PRIMARY KEY NONCLUSTERED 
(
	[taxonomy_version_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[taxonomy_version_dts]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[taxonomy_version_dts](
	[taxonomy_version_dts_id] [int] IDENTITY(1,1) NOT NULL,
	[taxonomy_version_id] [int] NOT NULL,
	[dts_id] [int] NOT NULL,
 CONSTRAINT [taxonomy_version_dts_pkey] PRIMARY KEY NONCLUSTERED 
(
	[taxonomy_version_dts_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[unit_base]    Script Date: 5/22/2020 1:58:39 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[unit_base](
	[unit_base_id] [int] IDENTITY(1,1) NOT NULL,
	[unit_hash] [varbinary](800) NULL,
	[unit_hash_string] [nvarchar](800) NULL,
	[unit_string] [nvarchar](300) NULL,
 CONSTRAINT [unit_base_pkey] PRIMARY KEY NONCLUSTERED 
(
	[unit_base_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [attribute_value_index01]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [attribute_value_index01] ON [dbo].[attribute_value]
(
	[qname_id] ASC,
	[text_value] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [base_namespace_index01]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [base_namespace_index01] ON [dbo].[base_namespace]
(
	[source_id] ASC,
	[preface] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_index01]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_index01] ON [dbo].[context]
(
	[accession_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_index02]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_index02] ON [dbo].[context]
(
	[accession_id] ASC,
	[context_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_index03]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_index03] ON [dbo].[context]
(
	[context_id] ASC,
	[accession_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [context_index04]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_index04] ON [dbo].[context]
(
	[fiscal_year] ASC,
	[fiscal_period] ASC,
	[context_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_index05]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_index05] ON [dbo].[context]
(
	[fiscal_year] ASC,
	[context_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [context_index06]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_index06] ON [dbo].[context]
(
	[fiscal_period] ASC,
	[context_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [context_index07]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_index07] ON [dbo].[context]
(
	[fiscal_period] ASC,
	[fiscal_year] ASC,
	[context_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [context_index08]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_index08] ON [dbo].[context]
(
	[entity_identifier] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_dimension_conext_dimension_index03]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_conext_dimension_index03] ON [dbo].[context_dimension]
(
	[member_qname_id] ASC,
	[dimension_qname_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_dimension_index01]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_index01] ON [dbo].[context_dimension]
(
	[context_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_dimension_index02]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_index02] ON [dbo].[context_dimension]
(
	[dimension_qname_id] ASC,
	[member_qname_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_dimension_index03]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_index03] ON [dbo].[context_dimension]
(
	[dimension_qname_id] ASC,
	[member_qname_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_dimension_index04]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_index04] ON [dbo].[context_dimension]
(
	[member_qname_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_dimension_index05]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_index05] ON [dbo].[context_dimension]
(
	[dimension_qname_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_dimension_index06]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_index06] ON [dbo].[context_dimension]
(
	[dimension_qname_id] ASC,
	[context_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_dimension_explicit_index01]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_explicit_index01] ON [dbo].[context_dimension_explicit]
(
	[context_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_dimension_explicit_index02]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_explicit_index02] ON [dbo].[context_dimension_explicit]
(
	[dimension_qname_id] ASC,
	[member_qname_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_dimension_explicit_index03]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_explicit_index03] ON [dbo].[context_dimension_explicit]
(
	[member_qname_id] ASC,
	[dimension_qname_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_dimension_explicit_index04]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_explicit_index04] ON [dbo].[context_dimension_explicit]
(
	[member_qname_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_dimension_explicit_index05]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_explicit_index05] ON [dbo].[context_dimension_explicit]
(
	[dimension_qname_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [context_dimension_explicit_index06]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_explicit_index06] ON [dbo].[context_dimension_explicit]
(
	[dimension_qname_id] ASC,
	[context_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [context_dimension_explicit_index07]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_explicit_index07] ON [dbo].[context_dimension_explicit]
(
	[dimension_local_name] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [context_dimension_explicit_index08]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_explicit_index08] ON [dbo].[context_dimension_explicit]
(
	[member_local_name] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [context_dimension_explicit_index09]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_explicit_index09] ON [dbo].[context_dimension_explicit]
(
	[typed_text_content] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [context_dimension_explicit_index10]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_explicit_index10] ON [dbo].[context_dimension_explicit]
(
	[dimension_local_name] ASC,
	[member_local_name] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [context_dimension_explicit_index11]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_explicit_index11] ON [dbo].[context_dimension_explicit]
(
	[dimension_namespace] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [context_dimension_explicit_index12]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [context_dimension_explicit_index12] ON [dbo].[context_dimension_explicit]
(
	[member_namespace] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [custom_arcrole_type_index01]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [custom_arcrole_type_index01] ON [dbo].[custom_arcrole_type]
(
	[document_id] ASC,
	[uri_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [custom_arcrole_type_index02]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [custom_arcrole_type_index02] ON [dbo].[custom_arcrole_type]
(
	[document_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [custom_role_type_index01]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [custom_role_type_index01] ON [dbo].[custom_role_type]
(
	[uri_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [custom_role_type_index02]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [custom_role_type_index02] ON [dbo].[custom_role_type]
(
	[document_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [custom_role_used_on_ix]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [custom_role_used_on_ix] ON [dbo].[custom_role_used_on]
(
	[custom_role_type_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [used_on_pkey]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [used_on_pkey] ON [dbo].[custom_role_used_on]
(
	[custom_role_used_on_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [document_index01]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [document_index01] ON [dbo].[document]
(
	[document_uri] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [document_structure_index01]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [document_structure_index01] ON [dbo].[document_structure]
(
	[parent_document_id] ASC,
	[child_document_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [dts_index01]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [dts_index01] ON [dbo].[dts]
(
	[dts_hash] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [dts_document_index01]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [dts_document_index01] ON [dbo].[dts_document]
(
	[dts_id] ASC,
	[document_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [dts_document_index02]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [dts_document_index02] ON [dbo].[dts_document]
(
	[document_id] ASC,
	[dts_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [dts_element_index01]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [dts_element_index01] ON [dbo].[dts_element]
(
	[dts_id] ASC,
	[element_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [dts_element_index02]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [dts_element_index02] ON [dbo].[dts_element]
(
	[element_id] ASC,
	[dts_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [dts_network_index01]    Script Date: 5/22/2020 1:58:39 PM ******/
CREATE NONCLUSTERED INDEX [dts_network_index01] ON [dbo].[dts_network]
(
	[dts_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [dts_network_index02]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [dts_network_index02] ON [dbo].[dts_network]
(
	[arcrole_uri_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [relationship_element_resource_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [relationship_element_resource_index01] ON [dbo].[dts_relationship]
(
	[from_element_id] ASC,
	[to_resource_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [relationship_element_resource_index02]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [relationship_element_resource_index02] ON [dbo].[dts_relationship]
(
	[to_resource_id] ASC,
	[from_element_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [relationship_from_res_ix]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [relationship_from_res_ix] ON [dbo].[dts_relationship]
(
	[from_resource_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [relationship_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [relationship_index01] ON [dbo].[dts_relationship]
(
	[from_element_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [relationship_index02]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [relationship_index02] ON [dbo].[dts_relationship]
(
	[dts_network_id] ASC,
	[to_element_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [relationship_index03]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [relationship_index03] ON [dbo].[dts_relationship]
(
	[dts_network_id] ASC,
	[from_element_id] ASC,
	[to_element_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [relationship_pkey]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [relationship_pkey] ON [dbo].[dts_relationship]
(
	[dts_relationship_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [relationship_to_res_ix]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [relationship_to_res_ix] ON [dbo].[dts_relationship]
(
	[to_resource_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [element_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [element_index01] ON [dbo].[element]
(
	[document_id] ASC,
	[qname_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [element_index02]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [element_index02] ON [dbo].[element]
(
	[qname_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [element_index03]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [element_index03] ON [dbo].[element]
(
	[qname_id] ASC,
	[element_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [element_index04]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [element_index04] ON [dbo].[element]
(
	[datatype_qname_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [element_index05]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [element_index05] ON [dbo].[element]
(
	[xbrl_base_datatype_qname_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [element_attribute_association_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [element_attribute_association_index01] ON [dbo].[element_attribute_value_association]
(
	[element_id] ASC,
	[attribute_value_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [element_attribute_association_pkey]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [element_attribute_association_pkey] ON [dbo].[element_attribute_value_association]
(
	[element_attribute_value_association_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [entity_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [entity_index01] ON [dbo].[entity]
(
	[authority_scheme] ASC,
	[entity_code] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [entity_index02]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [entity_index02] ON [dbo].[entity]
(
	[entity_code] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [entity_name_history_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [entity_name_history_index01] ON [dbo].[entity_name_history]
(
	[entity_id] ASC,
	[accession_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [entity_source_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [entity_source_index01] ON [dbo].[entity_source]
(
	[source_id] ASC,
	[entity_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [fact_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index01] ON [dbo].[fact]
(
	[element_id] ASC,
	[accession_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [fact_index02]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index02] ON [dbo].[fact]
(
	[element_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [fact_index03]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index03] ON [dbo].[fact]
(
	[unit_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [fact_index04]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index04] ON [dbo].[fact]
(
	[context_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [fact_index05]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index05] ON [dbo].[fact]
(
	[accession_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [fact_index06]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index06] ON [dbo].[fact]
(
	[context_id] ASC,
	[element_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [fact_index07]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index07] ON [dbo].[fact]
(
	[element_id] ASC,
	[context_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [fact_index08]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index08] ON [dbo].[fact]
(
	[element_id] ASC,
	[ultimus_index] ASC,
	[uom] ASC,
	[fiscal_year] ASC,
	[fiscal_period] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [fact_index09]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index09] ON [dbo].[fact]
(
	[element_id] ASC,
	[calendar_ultimus_index] ASC,
	[uom] ASC,
	[calendar_year] ASC,
	[calendar_period] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [fact_index10]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index10] ON [dbo].[fact]
(
	[fact_hash] ASC,
	[fact_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [fact_index11]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index11] ON [dbo].[fact]
(
	[fact_id] ASC,
	[calendar_hash] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [fact_index12]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index12] ON [dbo].[fact]
(
	[fact_id] ASC,
	[fact_hash] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [fact_index13]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index13] ON [dbo].[fact]
(
	[fact_id] ASC,
	[calendar_hash] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [fact_index14]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index14] ON [dbo].[fact]
(
	[ultimus_index] ASC,
	[fact_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [fact_index15]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index15] ON [dbo].[fact]
(
	[fact_id] ASC,
	[ultimus_index] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [fact_index16]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index16] ON [dbo].[fact]
(
	[fact_id] ASC,
	[ultimus_index] ASC,
	[calendar_ultimus_index] ASC,
	[uom] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [fact_index17]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index17] ON [dbo].[fact]
(
	[fiscal_ultimus_index] ASC,
	[fact_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [fact_index18]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index18] ON [dbo].[fact]
(
	[fact_id] ASC,
	[fiscal_ultimus_index] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [fact_index19]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index19] ON [dbo].[fact]
(
	[fiscal_hash] ASC,
	[fact_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [fact_index20]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index20] ON [dbo].[fact]
(
	[tuple_fact_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [fact_index21]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index21] ON [dbo].[fact]
(
	[unit_base_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [fact_index24]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index24] ON [dbo].[fact]
(
	[element_local_name] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [fact_index25]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index25] ON [dbo].[fact]
(
	[entity_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [fact_index26]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [fact_index26] ON [dbo].[fact]
(
	[element_namespace] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [pk_footnote_resouce]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [pk_footnote_resouce] ON [dbo].[footnote_resource]
(
	[resource_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [label_resource_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [label_resource_index01] ON [dbo].[label_resource]
(
	[resource_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [pk_label_resouce]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [pk_label_resouce] ON [dbo].[label_resource]
(
	[resource_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [namespace_idx01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [namespace_idx01] ON [dbo].[namespace]
(
	[uri] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [namespace_idx02]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [namespace_idx02] ON [dbo].[namespace]
(
	[is_base] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [namespace_source_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [namespace_source_index01] ON [dbo].[namespace_source]
(
	[namespace_id] ASC,
	[source_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [qname_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [qname_index01] ON [dbo].[qname]
(
	[qname_id] ASC,
	[namespace] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [qname_index02]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [qname_index02] ON [dbo].[qname]
(
	[local_name] ASC,
	[namespace] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [qname_index03]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [qname_index03] ON [dbo].[qname]
(
	[local_name] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [qname_index04]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [qname_index04] ON [dbo].[qname]
(
	[namespace] ASC,
	[qname_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [qname_index05]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [qname_index05] ON [dbo].[qname]
(
	[namespace] ASC,
	[local_name] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [qname_index07]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [qname_index07] ON [dbo].[qname]
(
	[local_name] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [reference_part_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [reference_part_index01] ON [dbo].[reference_part]
(
	[qname_id] ASC,
	[resource_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [reference_part_index02]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [reference_part_index02] ON [dbo].[reference_part]
(
	[resource_id] ASC,
	[qname_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [report_index_05]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [report_index_05] ON [dbo].[report]
(
	[source_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [report_index_06]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [report_index_06] ON [dbo].[report]
(
	[dts_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [report_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [report_index01] ON [dbo].[report]
(
	[source_report_identifier] ASC,
	[source_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [report_index02]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [report_index02] ON [dbo].[report]
(
	[entity_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [report_index03]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [report_index03] ON [dbo].[report]
(
	[accepted_timestamp] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [report_index04]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [report_index04] ON [dbo].[report]
(
	[properties] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [report_document_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [report_document_index01] ON [dbo].[report_document]
(
	[report_id] ASC,
	[document_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [report_document_index02]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [report_document_index02] ON [dbo].[report_document]
(
	[document_id] ASC,
	[report_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [report_element_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [report_element_index01] ON [dbo].[report_element]
(
	[report_id] ASC,
	[element_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [report_element_index02]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [report_element_index02] ON [dbo].[report_element]
(
	[element_id] ASC,
	[report_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [resource_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [resource_index01] ON [dbo].[resource]
(
	[document_id] ASC,
	[xml_location] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [resource_index02]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [resource_index02] ON [dbo].[resource]
(
	[role_uri_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [resource_index03]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [resource_index03] ON [dbo].[resource]
(
	[document_id] ASC,
	[xml_location] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [unit_base_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [unit_base_index01] ON [dbo].[unit_base]
(
	[unit_hash] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [unit_measure_base_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [unit_measure_base_index01] ON [dbo].[unit_measure_base]
(
	[unit_base_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [unit_report_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [unit_report_index01] ON [dbo].[unit_report]
(
	[report_id] ASC,
	[unit_xml_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
/****** Object:  Index [unit_report_index02]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [unit_report_index02] ON [dbo].[unit_report]
(
	[unit_base_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [uri_index01]    Script Date: 5/22/2020 1:58:40 PM ******/
CREATE NONCLUSTERED INDEX [uri_index01] ON [dbo].[uri]
(
	[uri] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
GO
ALTER TABLE [dbo].[document] ADD  DEFAULT ((0)) FOR [document_loaded]
GO
ALTER TABLE [dbo].[fact] ADD  DEFAULT ((0)) FOR [is_precision_infinity]
GO
ALTER TABLE [dbo].[fact] ADD  DEFAULT ((0)) FOR [is_decimals_infinity]
GO
ALTER TABLE [dbo].[report] ADD  DEFAULT ('1753-01-01 00:00:00') FOR [creation_timestamp]
GO
ALTER TABLE [dbo].[report] ADD  DEFAULT ('1753-01-01 00:00:00') FOR [accepted_timestamp]
GO
ALTER TABLE [dbo].[report] ADD  DEFAULT ((0)) FOR [is_most_current]
GO
ALTER TABLE [dbo].[attribute_value]  WITH NOCHECK ADD  CONSTRAINT [fk_attribute_value_qname] FOREIGN KEY([qname_id])
REFERENCES [dbo].[qname] ([qname_id])
GO
ALTER TABLE [dbo].[attribute_value] NOCHECK CONSTRAINT [fk_attribute_value_qname]
GO
ALTER TABLE [dbo].[base_namespace]  WITH CHECK ADD  CONSTRAINT [FK_base_namespace_source] FOREIGN KEY([source_id])
REFERENCES [dbo].[source] ([source_id])
GO
ALTER TABLE [dbo].[base_namespace] CHECK CONSTRAINT [FK_base_namespace_source]
GO
ALTER TABLE [dbo].[context_dimension]  WITH NOCHECK ADD  CONSTRAINT [fk_context_dimension_dimension_qname] FOREIGN KEY([dimension_qname_id])
REFERENCES [dbo].[qname] ([qname_id])
GO
ALTER TABLE [dbo].[context_dimension] NOCHECK CONSTRAINT [fk_context_dimension_dimension_qname]
GO
ALTER TABLE [dbo].[context_dimension]  WITH NOCHECK ADD  CONSTRAINT [fk_context_dimension_member_qname] FOREIGN KEY([member_qname_id])
REFERENCES [dbo].[qname] ([qname_id])
GO
ALTER TABLE [dbo].[context_dimension] NOCHECK CONSTRAINT [fk_context_dimension_member_qname]
GO
ALTER TABLE [dbo].[context_dimension]  WITH NOCHECK ADD  CONSTRAINT [fk_context_dimension_typed_qname] FOREIGN KEY([typed_qname_id])
REFERENCES [dbo].[qname] ([qname_id])
GO
ALTER TABLE [dbo].[context_dimension] NOCHECK CONSTRAINT [fk_context_dimension_typed_qname]
GO
ALTER TABLE [dbo].[context_dimension_explicit]  WITH CHECK ADD  CONSTRAINT [FK_context_dimension_explicit_context] FOREIGN KEY([context_id])
REFERENCES [dbo].[context] ([context_id])
GO
ALTER TABLE [dbo].[context_dimension_explicit] CHECK CONSTRAINT [FK_context_dimension_explicit_context]
GO
ALTER TABLE [dbo].[custom_arcrole_type]  WITH CHECK ADD  CONSTRAINT [fk_arcrole_cycles] FOREIGN KEY([cycles_allowed])
REFERENCES [dbo].[enumeration_arcrole_cycles_allowed] ([enumeration_arcrole_cycles_allowed_id])
GO
ALTER TABLE [dbo].[custom_arcrole_type] CHECK CONSTRAINT [fk_arcrole_cycles]
GO
ALTER TABLE [dbo].[custom_arcrole_type]  WITH CHECK ADD  CONSTRAINT [fk_custom_arcrole_type_document] FOREIGN KEY([document_id])
REFERENCES [dbo].[document] ([document_id])
GO
ALTER TABLE [dbo].[custom_arcrole_type] CHECK CONSTRAINT [fk_custom_arcrole_type_document]
GO
ALTER TABLE [dbo].[custom_arcrole_used_on]  WITH NOCHECK ADD  CONSTRAINT [fk_used_on_custom_arcrole_type] FOREIGN KEY([custom_arcrole_type_id])
REFERENCES [dbo].[custom_arcrole_type] ([custom_arcrole_type_id])
GO
ALTER TABLE [dbo].[custom_arcrole_used_on] NOCHECK CONSTRAINT [fk_used_on_custom_arcrole_type]
GO
ALTER TABLE [dbo].[custom_arcrole_used_on]  WITH NOCHECK ADD  CONSTRAINT [fk_used_on_qname] FOREIGN KEY([qname_id])
REFERENCES [dbo].[qname] ([qname_id])
GO
ALTER TABLE [dbo].[custom_arcrole_used_on] NOCHECK CONSTRAINT [fk_used_on_qname]
GO
ALTER TABLE [dbo].[custom_role_type]  WITH NOCHECK ADD  CONSTRAINT [fk_custom_role_type] FOREIGN KEY([document_id])
REFERENCES [dbo].[document] ([document_id])
GO
ALTER TABLE [dbo].[custom_role_type] NOCHECK CONSTRAINT [fk_custom_role_type]
GO
ALTER TABLE [dbo].[custom_role_type]  WITH NOCHECK ADD  CONSTRAINT [fk_custom_role_type_uri] FOREIGN KEY([uri_id])
REFERENCES [dbo].[uri] ([uri_id])
GO
ALTER TABLE [dbo].[custom_role_type] NOCHECK CONSTRAINT [fk_custom_role_type_uri]
GO
ALTER TABLE [dbo].[custom_role_used_on]  WITH CHECK ADD  CONSTRAINT [FK_custom_role_used_on_qname] FOREIGN KEY([qname_id])
REFERENCES [dbo].[qname] ([qname_id])
GO
ALTER TABLE [dbo].[custom_role_used_on] CHECK CONSTRAINT [FK_custom_role_used_on_qname]
GO
ALTER TABLE [dbo].[custom_role_used_on]  WITH CHECK ADD  CONSTRAINT [fk_used_on_custom_role_type] FOREIGN KEY([custom_role_type_id])
REFERENCES [dbo].[custom_role_type] ([custom_role_type_id])
GO
ALTER TABLE [dbo].[custom_role_used_on] CHECK CONSTRAINT [fk_used_on_custom_role_type]
GO
ALTER TABLE [dbo].[document_structure]  WITH CHECK ADD  CONSTRAINT [FK_document_structure_document] FOREIGN KEY([parent_document_id])
REFERENCES [dbo].[document] ([document_id])
GO
ALTER TABLE [dbo].[document_structure] CHECK CONSTRAINT [FK_document_structure_document]
GO
ALTER TABLE [dbo].[document_structure]  WITH CHECK ADD  CONSTRAINT [FK_document_structure_document1] FOREIGN KEY([child_document_id])
REFERENCES [dbo].[document] ([document_id])
GO
ALTER TABLE [dbo].[document_structure] CHECK CONSTRAINT [FK_document_structure_document1]
GO
ALTER TABLE [dbo].[dts_document]  WITH NOCHECK ADD  CONSTRAINT [fk_dts_document_document] FOREIGN KEY([document_id])
REFERENCES [dbo].[document] ([document_id])
GO
ALTER TABLE [dbo].[dts_document] NOCHECK CONSTRAINT [fk_dts_document_document]
GO
ALTER TABLE [dbo].[dts_document]  WITH NOCHECK ADD  CONSTRAINT [fk_dts_document_dts] FOREIGN KEY([dts_id])
REFERENCES [dbo].[dts] ([dts_id])
GO
ALTER TABLE [dbo].[dts_document] NOCHECK CONSTRAINT [fk_dts_document_dts]
GO
ALTER TABLE [dbo].[dts_element]  WITH NOCHECK ADD  CONSTRAINT [fk_dts_element_dts] FOREIGN KEY([dts_id])
REFERENCES [dbo].[dts] ([dts_id])
GO
ALTER TABLE [dbo].[dts_element] NOCHECK CONSTRAINT [fk_dts_element_dts]
GO
ALTER TABLE [dbo].[dts_element]  WITH NOCHECK ADD  CONSTRAINT [fk_dts_element_element] FOREIGN KEY([element_id])
REFERENCES [dbo].[element] ([element_id])
GO
ALTER TABLE [dbo].[dts_element] NOCHECK CONSTRAINT [fk_dts_element_element]
GO
ALTER TABLE [dbo].[dts_network]  WITH NOCHECK ADD  CONSTRAINT [fk_dts_network_qname_arc] FOREIGN KEY([arc_qname_id])
REFERENCES [dbo].[qname] ([qname_id])
GO
ALTER TABLE [dbo].[dts_network] NOCHECK CONSTRAINT [fk_dts_network_qname_arc]
GO
ALTER TABLE [dbo].[dts_network]  WITH NOCHECK ADD  CONSTRAINT [fk_dts_network_qname_link] FOREIGN KEY([extended_link_qname_id])
REFERENCES [dbo].[qname] ([qname_id])
GO
ALTER TABLE [dbo].[dts_network] NOCHECK CONSTRAINT [fk_dts_network_qname_link]
GO
ALTER TABLE [dbo].[dts_network]  WITH NOCHECK ADD  CONSTRAINT [fk_dts_network_report] FOREIGN KEY([dts_id])
REFERENCES [dbo].[dts] ([dts_id])
GO
ALTER TABLE [dbo].[dts_network] NOCHECK CONSTRAINT [fk_dts_network_report]
GO
ALTER TABLE [dbo].[dts_network]  WITH NOCHECK ADD  CONSTRAINT [fk_dts_network_uri_arcrole] FOREIGN KEY([arcrole_uri_id])
REFERENCES [dbo].[uri] ([uri_id])
GO
ALTER TABLE [dbo].[dts_network] NOCHECK CONSTRAINT [fk_dts_network_uri_arcrole]
GO
ALTER TABLE [dbo].[dts_network]  WITH NOCHECK ADD  CONSTRAINT [fk_dts_network_uri_linkrole] FOREIGN KEY([extended_link_role_uri_id])
REFERENCES [dbo].[uri] ([uri_id])
GO
ALTER TABLE [dbo].[dts_network] NOCHECK CONSTRAINT [fk_dts_network_uri_linkrole]
GO
ALTER TABLE [dbo].[dts_relationship]  WITH NOCHECK ADD  CONSTRAINT [fk_dts_relationship_dts_network] FOREIGN KEY([dts_network_id])
REFERENCES [dbo].[dts_network] ([dts_network_id])
GO
ALTER TABLE [dbo].[dts_relationship] NOCHECK CONSTRAINT [fk_dts_relationship_dts_network]
GO
ALTER TABLE [dbo].[dts_relationship]  WITH NOCHECK ADD  CONSTRAINT [fk_rel_from_element] FOREIGN KEY([from_element_id])
REFERENCES [dbo].[element] ([element_id])
GO
ALTER TABLE [dbo].[dts_relationship] NOCHECK CONSTRAINT [fk_rel_from_element]
GO
ALTER TABLE [dbo].[dts_relationship]  WITH NOCHECK ADD  CONSTRAINT [fk_rel_from_resource] FOREIGN KEY([from_resource_id])
REFERENCES [dbo].[resource] ([resource_id])
GO
ALTER TABLE [dbo].[dts_relationship] NOCHECK CONSTRAINT [fk_rel_from_resource]
GO
ALTER TABLE [dbo].[dts_relationship]  WITH NOCHECK ADD  CONSTRAINT [fk_rel_to_element] FOREIGN KEY([to_element_id])
REFERENCES [dbo].[element] ([element_id])
GO
ALTER TABLE [dbo].[dts_relationship] NOCHECK CONSTRAINT [fk_rel_to_element]
GO
ALTER TABLE [dbo].[dts_relationship]  WITH NOCHECK ADD  CONSTRAINT [fk_rel_to_resource] FOREIGN KEY([to_resource_id])
REFERENCES [dbo].[resource] ([resource_id])
GO
ALTER TABLE [dbo].[dts_relationship] NOCHECK CONSTRAINT [fk_rel_to_resource]
GO
ALTER TABLE [dbo].[element]  WITH CHECK ADD  CONSTRAINT [fk_element_balance] FOREIGN KEY([balance_id])
REFERENCES [dbo].[enumeration_element_balance] ([enumeration_element_balance_id])
GO
ALTER TABLE [dbo].[element] CHECK CONSTRAINT [fk_element_balance]
GO
ALTER TABLE [dbo].[element]  WITH NOCHECK ADD  CONSTRAINT [fk_element_datatype_qname] FOREIGN KEY([datatype_qname_id])
REFERENCES [dbo].[qname] ([qname_id])
GO
ALTER TABLE [dbo].[element] NOCHECK CONSTRAINT [fk_element_datatype_qname]
GO
ALTER TABLE [dbo].[element]  WITH NOCHECK ADD  CONSTRAINT [fk_element_document] FOREIGN KEY([document_id])
REFERENCES [dbo].[document] ([document_id])
GO
ALTER TABLE [dbo].[element] NOCHECK CONSTRAINT [fk_element_document]
GO
ALTER TABLE [dbo].[element]  WITH CHECK ADD  CONSTRAINT [fk_element_period_type] FOREIGN KEY([period_type_id])
REFERENCES [dbo].[enumeration_element_period_type] ([enumeration_element_period_type_id])
GO
ALTER TABLE [dbo].[element] CHECK CONSTRAINT [fk_element_period_type]
GO
ALTER TABLE [dbo].[element]  WITH NOCHECK ADD  CONSTRAINT [fk_element_qname] FOREIGN KEY([qname_id])
REFERENCES [dbo].[qname] ([qname_id])
GO
ALTER TABLE [dbo].[element] NOCHECK CONSTRAINT [fk_element_qname]
GO
ALTER TABLE [dbo].[element]  WITH NOCHECK ADD  CONSTRAINT [fk_element_sg_qname] FOREIGN KEY([substitution_group_qname_id])
REFERENCES [dbo].[qname] ([qname_id])
GO
ALTER TABLE [dbo].[element] NOCHECK CONSTRAINT [fk_element_sg_qname]
GO
ALTER TABLE [dbo].[element]  WITH NOCHECK ADD  CONSTRAINT [fk_element_xbrl_base_datatype_qname] FOREIGN KEY([xbrl_base_datatype_qname_id])
REFERENCES [dbo].[qname] ([qname_id])
GO
ALTER TABLE [dbo].[element] NOCHECK CONSTRAINT [fk_element_xbrl_base_datatype_qname]
GO
ALTER TABLE [dbo].[element_attribute_value_association]  WITH NOCHECK ADD  CONSTRAINT [fk_eav_av] FOREIGN KEY([attribute_value_id])
REFERENCES [dbo].[attribute_value] ([attribute_value_id])
GO
ALTER TABLE [dbo].[element_attribute_value_association] NOCHECK CONSTRAINT [fk_eav_av]
GO
ALTER TABLE [dbo].[element_attribute_value_association]  WITH NOCHECK ADD  CONSTRAINT [fk_eav_element] FOREIGN KEY([element_id])
REFERENCES [dbo].[element] ([element_id])
GO
ALTER TABLE [dbo].[element_attribute_value_association] NOCHECK CONSTRAINT [fk_eav_element]
GO
ALTER TABLE [dbo].[entity_identifier]  WITH NOCHECK ADD  CONSTRAINT [entity_identifier_entity_id_fkey] FOREIGN KEY([entity_id])
REFERENCES [dbo].[entity] ([entity_id])
GO
ALTER TABLE [dbo].[entity_identifier] NOCHECK CONSTRAINT [entity_identifier_entity_id_fkey]
GO
ALTER TABLE [dbo].[entity_name_history]  WITH NOCHECK ADD  CONSTRAINT [entity_name_history_entity_id_fkey] FOREIGN KEY([entity_id])
REFERENCES [dbo].[entity] ([entity_id])
GO
ALTER TABLE [dbo].[entity_name_history] NOCHECK CONSTRAINT [entity_name_history_entity_id_fkey]
GO
ALTER TABLE [dbo].[entity_source]  WITH CHECK ADD  CONSTRAINT [FK_entity_source_entity] FOREIGN KEY([entity_id])
REFERENCES [dbo].[entity] ([entity_id])
GO
ALTER TABLE [dbo].[entity_source] CHECK CONSTRAINT [FK_entity_source_entity]
GO
ALTER TABLE [dbo].[entity_source]  WITH CHECK ADD  CONSTRAINT [FK_entity_source_source] FOREIGN KEY([source_id])
REFERENCES [dbo].[source] ([source_id])
GO
ALTER TABLE [dbo].[entity_source] CHECK CONSTRAINT [FK_entity_source_source]
GO
ALTER TABLE [dbo].[fact]  WITH CHECK ADD  CONSTRAINT [fk_fact_context] FOREIGN KEY([context_id])
REFERENCES [dbo].[context] ([context_id])
GO
ALTER TABLE [dbo].[fact] CHECK CONSTRAINT [fk_fact_context]
GO
ALTER TABLE [dbo].[fact]  WITH CHECK ADD  CONSTRAINT [fk_fact_element] FOREIGN KEY([element_id])
REFERENCES [dbo].[element] ([element_id])
GO
ALTER TABLE [dbo].[fact] CHECK CONSTRAINT [fk_fact_element]
GO
ALTER TABLE [dbo].[fact]  WITH CHECK ADD  CONSTRAINT [fk_fact_fact_tuple] FOREIGN KEY([tuple_fact_id])
REFERENCES [dbo].[fact] ([fact_id])
GO
ALTER TABLE [dbo].[fact] CHECK CONSTRAINT [fk_fact_fact_tuple]
GO
ALTER TABLE [dbo].[fact]  WITH CHECK ADD  CONSTRAINT [fk_fact_report] FOREIGN KEY([accession_id])
REFERENCES [dbo].[report] ([report_id])
GO
ALTER TABLE [dbo].[fact] CHECK CONSTRAINT [fk_fact_report]
GO
ALTER TABLE [dbo].[fact]  WITH CHECK ADD  CONSTRAINT [fk_fact_unit_unit_base] FOREIGN KEY([unit_base_id])
REFERENCES [dbo].[unit_base] ([unit_base_id])
GO
ALTER TABLE [dbo].[fact] CHECK CONSTRAINT [fk_fact_unit_unit_base]
GO
ALTER TABLE [dbo].[fact]  WITH CHECK ADD  CONSTRAINT [fk_fact_unit_unit_report] FOREIGN KEY([unit_id])
REFERENCES [dbo].[unit_report] ([unit_report_id])
GO
ALTER TABLE [dbo].[fact] CHECK CONSTRAINT [fk_fact_unit_unit_report]
GO
ALTER TABLE [dbo].[footnote_resource]  WITH CHECK ADD  CONSTRAINT [FK_footnote_resource_resource] FOREIGN KEY([resource_id])
REFERENCES [dbo].[resource] ([resource_id])
GO
ALTER TABLE [dbo].[footnote_resource] CHECK CONSTRAINT [FK_footnote_resource_resource]
GO
ALTER TABLE [dbo].[label_resource]  WITH NOCHECK ADD  CONSTRAINT [fk_resource_id] FOREIGN KEY([resource_id])
REFERENCES [dbo].[resource] ([resource_id])
GO
ALTER TABLE [dbo].[label_resource] NOCHECK CONSTRAINT [fk_resource_id]
GO
ALTER TABLE [dbo].[namespace]  WITH NOCHECK ADD  CONSTRAINT [namespace_taxonomy_version_id_fkey] FOREIGN KEY([taxonomy_version_id])
REFERENCES [dbo].[taxonomy_version] ([taxonomy_version_id])
GO
ALTER TABLE [dbo].[namespace] NOCHECK CONSTRAINT [namespace_taxonomy_version_id_fkey]
GO
ALTER TABLE [dbo].[namespace_source]  WITH CHECK ADD  CONSTRAINT [FK_namespace_source_namespace] FOREIGN KEY([namespace_id])
REFERENCES [dbo].[namespace] ([namespace_id])
GO
ALTER TABLE [dbo].[namespace_source] CHECK CONSTRAINT [FK_namespace_source_namespace]
GO
ALTER TABLE [dbo].[namespace_source]  WITH CHECK ADD  CONSTRAINT [FK_namespace_source_source] FOREIGN KEY([source_id])
REFERENCES [dbo].[source] ([source_id])
GO
ALTER TABLE [dbo].[namespace_source] CHECK CONSTRAINT [FK_namespace_source_source]
GO
ALTER TABLE [dbo].[reference_part]  WITH NOCHECK ADD  CONSTRAINT [fk_reference_part_qname] FOREIGN KEY([qname_id])
REFERENCES [dbo].[qname] ([qname_id])
GO
ALTER TABLE [dbo].[reference_part] NOCHECK CONSTRAINT [fk_reference_part_qname]
GO
ALTER TABLE [dbo].[reference_part]  WITH NOCHECK ADD  CONSTRAINT [fk_reference_part_resource] FOREIGN KEY([resource_id])
REFERENCES [dbo].[resource] ([resource_id])
GO
ALTER TABLE [dbo].[reference_part] NOCHECK CONSTRAINT [fk_reference_part_resource]
GO
ALTER TABLE [dbo].[report]  WITH NOCHECK ADD  CONSTRAINT [fk_report_dts] FOREIGN KEY([dts_id])
REFERENCES [dbo].[dts] ([dts_id])
GO
ALTER TABLE [dbo].[report] NOCHECK CONSTRAINT [fk_report_dts]
GO
ALTER TABLE [dbo].[report]  WITH NOCHECK ADD  CONSTRAINT [fk_report_dts_entry] FOREIGN KEY([entry_dts_id])
REFERENCES [dbo].[dts] ([dts_id])
GO
ALTER TABLE [dbo].[report] NOCHECK CONSTRAINT [fk_report_dts_entry]
GO
ALTER TABLE [dbo].[report]  WITH NOCHECK ADD  CONSTRAINT [fk_report_entity] FOREIGN KEY([entity_id])
REFERENCES [dbo].[entity] ([entity_id])
GO
ALTER TABLE [dbo].[report] NOCHECK CONSTRAINT [fk_report_entity]
GO
ALTER TABLE [dbo].[report]  WITH CHECK ADD  CONSTRAINT [FK_report_source] FOREIGN KEY([source_id])
REFERENCES [dbo].[source] ([source_id])
GO
ALTER TABLE [dbo].[report] CHECK CONSTRAINT [FK_report_source]
GO
ALTER TABLE [dbo].[report_document]  WITH NOCHECK ADD  CONSTRAINT [fk_report_document_document] FOREIGN KEY([document_id])
REFERENCES [dbo].[document] ([document_id])
GO
ALTER TABLE [dbo].[report_document] NOCHECK CONSTRAINT [fk_report_document_document]
GO
ALTER TABLE [dbo].[report_document]  WITH NOCHECK ADD  CONSTRAINT [fk_report_document_report] FOREIGN KEY([report_id])
REFERENCES [dbo].[report] ([report_id])
GO
ALTER TABLE [dbo].[report_document] NOCHECK CONSTRAINT [fk_report_document_report]
GO
ALTER TABLE [dbo].[report_element]  WITH NOCHECK ADD  CONSTRAINT [fk_report_element_element] FOREIGN KEY([element_id])
REFERENCES [dbo].[element] ([element_id])
GO
ALTER TABLE [dbo].[report_element] NOCHECK CONSTRAINT [fk_report_element_element]
GO
ALTER TABLE [dbo].[report_element]  WITH NOCHECK ADD  CONSTRAINT [fk_report_element_report] FOREIGN KEY([report_id])
REFERENCES [dbo].[report] ([report_id])
GO
ALTER TABLE [dbo].[report_element] NOCHECK CONSTRAINT [fk_report_element_report]
GO
ALTER TABLE [dbo].[resource]  WITH NOCHECK ADD  CONSTRAINT [fk_resource_document] FOREIGN KEY([document_id])
REFERENCES [dbo].[document] ([document_id])
GO
ALTER TABLE [dbo].[resource] NOCHECK CONSTRAINT [fk_resource_document]
GO
ALTER TABLE [dbo].[resource]  WITH NOCHECK ADD  CONSTRAINT [fk_resource_qname] FOREIGN KEY([qname_id])
REFERENCES [dbo].[qname] ([qname_id])
GO
ALTER TABLE [dbo].[resource] NOCHECK CONSTRAINT [fk_resource_qname]
GO
ALTER TABLE [dbo].[resource]  WITH NOCHECK ADD  CONSTRAINT [fk_resource_role_uri] FOREIGN KEY([role_uri_id])
REFERENCES [dbo].[uri] ([uri_id])
GO
ALTER TABLE [dbo].[resource] NOCHECK CONSTRAINT [fk_resource_role_uri]
GO
ALTER TABLE [dbo].[taxonomy_version]  WITH NOCHECK ADD  CONSTRAINT [taxonomy_version_taxonomy_id_fkey] FOREIGN KEY([taxonomy_id])
REFERENCES [dbo].[taxonomy] ([taxonomy_id])
GO
ALTER TABLE [dbo].[taxonomy_version] NOCHECK CONSTRAINT [taxonomy_version_taxonomy_id_fkey]
GO
ALTER TABLE [dbo].[taxonomy_version_dts]  WITH CHECK ADD  CONSTRAINT [FK_taxonomy_version_dts_dts] FOREIGN KEY([dts_id])
REFERENCES [dbo].[dts] ([dts_id])
GO
ALTER TABLE [dbo].[taxonomy_version_dts] CHECK CONSTRAINT [FK_taxonomy_version_dts_dts]
GO
ALTER TABLE [dbo].[taxonomy_version_dts]  WITH CHECK ADD  CONSTRAINT [FK_taxonomy_version_dts_taxonomy_version] FOREIGN KEY([taxonomy_version_id])
REFERENCES [dbo].[taxonomy_version] ([taxonomy_version_id])
GO
ALTER TABLE [dbo].[taxonomy_version_dts] CHECK CONSTRAINT [FK_taxonomy_version_dts_taxonomy_version]
GO
ALTER TABLE [dbo].[taxonomy_version_dts]  WITH CHECK ADD  CONSTRAINT [FK_taxonomy_version_dts_taxonomy_version_dts] FOREIGN KEY([taxonomy_version_dts_id])
REFERENCES [dbo].[taxonomy_version_dts] ([taxonomy_version_dts_id])
GO
ALTER TABLE [dbo].[taxonomy_version_dts] CHECK CONSTRAINT [FK_taxonomy_version_dts_taxonomy_version_dts]
GO
ALTER TABLE [dbo].[unit_measure_base]  WITH CHECK ADD  CONSTRAINT [FK_unit_measure_base_location_id] FOREIGN KEY([location_id])
REFERENCES [dbo].[enumeration_unit_measure_location] ([enumeration_unit_measure_location_id])
ON UPDATE CASCADE
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[unit_measure_base] CHECK CONSTRAINT [FK_unit_measure_base_location_id]
GO
ALTER TABLE [dbo].[unit_measure_base]  WITH NOCHECK ADD  CONSTRAINT [fk_unit_measure_base_unit_base] FOREIGN KEY([unit_base_id])
REFERENCES [dbo].[unit_base] ([unit_base_id])
GO
ALTER TABLE [dbo].[unit_measure_base] NOCHECK CONSTRAINT [fk_unit_measure_base_unit_base]
GO
ALTER TABLE [dbo].[unit_measure_base]  WITH CHECK ADD  CONSTRAINT [FK_unit_measure_base_unit_measure_base] FOREIGN KEY([unit_measure_base_id])
REFERENCES [dbo].[unit_measure_base] ([unit_measure_base_id])
GO
ALTER TABLE [dbo].[unit_measure_base] CHECK CONSTRAINT [FK_unit_measure_base_unit_measure_base]
GO
ALTER TABLE [dbo].[unit_report]  WITH NOCHECK ADD  CONSTRAINT [fk_unit_report_report] FOREIGN KEY([report_id])
REFERENCES [dbo].[report] ([report_id])
GO
ALTER TABLE [dbo].[unit_report] NOCHECK CONSTRAINT [fk_unit_report_report]
GO
ALTER TABLE [dbo].[unit_report]  WITH NOCHECK ADD  CONSTRAINT [fk_unit_report_unit_base] FOREIGN KEY([unit_base_id])
REFERENCES [dbo].[unit_base] ([unit_base_id])
GO
ALTER TABLE [dbo].[unit_report] NOCHECK CONSTRAINT [fk_unit_report_unit_base]
GO
ALTER TABLE [dbo].[uri]  WITH NOCHECK ADD  CONSTRAINT [role_type_role_type_label] FOREIGN KEY([uri_id])
REFERENCES [dbo].[uri] ([uri_id])
GO
ALTER TABLE [dbo].[uri] NOCHECK CONSTRAINT [role_type_role_type_label]
GO
/****** Object:  StoredProcedure [dbo].[TestParams]    Script Date: 5/22/2020 1:58:40 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- Create Stored Procedure
CREATE PROCEDURE [dbo].[TestParams]
@FirstParam bigint
AS
BEGIN
	SELECT  @FirstParam FirstParam
END;
GO



SET IDENTITY_INSERT [dbo].[document] ON 

INSERT [dbo].[document] ([document_id], [document_uri], [document_loaded], [content], [document_type], [target_namespace]) VALUES (1, N'http://xbrl.us/us-gaap/1.0/non-gaap/dei-2008-03-31.xsd', 0, NULL, NULL, NULL)
INSERT [dbo].[document] ([document_id], [document_uri], [document_loaded], [content], [document_type], [target_namespace]) VALUES (2, N'http://taxonomies.xbrl.us/us-gaap/2009/elts/us-gaap-2009-01-31.xsd', 0, NULL, NULL, NULL)
INSERT [dbo].[document] ([document_id], [document_uri], [document_loaded], [content], [document_type], [target_namespace]) VALUES (3, N'http://xbrl.fasb.org/us-gaap/2011/elts/us-gaap-2011-01-31.xsd', 0, NULL, NULL, NULL)
INSERT [dbo].[document] ([document_id], [document_uri], [document_loaded], [content], [document_type], [target_namespace]) VALUES (4, N'http://xbrl.sec.gov/rr/2010/rr-2010-02-28.xsd', 0, NULL, NULL, NULL)
INSERT [dbo].[document] ([document_id], [document_uri], [document_loaded], [content], [document_type], [target_namespace]) VALUES (5, N'http://xbrl.fasb.org/us-gaap/2012/elts/us-gaap-2012-01-31.xsd', 0, NULL, NULL, NULL)
INSERT [dbo].[document] ([document_id], [document_uri], [document_loaded], [content], [document_type], [target_namespace]) VALUES (6, N'http://xbrl.fasb.org/us-gaap/2013/elts/us-gaap-2013-01-31.xsd', 0, NULL, NULL, NULL)
INSERT [dbo].[document] ([document_id], [document_uri], [document_loaded], [content], [document_type], [target_namespace]) VALUES (7, N'http://xbrl.fasb.org/us-gaap/2014/elts/us-gaap-2014-01-31.xsd', 0, NULL, NULL, NULL)
INSERT [dbo].[document] ([document_id], [document_uri], [document_loaded], [content], [document_type], [target_namespace]) VALUES (8, N'http://xbrl.fasb.org/us-gaap/2015/elts/us-gaap-2015-01-31.xsd', 0, NULL, NULL, NULL)
INSERT [dbo].[document] ([document_id], [document_uri], [document_loaded], [content], [document_type], [target_namespace]) VALUES (9, N'http://xbrl.fasb.org/us-gaap/2016/elts/us-gaap-2016-01-31.xsd', 0, NULL, NULL, NULL)
INSERT [dbo].[document] ([document_id], [document_uri], [document_loaded], [content], [document_type], [target_namespace]) VALUES (10, N'http://xbrl.fasb.org/us-gaap/2017/elts/us-gaap-2017-01-31.xsd', 0, NULL, NULL, NULL)
INSERT [dbo].[document] ([document_id], [document_uri], [document_loaded], [content], [document_type], [target_namespace]) VALUES (11, N'http://xbrl.sec.gov/rr/2012/rr-2012-01-31.xsd', 0, NULL, NULL, NULL)
INSERT [dbo].[document] ([document_id], [document_uri], [document_loaded], [content], [document_type], [target_namespace]) VALUES (12, N'http://xbrl.sec.gov/rocr/2015/ratings-2015-03-31.xsd', 0, NULL, NULL, NULL)
INSERT [dbo].[document] ([document_id], [document_uri], [document_loaded], [content], [document_type], [target_namespace]) VALUES (13, N'http://xbrl.fasb.org/us-gaap/2018/elts/us-gaap-2018-01-31.xsd', 0, NULL, NULL, NULL)
INSERT [dbo].[document] ([document_id], [document_uri], [document_loaded], [content], [document_type], [target_namespace]) VALUES (14, N'http://xbrl.ifrs.org/taxonomy/2016-03-31/full_ifrs/full_ifrs-cor_2016-03-31.xsd', 0, NULL, NULL, NULL)
INSERT [dbo].[document] ([document_id], [document_uri], [document_loaded], [content], [document_type], [target_namespace]) VALUES (15, N'http://xbrl.ifrs.org/taxonomy/2017-03-09/full_ifrs/full_ifrs-cor_2017-03-09.xsd', 0, NULL, NULL, NULL)
INSERT [dbo].[document] ([document_id], [document_uri], [document_loaded], [content], [document_type], [target_namespace]) VALUES (16, N'http://xbrl.ifrs.org/taxonomy/2018-03-16/full_ifrs/full_ifrs-cor_2018-03-16.xsd', 0, NULL, NULL, NULL)
SET IDENTITY_INSERT [dbo].[document] OFF

SET IDENTITY_INSERT [dbo].[enumeration_arcrole_cycles_allowed] ON
INSERT [dbo].[enumeration_arcrole_cycles_allowed] ([enumeration_arcrole_cycles_allowed_id], [description]) VALUES (1, N'any')
INSERT [dbo].[enumeration_arcrole_cycles_allowed] ([enumeration_arcrole_cycles_allowed_id], [description]) VALUES (2, N'undirected')
INSERT [dbo].[enumeration_arcrole_cycles_allowed] ([enumeration_arcrole_cycles_allowed_id], [description]) VALUES (3, N'none')
SET IDENTITY_INSERT [dbo].[enumeration_arcrole_cycles_allowed] OFF
SET IDENTITY_INSERT [dbo].[enumeration_element_balance] ON
INSERT [dbo].[enumeration_element_balance] ([enumeration_element_balance_id], [description]) VALUES (1, N'debit')
INSERT [dbo].[enumeration_element_balance] ([enumeration_element_balance_id], [description]) VALUES (2, N'credit')
SET IDENTITY_INSERT [dbo].[enumeration_element_balance] OFF


SET IDENTITY_INSERT [dbo].[enumeration_element_period_type] ON
INSERT [dbo].[enumeration_element_period_type] ([enumeration_element_period_type_id], [description]) VALUES (1, N'instant')
INSERT [dbo].[enumeration_element_period_type] ([enumeration_element_period_type_id], [description]) VALUES (2, N'duration')
INSERT [dbo].[enumeration_element_period_type] ([enumeration_element_period_type_id], [description]) VALUES (3, N'forever')
SET IDENTITY_INSERT [dbo].[enumeration_element_period_type] OFF

SET IDENTITY_INSERT [dbo].[enumeration_unit_measure_location] ON
INSERT [dbo].[enumeration_unit_measure_location] ([enumeration_unit_measure_location_id], [description]) VALUES (1, N'measure')
INSERT [dbo].[enumeration_unit_measure_location] ([enumeration_unit_measure_location_id], [description]) VALUES (2, N'numerator')
INSERT [dbo].[enumeration_unit_measure_location] ([enumeration_unit_measure_location_id], [description]) VALUES (3, N'denominator')
SET IDENTITY_INSERT [dbo].[enumeration_unit_measure_location] OFF

SET IDENTITY_INSERT [dbo].[source] ON 

INSERT [dbo].[source] ([source_id], [source_name]) VALUES (1, N'FERC')
SET IDENTITY_INSERT [dbo].[source] OFF
GO

USE [master]
GO
ALTER DATABASE [XBRL] SET  READ_WRITE 
GO