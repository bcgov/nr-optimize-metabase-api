-- Command to put in OpenShift console to start postgres: psql -U postgres -d metabase
-- NOTE: At time of writing, test metabase db uses sdaparty instead of ministry
-- Insert sfp, email and hdriveusage for june/july into hosting expenses:
INSERT INTO hostingexpenses (
	ownerparty,
	category,
	expenseamount,
	fundingmodelstatus,
	glperiod,
	inventoryitem,
	omassettag,
	price,
	quantity,
	recoveryfrequency,
	recoveryperiod,
	recoverytype,
	reportingcustomer,
	sdaparty,
	servicelevel1,
	servicelevel2,
	servicename
)
SELECT 
	'NATURAL RESOURCE MINISTRIES' ownerparty,
	'Incremental Storage' category,
	sum(datausage)*2.7 AS "expenseamount",
	'RECOVERY' fundingmodelstatus,
	NULL glperiod,
	NULL inventoryitem,
	NULL omassettag,
	sum(datausage)*2.7 AS "price",
	1 quantity,
	'Consumption' recoveryfrequency,
	date_trunc('month', CAST(date AS timestamp)) AS "recoveryperiod",
	'Consumption' recoverytype,
	'GENERATED SFP ESTIMATION DATA' reportingcustomer,
	ministry as "sdaparty",
	'Hosting Services' servicelevel1,
	'Incremental Storage' servicelevel2,
	'Incremental Storage' servicename
FROM sfpmonthly
WHERE (date >= timestamp with time zone '2021-06-01 00:00:00.000Z'
   AND date < timestamp with time zone '2021-08-01 00:00:00.000Z')
GROUP BY date_trunc('month', CAST(date AS timestamp)), ministry 
UNION ALL
SELECT 
	'NATURAL RESOURCE MINISTRIES' ownerparty,
	'Incremental Storage' category,
	sum(datausagegb - 0.15) * 2.7 AS "expenseamount",
	'RECOVERY' fundingmodelstatus,
	NULL glperiod,
	NULL inventoryitem,
	NULL omassettag,
	sum(datausagegb - 0.15) * 2.7 AS "price",
	1 quantity,
	'Consumption' recoveryfrequency,
	date_trunc('month', CAST(date AS timestamp)) AS "recoveryperiod",
	'Consumption' recoverytype,
	'GENERATED EMAIL ESTIMATION DATA' reportingcustomer,
	ministry as "sdaparty",
	'Hosting Services' servicelevel1,
	'Incremental Storage' servicelevel2,
	'Incremental Storage' servicename
FROM casincremental
WHERE (consumptiontype = 'MESSAGING'
	AND (date >= timestamp with time zone '2021-06-01 00:00:00.000Z' AND date < timestamp with time zone '2021-08-01 00:00:00.000Z'))
GROUP BY date_trunc('month', CAST(date AS timestamp)), ministry
UNION ALL
SELECT 
	'NATURAL RESOURCE MINISTRIES' ownerparty,
	'Incremental Storage' category,
	sum(datausage-1.5)*2.7 AS "expenseamount",
	'RECOVERY' fundingmodelstatus,
	NULL glperiod,
	NULL inventoryitem,
	NULL omassettag,
	sum(datausage-1.5)*2.7 AS "price",
	1 quantity,
	'Consumption' recoveryfrequency,
	date_trunc('month', CAST(date AS timestamp)) AS "recoveryperiod",
	'Consumption' recoverytype,
	'GENERATED H DRIVE ESTIMATION DATA' reportingcustomer,
	ministry as "sdaparty",
	'Hosting Services' servicelevel1,
	'Incremental Storage' servicelevel2,
	'Incremental Storage' servicename
FROM hdriveusage
WHERE (date >= timestamp with time zone '2021-06-01 00:00:00.000Z'
   AND date < timestamp with time zone '2021-08-01 00:00:00.000Z')
GROUP BY date_trunc('month', CAST(date AS timestamp)), ministry;
	

---------------------------------------------------------------------------
-- NOTE: IN DEVELOPMENT. WORK ON HOLD.
-- The idea is to create a table which contains summary data to be displayed in a line graph for Potential Cost Avoidance
-- The hostingexpensespredictive table has 3 displaytypes: 'real' 'high prediction' 'low prediction'
-- 'high prediction' points are based on 12% increases to the most recent datapoint, or maybe fiscal Q1 start, to represent the estimated cost growth without Optimize
-- 'low prediction' are as 'high prediction' but with 11% decreases, to represent the goal for the Optimize team

-- Rebuild predictive hosting expenses table
DROP TABLE IF EXISTS hostingexpensespredictive;

CREATE TABLE hostingexpensespredictive (
	recoveryperiod timestamp,
	expenseamount text,
	displaytype text
);

-- Populate with existing date from the hostingexpenses table
INSERT INTO hostingexpensespredictive (
	recoveryperiod,
	expenseamount,
	displaytype
)
SELECT date_trunc('month', CAST(recoveryperiod AS timestamp)) AS "recoveryperiod", sum(expenseamount) AS "expenseamount", 'real' displaytype
FROM hostingexpenses
WHERE fundingmodelstatus = 'RECOVERY'
GROUP BY date_trunc('month', CAST(recoveryperiod AS timestamp));

-- Create procedure for creating multiple future data points based on the most recent existing 'real' data point
-- THIS FUNCTION IS IN DEVELOPMENT!
CREATE OR REPLACE FUNCTION addhostingexpensepredictions(
	timestoadd integer,
	modpercentage integer
)
RETURNS integer
AS $$
BEGIN
	FOR i IN 10..1 LOOP
		INSERT INTO hostingexpensespredictive (
			recoveryperiod,
			expenseamount,
			displaytype
		) VALUES (
			recoveryperiod,
			5000,
			"False"
		);
	END LOOP;
	RETURN 6;
	commit;
END;
$$ LANGUAGE plpgsql;

select addhostingexpensepredictions(2,12);