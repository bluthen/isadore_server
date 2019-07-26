CREATE OR REPLACE FUNCTION calc_wetbulb(tc DOUBLE PRECISION, rh DOUBLE PRECISION, p DOUBLE PRECISION)
    RETURNS DOUBLE PRECISION
AS $$
if 'hygrometry' in SD:
    hygrometry = SD['hygrometry']
else:
    import hygrometry
    SD['hygrometry'] = hygrometry
return hygrometry.conv_c2f(hygrometry.wetbulb(tc, rh, p))
$$ LANGUAGE plpython2u IMMUTABLE;


CREATE OR REPLACE FUNCTION calc_absolute_humidity(tc DOUBLE PRECISION, rh DOUBLE PRECISION)
    RETURNS DOUBLE PRECISION
AS $$
if 'hygrometry' in SD:
    hygrometry = SD['hygrometry']
else:
    import hygrometry
    SD['hygrometry'] = hygrometry
return hygrometry.absolute_humidity(tc, rh)
$$ LANGUAGE plpython2u IMMUTABLE;


CREATE EXTENSION pgcrypto;
