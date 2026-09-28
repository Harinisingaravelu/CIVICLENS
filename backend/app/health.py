from .analytics import load_data
from .database import connect, init_db

def readiness():
    checks={}
    try:
        df=load_data(); checks["dataset"]=True; rows=int(len(df)); snapshot=str(df["snapshot_date"].iloc[0])
    except Exception: checks["dataset"]=False; rows=0; snapshot=None
    try:
        init_db()
        with connect() as conn: conn.execute("SELECT 1").fetchone()
        checks["database"]=True
    except Exception: checks["database"]=False
    ready=all(checks.values())
    return {"status":"ready" if ready else "not_ready","checks":checks,"dataset_rows":rows,"snapshot_date":snapshot}
