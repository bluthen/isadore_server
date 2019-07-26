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
from bottle import route
from bottle import request, abort, response
from authentication import authorized
from cache import noCache
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.cm as cm
import numpy as np
import StringIO
from plot import graphLock
import json
import time
import logging


@route('/resources/data/heatmap', method=["GET"])
@authorized('User')
@noCache()
def getHeatmap():
    stime = time.clock()
    binDesc = json.loads(request.params.get('bin_desc'))
    values = json.loads(request.params.get('values'))["values"]
    options = json.loads(request.params.get('options'))
    dims = options["graph_dims"]
    tempRange = None
    if "temp_range" in options:
        tempRange = options["temp_range"]
    if dims[0] > 2000 or dims[1] > 2000:
        abort(400, 'options.graph_dims more than 2000x2000')
    binPerFt = float(request.params.get('bin_per_ft'))
    title = request.params.get('title', None)
    data = plotBinHeatmapData(binDesc, values, binPerFt, dims, title, tempRange)
    response.content_type = "image/png"
    logging.debug('heatmaptime.getHeatmap ' + str(time.clock() - stime))
    return data.getvalue()


def plotBinHeatmapData(binDesc, values, binPerFt, dims, title=None, tempRange=None):
    stime = time.clock()
    pngBuffer = StringIO.StringIO()
    try:
        graphLock.acquire()
        fig = plotBinHeatmap(binDesc, values, binPerFt, title=title, tempRange=tempRange)
        fig.set_dpi(80)
        dpi = fig.get_dpi()
        fig.set_size_inches(float(dims[0]) / dpi, float(dims[1]) / dpi)
        fig.savefig(pngBuffer, format="png", dpi=80)
        plt.close(fig)
        pngBuffer.seek(0)
    finally:
        graphLock.release()
    logging.debug('heatmaptime.plotBinHeatmapData ' + str(time.clock() - stime))
    return pngBuffer


def plotBinHeatmap(binDesc, values, binPerFt, minVal=50., maxVal=100., title=None, tempRange=None):
    """
    :param binDesc:
     shape = circle|rect
     radius || xlen && ylen
    :param values:
      [{pos: (x, y), eng: value}, ...]
    :param binPerFt:
    :return:
    """
    # All calculations will be done in positive coordinates
    # CREATE FIGURE PARTS
    stime = time.clock()
    fig = plt.figure()
    if title:
        plt.title(title)
    ax = fig.add_subplot(1, 1, 1)
    # COMPUTE FIGURE RANGE
    if binDesc["shape"] == "circle":
        Xmax = 2. * binDesc["radius"]
        Ymax = 2. * binDesc["radius"]
    elif binDesc["shape"] == "rect":
        Xmax = float(binDesc["xlen"])
        Ymax = float(binDesc["ylen"])
    else:
        raise Exception("Bad bin shape type")
    # CREATE INTERP GRID
    X = np.linspace(0, Xmax, Xmax * binPerFt)
    Y = np.linspace(0, Ymax, Ymax * binPerFt)
    X, Y = np.meshgrid(X, Y)
    # INTERPOLATE
    Z = interpolateVals(values, X, Y)
    print Z
    # # SCALE VALUES INTO MIN/MAX RANGE
    # Z = np.where(Z > minVal,Z,minVal)
    # Z = np.where(Z < maxVal,Z,maxVal)
    # Z = Z - minVal
    # Z = Z / (maxVal - minVal)
    # logging.debug(str(Z))
    # DRAW INTERPOLATED SPACE
    # ax.imshow(Z,vmin=0.,vmax=1.,cmap=cm.afmhot)
    # ax.imshow(Z,cmap=cm.afmhot)
    if tempRange:
        tr = tempRange
        zmax = np.max(Z)
        zmin = np.min(Z)
        print zmax, zmin
        vmin = 9999999
        vmax = -9999999
        for v in values:
            if v["eng"] < vmin:
                vmin = v["eng"]
            if v["eng"] > vmax:
                vmax = v["eng"]
        print vmax, vmin
        print "-----------"
        print tr
        cr = [(zmax-zmin)/(vmax-vmin)*(tr[0]-vmin)+zmin, (zmax-zmin)/(vmax-vmin)*(tr[1]-vmin)+zmin]
        print cr
        ax.contourf(X * binPerFt, Y * binPerFt, Z, cmap=cm.afmhot, vmin=cr[0], vmax=cr[1])
    else:
        ax.contourf(X * binPerFt, Y * binPerFt, Z, cmap=cm.afmhot)
    # DRAW BIN OUTLINE
    if binDesc["shape"] == "circle":
        binPatch = drawCircleBin((Xmax / 2. * binPerFt, Ymax / 2. * binPerFt), binDesc["radius"] * binPerFt)
    elif binDesc["shape"] == "rect":
        binPatch = drawRectBin(Xmax * binPerFt, Ymax * binPerFt)
    ax.add_patch(binPatch)
    # SET FIG/AXIS SPECS
    # set size
    ax.set_ylim((0, Ymax * binPerFt))
    ax.set_xlim((0, Xmax * binPerFt))
    # TODO: ensure figure will be square
    # TODO: draw inlet/outlet location/air dir indicator
    # ANNOTATE POINTS
    # TODO: draw directly over point, not with bottom, left corner over point
    for val in values:
        ax.annotate(str(val["eng"]),
                    np.array(val["pos"]) * binPerFt,
                    bbox={"boxstyle": "round", "fc": "0.8"})
    logging.debug('heatmaptime.plotBinHeatmap ' + str(time.clock() - stime))
    return fig


def drawCircleBin(center, r):
    return patches.Circle(center, r, fill=False, edgecolor=(0, 0, 0), linewidth=4.)


def drawRectBin(Xsize, Ysize, pos=(0, 0)):
    return patches.Rectangle(pos, Xsize, Ysize, fill=False, edgecolor=(0, 0, 0), linewidth=4.)


# def interpolateVals(values,gridX,gridY):
# # create interpolator
#     x = [val["pos"][0] for val in values]
#     y = [val["pos"][1] for val in values]
#     z = [val["eng"] for val in values]
#     rbf = interp.Rbf(x,y,z,function="linear")
#     # interpolate
#     return rbf(gridX,gridY)

def interpolateVals(values, gridX, gridY):
    stime = time.clock()
    gridSize = np.prod(gridX.shape)
    dists = np.empty((gridX.shape + (len(values),)))
    for vali, val in enumerate(values):
        tmpDist = np.vstack((gridX.reshape(1, gridSize), gridY.reshape(1, gridSize)))
        tmpDist -= np.array(val["pos"], ndmin=2).T
        tmpDist = [np.linalg.norm(d) for d in tmpDist.T]
        dists[:, :, vali] = np.array(tmpDist).reshape(gridX.shape)
    valWeights = np.empty_like(dists)
    sumDists = np.sum(dists, axis=2)  # sum distances
    for val in range(dists.shape[2]):
        valWeights[:, :, val] = 1. - dists[:, :, val] / sumDists
    gridZ = np.zeros_like(gridX)
    for vali, val in enumerate(values):
        gridZ += valWeights[:, :, vali] * val["eng"]
    logging.debug('heatmaptime.interpolateVals ' + str(time.clock() - stime))
    return gridZ
