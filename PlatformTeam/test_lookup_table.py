import sys
import pandas as pd
import psycopg2
import push_postgres_constants as constants

main_df = pd.read_csv(
    r"C:\Git_Repo\nr-optimize-metabase-api\push-data-to-metabase\RESE_UserBasedSoftware_Recoverable_AttributesFilter.csv"
)
lookup_df = pd.read_csv(
    r"C:\Git_Repo\nr-optimize-metabase-api\push-data-to-metabase\AD_displayname_email.csv"
)

main_df["DisplayName"] = main_df.IDIR.map(
    dict(lookup_df[["IDIR", "DisplayName"]].values)
)

main_df["Email"] = main_df.IDIR.map(dict(lookup_df[["IDIR", "Email"]].values))

main_df["AFIN Asset"] = main_df["AFIN Asset"].astype(str)

print(main_df.head())

main_df.to_csv(
    r"C:\Git_Repo\nr-optimize-metabase-api\push-data-to-metabase\userbasedsw_metabase.csv",
    sep=",",
    encoding="utf-8",
    index=False,
    header=True,
)

record_tuples = list(main_df.itertuples(index=False, name=None))


# inserts tuples into metabase
def insert_records_to_metabase(record_tuples):
    conn = None
    try:
        # Open a connection
        conn = psycopg2.connect(
            host="localhost",
            port="5431",
            database=constants.POSTGRES_DB_NAME,
            user=constants.POSTGRES_USER,
            password=constants.POSTGRES_PASS,
        )
        cur = conn.cursor()

        print("Inserting new data")

        cur.executemany(
            """
            INSERT into userbasedsw(afinasset, idiraccount, servicecategory, serviceattribute, ministry, reseglperiod, reseexpenseaccount, reseamount, afinrecoverytype, fundingmodel, displayname, email)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
        """,
            record_tuples,
        )
        print("Insert Complete")

        # close the communication with the PostgreSQL
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")


if __name__ == "__main__":
    insert_records_to_metabase(record_tuples)

# Here you want to change your database, username & password according to your own values
# param_dic = {
#    "host": "localhost",
#    "port": "5431",
#    "database": constants.POSTGRES_DB_NAME,
#    "user": constants.POSTGRES_USER,
#    "password": constants.POSTGRES_PASS,
# }
#
#
# def connect(params_dic):
#    """Connect to the PostgreSQL database server"""
#    conn = None
#    try:
#        conn = psycopg2.connect(
#            host="localhost",
#            port="5431",
#            database=constants.POSTGRES_DB_NAME,
#            user=constants.POSTGRES_USER,
#            password=constants.POSTGRES_PASS,
#        )
#    except (Exception, psycopg2.DatabaseError) as error:
#        print(error)
#        sys.exit(1)
#    return conn
#
#
# def single_insert(conn, insert_req):
#    """Execute a single INSERT request"""
#    cursor = conn.cursor()
#    try:
#        cursor.execute(insert_req)
#        conn.commit()
#    except (Exception, psycopg2.DatabaseError) as error:
#        print("Error: %s" % error)
#        conn.rollback()
#        cursor.close()
#        return 1
#    cursor.close()
#
#
## Connecting to the database
# conn = connect(param_dic)
## Inserting each row
# for i in main_df.index:
#    query = """
#    INSERT into userbasedsw(afinasset, idiraccount, servicecategory, serviceattribute, reseexpenseaccount, afinrecoverytype, fundingmodel, reseamount, reseglperiod, displayname, email, ministry) values('%s',%s,%s,'%s',%s,%s,'%s',%s,%s,'%s',%s,%s);
#    """ % (
#        main_df["AFIN Asset"],
#        main_df["IDIR"],
#        main_df["Service Category"],
#        main_df["Service Attribute"],
#        main_df["RESE Financial Ministry"],
#        main_df["RESE GL Period"],
#        main_df["RESE Expense Account"],
#        main_df["RESE Amount"],
#        main_df["AFIN Recovery Type"],
#        main_df["Funding Model"],
#        main_df["DisplayName"],
#        main_df["Email"],
#    )
#    single_insert(conn, query)
## Close the connection
# conn.close()
