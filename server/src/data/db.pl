connect_to_db :-
	odbc_connect('test',_,[open(once),alias(tstConn)]).