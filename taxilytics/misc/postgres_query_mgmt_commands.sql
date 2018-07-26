SELECT datname, pid, state, query FROM pg_stat_activity;  -- To get a list of open connections
SELECT pg_cancel_backend(19059);  -- Stop the query associated with the procpid
SELECT pg_terminate_backend(procpid);  -- To kill the connection associated with the procpid