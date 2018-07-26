CREATE OR REPLACE FUNCTION temp_find_funk_time(df_bytes bytea)
  RETURNS boolean AS
$BODY$
    import pandas as pd
    import pickle
    df = pickle.loads(df_bytes)
    try:
        df.index.to_datetime().tz_convert('Asia/Shanghai')
        return True
    except TypeError:
        return False
$BODY$
  LANGUAGE plpython3u VOLATILE;


CREATE OR REPLACE FUNCTION temp_fix_ts(df_bytes bytea)
  RETURNS pd_df AS
$BODY$
    import pandas as pd
    import pickle
    df = pickle.loads(df_bytes)
    df.index = df.index.to_datetime().tz_convert('Asia/Shanghai')
    df.index.name = 'timestamp'
    return pickle.dumps(df)
$BODY$
  LANGUAGE plpython3u VOLATILE


SELECT * FROM entity_datadefinition;

SELECT * FROM entity_organization;