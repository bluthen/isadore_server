-- https://gist.github.com/matheusoliveira/9488951

CREATE OR REPLACE FUNCTION public.json_append(data json, insert_data json)
RETURNS json
LANGUAGE sql
AS $$
SELECT ('{'||string_agg(to_json(key)||':'||value, ',')||'}')::json
FROM (
SELECT * FROM json_each(data)
UNION ALL
SELECT * FROM json_each(insert_data)
) t;
$$;

CREATE OR REPLACE FUNCTION public.json_delete(data json, keys text[])
RETURNS json
LANGUAGE sql
AS $$
SELECT ('{'||string_agg(to_json(key)||':'||value, ',')||'}')::json
FROM (
SELECT * FROM json_each(data)
WHERE key <>ALL(keys)
) t;
$$;

CREATE OR REPLACE FUNCTION public.json_merge(data json, merge_data json)
RETURNS json
LANGUAGE sql
AS $$
SELECT ('{'||string_agg(to_json(key)||':'||value, ',')||'}')::json
FROM (
WITH to_merge AS (
SELECT * FROM json_each(merge_data)
)
SELECT *
FROM json_each(data)
WHERE key NOT IN (SELECT key FROM to_merge)
UNION ALL
SELECT * FROM to_merge
) t;
$$;

CREATE OR REPLACE FUNCTION public.json_update(data json, update_data json)
RETURNS json
LANGUAGE sql
AS $$
SELECT ('{'||string_agg(to_json(key)||':'||value, ',')||'}')::json
FROM (
WITH old_data AS (
SELECT * FROM json_each(data)
), to_update AS (
SELECT * FROM json_each(update_data)
WHERE key IN (SELECT key FROM old_data)
)
SELECT * FROM old_data
WHERE key NOT IN (SELECT key FROM to_update)
UNION ALL
SELECT * FROM to_update
) t;
$$;

