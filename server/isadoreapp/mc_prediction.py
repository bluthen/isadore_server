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

import sys
import numpy as np
import cPickle
import gzip

N_back = 0
N_in = 5  # includes bias
MC_range = (10., 40.)
T_range = (55.0, 110.0)
RH_range = (0., 100.)


def calculate_ESN_inTRH_regWithAssumption(inlet_temp, outlet_temp, inlet_rh, outlet_rh, initMC):
    """
    Generates 15min MC predictions for each 15m inlet/outlet temp and rh subsample value from a fill air span. 
    Mixes output with predicted drying rate.
    Assumes all arguments have already been repaired and roll interpolated. 
    Repaired means missing values are interpolated. 
    Roll interpolate means values in-between an hour on either side of a roll is thrown out and interpolated values take their place. 
    All arguments are of the same 1d array length.

    :param inlet_temp: inlet temperature in Fahrenheit
    :param outlet_temp: outlet temperature in Fahrenheit
    :param inlet_rh: inlet RH in percent (ie 10.0 = 10.0%)
    :param outlet_temp: outlet RH in percent (ie 10.0 = 10.0%)
    :type inlet_temp: 1d Array of floats
    :type outlet_temp: 1d Array of floats
    :type inlet_rh: 1d Array of floats
    :type outlet_rh: 1d Array of floats
    :return: The moisture content (ie 10.0 = 10.0%)
    :rtype: 1d array of float same size as argument arrays.

    :raises ValueError: if all argument arrays are not the same length.
    """

    assumedHrsPerPt = 4.5; minAssumedMC = 10.0;
    initTdiffSample = 20        # about 5 hours in
    # ###
    # housekeeping
    # ###
    if len(set((len(inlet_temp), len(outlet_temp), len(inlet_rh), len(outlet_rh)))) != 1:
        raise ValueError("array sizes not equal")
    M_in = len(inlet_temp)
    # ###
    # load ESN matrices from best performer (taken from AWS server)
    # ###
    inFile = "result_useInitMC_randomParamSearch_crossVal_608.gz"
    fh = gzip.open(inFile)
    meanMSE = cPickle.load(fh)
    N = cPickle.load(fh)
    sparsityRatio = cPickle.load(fh)
    alpha = cPickle.load(fh)
    transientPeriodLen = cPickle.load(fh)
    Win_rng = cPickle.load(fh)
    W = cPickle.load(fh)
    Win = cPickle.load(fh)
    Wout = cPickle.load(fh)
    fh.close()
    # ###
    # make input matrix and scale input
    # ###
    # make
    U = np.zeros((N_in, M_in))  # bias is bottom row
    U[0, :] = inlet_temp
    U[2, :] = outlet_temp
    U[1, :] = inlet_rh
    U[3, :] = outlet_rh
    # scale
    U[0, :] = (U[0, :] - T_range[0]) / (T_range[1] - T_range[0])
    U[1, :] = (U[1, :] - RH_range[0]) / (RH_range[1] - RH_range[0])
    U[2, :] = (U[2, :] - T_range[0]) / (T_range[1] - T_range[0])
    U[3, :] = (U[3, :] - RH_range[0]) / (RH_range[1] - RH_range[0])
    # ###
    # run through ESN one time-step at a time to create ESN output
    # unscale output
    # return output
    # ###
    x = np.zeros(N)  # ESN state vector
    y = np.zeros((1, M_in))  # ESN output vector
    for t in range(1, M_in):
        x = np.dot(W, x)
        x += np.dot(Win, U[:, t])
        x = np.tanh(x)
        y[:, t] = np.tanh(np.dot(Wout, np.concatenate((U[:, t], x))))
    y_unscaled = y[0, :] * (MC_range[1] - MC_range[0]) + MC_range[0]
    # ###
    # compute assumed MC at each sample
    # ###
    dryingTimes = np.array(range(len(inlet_temp)),dtype=float)
    dryingTimes = dryingTimes * 0.25
    assumedPtsLost = dryingTimes * (1.0/assumedHrsPerPt)
    assumedMC = initMC-assumedPtsLost
    assumedMC = np.maximum(assumedMC,minAssumedMC)
    # ###
    # compute the mixing value
    # ###
    initTdiff = np.abs(inlet_temp[initTdiffSample] - outlet_temp[initTdiffSample])
    Tdiffs = np.abs(np.array(inlet_temp) - np.array(outlet_temp))
    lambda_t = Tdiffs / initTdiff
    lambda_t[lambda_t > 1.0] = 1.0; lambda_t[lambda_t < 0.0] = 0;
    # ###
    # mix and return
    # ###
    y_mixed = y_unscaled * (1.0 - lambda_t) + assumedMC * lambda_t
    return y_mixed

def calculate_ESN_inTRH(inlet_temp, outlet_temp, inlet_rh, outlet_rh):
    """
    Generates 15min MC predictions for each 15m inlet/outlet temp and rh subsample value from a fill air span.
    Assumes all arguments have already been repaired and roll interpolated.
    Repaired means missing values are interpolated.
    Roll interpolate means values in-between an hour on either side of a roll is thrown out and interpolated values take their place.
    All arguments are of the same 1d array length.

    :param inlet_temp: inlet temperature in Fahrenheit
    :param outlet_temp: outlet temperature in Fahrenheit
    :param inlet_rh: inlet RH in percent (ie 10.0 = 10.0%)
    :param outlet_temp: outlet RH in percent (ie 10.0 = 10.0%)
    :type inlet_temp: 1d Array of floats
    :type outlet_temp: 1d Array of floats
    :type inlet_rh: 1d Array of floats
    :type outlet_rh: 1d Array of floats
    :return: The moisture content (ie 10.0 = 10.0%)
    :rtype: 1d array of float same size as argument arrays.

    :raises ValueError: if all argument arrays are not the same length.
    """

    # ###
    # housekeeping
    # ###
    if len(set((len(inlet_temp), len(outlet_temp), len(inlet_rh), len(outlet_rh)))) != 1:
        raise ValueError("array sizes not equal")
    M_in = len(inlet_temp)
    # ###
    # load ESN matrices from best performer (taken from AWS server)
    # ###
    inFile = "result_useInitMC_randomParamSearch_crossVal_608.gz"
    fh = gzip.open(inFile)
    meanMSE = cPickle.load(fh)
    N = cPickle.load(fh)
    sparsityRatio = cPickle.load(fh)
    alpha = cPickle.load(fh)
    transientPeriodLen = cPickle.load(fh)
    Win_rng = cPickle.load(fh)
    W = cPickle.load(fh)
    Win = cPickle.load(fh)
    Wout = cPickle.load(fh)
    fh.close()
    # ###
    # make input matrix and scale input
    # ###
    # make
    U = np.zeros((N_in, M_in))  # bias is bottom row
    U[0, :] = inlet_temp
    U[2, :] = outlet_temp
    U[1, :] = inlet_rh
    U[3, :] = outlet_rh
    # scale
    U[0, :] = (U[0, :] - T_range[0]) / (T_range[1] - T_range[0])
    U[1, :] = (U[1, :] - RH_range[0]) / (RH_range[1] - RH_range[0])
    U[2, :] = (U[2, :] - T_range[0]) / (T_range[1] - T_range[0])
    U[3, :] = (U[3, :] - RH_range[0]) / (RH_range[1] - RH_range[0])
    # ###
    # run through ESN one time-step at a time to create ESN output
    # unscale output
    # return output
    # ###
    x = np.zeros(N)  # ESN state vector
    y = np.zeros((1, M_in))  # ESN output vector
    for t in range(1, M_in):
        x = np.dot(W, x)
        x += np.dot(Win, U[:, t])
        x = np.tanh(x)
        y[:, t] = np.tanh(np.dot(Wout, np.concatenate((U[:, t], x))))
    y_unscaled = y[0, :] * (MC_range[1] - MC_range[0]) + MC_range[0]
    return y_unscaled


if __name__ == '__main__':
    # ###
    # load repaired raw data from files (files created for another experiment)
    # ###
    repairedRawData_all = []
    repairedFillMeta_all = []
    sysName = []
    fh = gzip.open("model1_raw_repaired.gz", "r")
    sysName += ["model1"]
    repairedRawData_all += [cPickle.load(fh)]
    repairedFillMeta_all += [cPickle.load(fh)]
    fh.close()
    fh = gzip.open("model2_raw_repaired.gz", "r")
    sysName += ["model2"]
    repairedRawData_all += [cPickle.load(fh)]
    repairedFillMeta_all += [cPickle.load(fh)]
    fh.close()

    # ###
    # split into inlet and outlet T and RH
    # interpolate one hour on each side of roll d/t
    # ###
    inOutData_interpedRoll = []
    inOutData_interpedRoll_meta = []
    for rawi in range(len(repairedFillMeta_all)):
        for i in range(len(repairedFillMeta_all[rawi])):
            # in/out T, in/out RH
            if repairedFillMeta_all[rawi][i]["roll_dt"]:
                inOutData_interpedRoll += [np.zeros((4, repairedRawData_all[rawi][i].shape[1]))]
                inOutData_interpedRoll_meta += [repairedFillMeta_all[rawi][i]]
                rollDT = inOutData_interpedRoll_meta[-1]["roll_dt"][0]
                fillStartDT = inOutData_interpedRoll_meta[-1]["start_dt"]
                rollSubsampleCount = int(
                    np.floor((rollDT - fillStartDT).days * 24 * 4 + (rollDT - fillStartDT).seconds / 60. / 15.))
                inOutData_interpedRoll_meta[-1]["roll_subsample_count"] = rollSubsampleCount
                inOutData_interpedRoll[-1][0, :rollSubsampleCount] = repairedRawData_all[rawi][i][1,
                                                                     :rollSubsampleCount]
                inOutData_interpedRoll[-1][1, :rollSubsampleCount] = repairedRawData_all[rawi][i][0,
                                                                     :rollSubsampleCount]
                inOutData_interpedRoll[-1][2, :rollSubsampleCount] = repairedRawData_all[rawi][i][3,
                                                                     :rollSubsampleCount]
                inOutData_interpedRoll[-1][3, :rollSubsampleCount] = repairedRawData_all[rawi][i][2,
                                                                     :rollSubsampleCount]
                inOutData_interpedRoll[-1][0, rollSubsampleCount:] = repairedRawData_all[rawi][i][0,
                                                                     rollSubsampleCount:]
                inOutData_interpedRoll[-1][1, rollSubsampleCount:] = repairedRawData_all[rawi][i][1,
                                                                     rollSubsampleCount:]
                inOutData_interpedRoll[-1][2, rollSubsampleCount:] = repairedRawData_all[rawi][i][2,
                                                                     rollSubsampleCount:]
                inOutData_interpedRoll[-1][3, rollSubsampleCount:] = repairedRawData_all[rawi][i][3,
                                                                     rollSubsampleCount:]
                for j in range(4):
                    b = inOutData_interpedRoll[-1][j, rollSubsampleCount - 4]
                    m = (inOutData_interpedRoll[-1][j, rollSubsampleCount + 4] - inOutData_interpedRoll[-1][
                        j, rollSubsampleCount - 4]) / 9.
                    for k in range(9):
                        inOutData_interpedRoll[-1][j, rollSubsampleCount - 4 + k] = m * k + b
            else:
                print "selected fill", i, "missing roll DT"

    # ###
    # remove unwanted fills and note which ones to clip a little off the end
    # ###
    # maybe 465
    ignoreIdxs = (547, 550, 539, 480, 481, 384, 281, 98, 47)
    clipIdxs = (
        (386, 420),
        (384, 416),
        (306, 381),
        (295, 263)
    )

    # ###
    # interpolate select regions where error data is present
    # ###
    # (idx,startSubSample,endSubSample)
    interpRegions = (
        (563, 150, 154),  # check this one in last figure
        (660, 175, 178),
        (669, 166, 171),
        (678, 156, 163),
        (620, 243, 260),
        (627, 254, 273),
        (580, 366, 413),
        (581, 356, 414),
        (588, 366, 406),
        (595, 355, 398),
        (554, 336, 355),
        (518, 380, 388),
        (461, 46, 55),
        (461, 115, 126),
        (462, 312, 328),
        (465, 340, 355),
        (434, 94, 136),
        (439, 312, 354),
        (342, 17, 27),
        (346, 5, 25),
        (329, 72, 80),
        (328, 8, 19),
        (331, 103, 113),
        (300, 81, 91),
        (302, 71, 81),
        (303, 15, 23),
        (309, 291, 301),
        (311, 111, 120),
        (296, 76, 88),
        (297, 456, 469),
        (298, 82, 93),
        (270, 96, 109),
        (182, 367, 376),
        (184, 372, 383),
        (194, 310, 320),
        (142, 16, 24),
        (129, 16, 23),
        (130, 199, 208),
        (105, 185, 192),
        (41, 330, 385),
        (13, 0, 36),
        (14, 0, 34)
    )
    for i in range(len(inOutData_interpedRoll_meta)):
        for interpInfo in interpRegions:
            # if inOutData_interpedRoll_meta[i]["id"] == interpInfo[0]:
            interpSz = interpInfo[2] - interpInfo[1] + 1
            if i == interpInfo[0]:
                for j in range(4):
                    b = inOutData_interpedRoll[i][j, interpInfo[1]]
                    m = (inOutData_interpedRoll[i][j, interpInfo[2]] - inOutData_interpedRoll[i][
                        j, interpInfo[1]]) / float(interpInfo[2] - interpInfo[1])
                    for k in range(interpSz):
                        inOutData_interpedRoll[i][j, interpInfo[1] + k] = m * k + b

    # ###
    # break into train and test fills
    # ###
    testRatio = 0.2
    testIdxs = np.random.choice(range(len(inOutData_interpedRoll)),
                                size=int(np.ceil(len(inOutData_interpedRoll) * testRatio)),
                                replace=False)
    trainIdxs = list(set(range(len(inOutData_interpedRoll))) - set(testIdxs))

    # ###
    # compute the position of the MC samples (in subsamples) taken after air rotation (aka size of data set)
    # exclude MC samples taken within 4 hours of stop air time
    # also compute the total number of subsamples for the entire fill
    # ###
    for i in range(len(inOutData_interpedRoll_meta)):
        fillStartDT = inOutData_interpedRoll_meta[i]["start_dt"]
        fillEndDT = inOutData_interpedRoll_meta[i]["end_dt"]
        for di in range(len(inOutData_interpedRoll_meta[i]["during_mc"])):
            MC_DT = inOutData_interpedRoll_meta[i]["during_mc"][di][0]
            MC_SubsampleCount = int(
                np.floor((MC_DT - fillStartDT).days * 24 * 4 + (MC_DT - fillStartDT).seconds / 60. / 15.))
            inOutData_interpedRoll_meta[i]["during_mc"][di] = (inOutData_interpedRoll_meta[i]["during_mc"][di][0],
                                                               inOutData_interpedRoll_meta[i]["during_mc"][di][1],
                                                               MC_SubsampleCount)
        fillSubsampleCount = int(
            np.floor((fillEndDT - fillStartDT).days * 24 * 4 + (fillEndDT - fillStartDT).seconds / 60. / 15.))
        inOutData_interpedRoll_meta[i]["subsample_count"] = fillSubsampleCount
    # ###
    # eval calculate function
    # ###
    est_mc = calculate_ESN_inTRH(list(inOutData_interpedRoll[0][0, :]),
                                 list(inOutData_interpedRoll[0][1, :]),
                                 list(inOutData_interpedRoll[0][2, :]),
                                 list(inOutData_interpedRoll[0][3, :]))
    print "EST MC%: ", est_mc

    est_mc2 = calculate_ESN_inTRH_regWithAssumption(list(inOutData_interpedRoll[0][0, :]),
                                                    list(inOutData_interpedRoll[0][1, :]),
                                                    list(inOutData_interpedRoll[0][2, :]),
                                                    list(inOutData_interpedRoll[0][3, :]),
                                                    np.mean(inOutData_interpedRoll_meta[0]["pre_mc"]))
    print "EST MC%: ", est_mc2
