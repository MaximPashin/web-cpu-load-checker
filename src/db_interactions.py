import sqlite3 as sl
import pandas as pd
import psutil
import time
import sys
import asyncio



def ensure_db_exist(db_name):
    con = sl.connect(db_name)
    c = con.cursor()

    c.execute('''SELECT count(name) FROM sqlite_master WHERE type='table' AND name='CPU_LOAD' ''')

    if c.fetchone()[0]==0:
        con.execute("""
        CREATE TABLE CPU_LOAD(
            time INTEGER NOT NULL PRIMARY KEY,
            percent REAL
        );
        """)

    con.commit()
    con.close()


def check_measure_interrupt(connect, bound_time):
    cursor = connect.cursor()
    cursor.execute("""
        SELECT *
        FROM CPU_LOAD
        WHERE time >= {}
    """.format(bound_time))
    if len(cursor.fetchall()) == 0:
        return True
    else: return False


def write_measure_to_db(db_name, current_time, load, sec_freq):
    con = sl.connect(db_name)
    
    sql = 'INSERT INTO CPU_LOAD (time, percent) values(?, ?)'
    with con:
        if check_measure_interrupt(con, current_time - (sec_freq+1)*10**9):
            con.executemany(sql, [(current_time - sec_freq*10**9, None)])
        con.executemany(sql, [(current_time, load)])
    			
    con.commit()
    con.close()


async def write_CPU_load(db_name):
    CPU_load = psutil.cpu_percent()
    current_time = time.time_ns()
    write_measure_to_db(db_name, current_time, CPU_load, 6)

    
def get_loads_df(db_name, bound_time):
    con = sl.connect(db_name)
    df = pd.read_sql('''
            SELECT *
            FROM CPU_LOAD
            WHERE time >= {}
        '''.format(bound_time), con, index_col='time')
    con.close()
    df = df.sort_values(by=['time'])
    return df