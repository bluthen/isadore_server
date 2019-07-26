#   Copyright 2010-2019 Dan Elliott, Russell Valentine
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import math


def conv_F2C(f):
    """Convert fahrenheit to Celsius"""
    return (f - 32.0) * 0.555556


def conv_C2F(c):
    """Convert Celsius to Fahrenheit"""
    return c*1.8+32.0


def noaa_Td(Tc, RH):
    """
    Calculates vapor pressure, saturation vapor pressure, and dew point in celcius
    returns [vapor pressure, saturation vapor pressure, dew point]
    """
    Tc = float(Tc)
    RH = float(RH)
    es = 6.112 * math.exp(17.67 * Tc / (Tc + 243.5))
    V = es * RH / 100.0
    if V != 0:
        l = math.log(V / 6.112)
        Td = 243.5 * l / ( 17.67 - l)
    else:
        Td = float('nan')
    return [es, V, Td]


#debug_counts=[]
def noaa_calc_wb(Edifference, Twguess, Ctemp, MBpressure, E2, previoussign, incr):
    """
    Incremental wetbulb calculation
    Source: http://www.srh.noaa.gov/epz/?n=wxcalc_rh
    """
    #global debug_counts
    count = 0

    #Make sure everything is a float
    Edifference = float(Edifference)
    Twguess = float(Twguess)
    Ctemp = float(Ctemp)
    MBpressure = float(MBpressure)
    E2 = float(E2)
    previoussign = previoussign
    incr = float(incr)

    while math.fabs(Edifference) > 0.0005:
        Ewguess = 6.112 * math.exp((17.67 * Twguess) / (Twguess + 243.5))
        Eguess = Ewguess - MBpressure * (Ctemp - Twguess) * 0.00066 * (1.0 + (0.00115 * Twguess))
        Edifference = E2 - Eguess
        #print Edifference

        #print Twguess, Ewguess, E2, Eguess, Edifference, count

        #Had to change this from Edifference == 0
        if math.fabs(Edifference) < 0.0005:
            break
        else:
            if Edifference < 0.0:
                cursign = -1
                if cursign != previoussign:
                    previoussign = float(cursign)
                    incr = incr/10.0
                else:
                    incr = incr
            else:
                cursign = 1
                if cursign != previoussign:
                    previoussign = cursign
                    incr = incr/10.0
                else:
                    incr = incr

        Twguess = float(Twguess) + float(incr) * float(previoussign)
        count += 1
        #if count > 15:
        #    break
    wetbulb = Twguess
    #print wetbulb
    #debug_counts.append(count)
    #print "Count %d" % (count,)
    return wetbulb


def noaa_calc_sWB(Tc, RH, P):
    """
    Calculate Wet bulb in Celcius given temperature, relative humidity, and pressure.
    """
    RH = float(RH)
    if RH <= 0:
        RH = 0.
    [es, V, Td] = noaa_Td(float(Tc), RH)
    return noaa_calc_wb(1., 0., float(Tc), float(P), float(V), 1, 10.)
