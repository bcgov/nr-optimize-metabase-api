CREATE TABLE hostingexpensesbudget (
	ministry text,
	month timestamp without time zone,
	budget numeric(12,3),
	fiscalyear numeric(4)
);

COMMENT ON COLUMN hostingexpensesbudget.ministry IS 'Acronym for a specific Ministry in the BC Public Service';
COMMENT ON COLUMN hostingexpensesbudget.month IS 'First day of the month';
COMMENT ON COLUMN hostingexpensesbudget.budget IS 'The dollar amount a specific Ministry in the BC Public Service has allocated to spend on Hosting Expenses';
COMMENT ON COLUMN hostingexpensesbudget.fiscalyear IS 'The fiscal year that the budget is applied to. A fiscal year for the BC Public Service goes from midnight April 1 of one year to 11:59 pm March 31 of the following year i.e. 2022 is 2021-04-01 to 2022-03-31';

INSERT INTO hostingexpensesbudget (ministry, month,	budget,	fiscalyear)
VALUES
('EMLI','2021-04-01',123,2022),
('EMLI','2021-05-01',234,2022),
('EMLI','2021-06-01',345,2022)...etc
