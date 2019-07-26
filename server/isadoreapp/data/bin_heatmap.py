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

from isadoreapp import app
import flask
from flask import request, abort, Response
from isadoreapp.authentication import authorized
from isadoreapp.cache import noCache
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.cm as cm
import numpy as np
from io import StringIO
from isadoreapp.data.plot import graphLock
import json
import time
import logging


@app.route('/resources/data/heatmap', methods=["GET"])
@authorized('User')
@noCache()
def get_heatmap():
    stime = time.clock()
    bin_desc = json.loads(request.values.get('bin_desc'))
    values = json.loads(request.values.get('values'))["values"]
    options = json.loads(request.values.get('options'))
    dims = options["graph_dims"]
    temp_range = None
    if "temp_range" in options:
        temp_range = options["temp_range"]
    if dims[0] > 2000 or dims[1] > 2000:
        abort(400, 'options.graph_dims more than 2000x2000')
    bin_per_ft = float(request.values.get('bin_per_ft'))
    title = request.values.get('title', None)
    data = plot_bin_heatmap_data(bin_desc, values, bin_per_ft, dims, title, temp_range)
    logging.debug('heatmaptime.getHeatmap ' + str(time.clock() - stime))
    return flask.send_file(data, mimetype="image/png")


def plot_bin_heatmap_data(bin_desc, values, bin_per_ft, dims, title=None, temp_range=None):
    stime = time.clock()
    png_buffer = StringIO()
    try:
        graphLock.acquire()
        fig = plot_bin_heatmap(bin_desc, values, bin_per_ft, title=title, temp_range=temp_range)
        fig.set_dpi(80)
        dpi = fig.get_dpi()
        fig.set_size_inches(float(dims[0]) / dpi, float(dims[1]) / dpi)
        fig.savefig(png_buffer, format="png", dpi=80)
        plt.close(fig)
        png_buffer.seek(0)
    finally:
        graphLock.release()
    logging.debug('heatmaptime.plotBinHeatmapData ' + str(time.clock() - stime))
    return png_buffer


def plot_bin_heatmap(bin_desc, values, bin_per_ft, min_val=50., max_val=100., title=None, temp_range=None):
    """
    :param bin_desc:
     shape = circle|rect
     radius || xlen && ylen
    :param values:
      [{pos: (x, y), eng: value}, ...]
    :param bin_per_ft:
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
    if bin_desc["shape"] == "circle":
        xmax = 2. * bin_desc["radius"]
        ymax = 2. * bin_desc["radius"]
    elif bin_desc["shape"] == "rect":
        xmax = float(bin_desc["xlen"])
        ymax = float(bin_desc["ylen"])
    else:
        raise Exception("Bad bin shape type")
    # CREATE INTERP GRID
    x = np.linspace(0, xmax, xmax * bin_per_ft)
    y = np.linspace(0, ymax, ymax * bin_per_ft)
    x, y = np.meshgrid(x, y)
    # INTERPOLATE
    z = interpolate_vals(values, x, y)
    print(z)
    # # SCALE VALUES INTO MIN/MAX RANGE
    # Z = np.where(Z > minVal,Z,minVal)
    # Z = np.where(Z < maxVal,Z,maxVal)
    # Z = Z - minVal
    # Z = Z / (maxVal - minVal)
    # logging.debug(str(Z))
    # DRAW INTERPOLATED SPACE
    # ax.imshow(Z,vmin=0.,vmax=1.,cmap=cm.afmhot)
    # ax.imshow(Z,cmap=cm.afmhot)
    if temp_range:
        tr = temp_range
        zmax = np.max(z)
        zmin = np.min(z)
        print(zmax, zmin)
        vmin = 9999999
        vmax = -9999999
        for v in values:
            if v["eng"] < vmin:
                vmin = v["eng"]
            if v["eng"] > vmax:
                vmax = v["eng"]
        print(vmax, vmin)
        print("-----------")
        print(tr)
        cr = [(zmax-zmin)/(vmax-vmin)*(tr[0]-vmin)+zmin, (zmax-zmin)/(vmax-vmin)*(tr[1]-vmin)+zmin]
        print(cr)
        ax.contourf(x * bin_per_ft, y * bin_per_ft, z, cmap=cm.afmhot, vmin=cr[0], vmax=cr[1])
    else:
        ax.contourf(x * bin_per_ft, y * bin_per_ft, z, cmap=cm.afmhot)
    # DRAW BIN OUTLINE
    if bin_desc["shape"] == "circle":
        bin_patch = draw_circle_bin((xmax / 2. * bin_per_ft, ymax / 2. * bin_per_ft), bin_desc["radius"] * bin_per_ft)
    elif bin_desc["shape"] == "rect":
        bin_patch = draw_rect_bin(xmax * bin_per_ft, ymax * bin_per_ft)
    ax.add_patch(bin_patch)
    # SET FIG/AXIS SPECS
    # set size
    ax.set_ylim((0, ymax * bin_per_ft))
    ax.set_xlim((0, xmax * bin_per_ft))
    # TODO: ensure figure will be square
    # TODO: draw inlet/outlet location/air dir indicator
    # ANNOTATE POINTS
    # TODO: draw directly over point, not with bottom, left corner over point
    for val in values:
        ax.annotate(str(val["eng"]),
                    np.array(val["pos"]) * bin_per_ft,
                    bbox={"boxstyle": "round", "fc": "0.8"})
    logging.debug('heatmaptime.plotBinHeatmap ' + str(time.clock() - stime))
    return fig


def draw_circle_bin(center, r):
    return patches.Circle(center, r, fill=False, edgecolor=(0, 0, 0), linewidth=4.)


def draw_rect_bin(xsize, ysize, pos=(0, 0)):
    return patches.Rectangle(pos, xsize, ysize, fill=False, edgecolor=(0, 0, 0), linewidth=4.)


# def interpolateVals(values,gridX,gridY):
# # create interpolator
#     x = [val["pos"][0] for val in values]
#     y = [val["pos"][1] for val in values]
#     z = [val["eng"] for val in values]
#     rbf = interp.Rbf(x,y,z,function="linear")
#     # interpolate
#     return rbf(gridX,gridY)

def interpolate_vals(values, grid_x, grid_y):
    stime = time.clock()
    grid_size = np.prod(grid_x.shape)
    dists = np.empty((grid_x.shape + (len(values),)))
    for vali, val in enumerate(values):
        tmp_dist = np.vstack((grid_x.reshape(1, grid_size), grid_y.reshape(1, grid_size)))
        tmp_dist -= np.array(val["pos"], ndmin=2).T
        tmp_dist = [np.linalg.norm(d) for d in tmp_dist.T]
        dists[:, :, vali] = np.array(tmp_dist).reshape(grid_x.shape)
    val_weights = np.empty_like(dists)
    sum_dists = np.sum(dists, axis=2)  # sum distances
    for val in range(dists.shape[2]):
        val_weights[:, :, val] = 1. - dists[:, :, val] / sum_dists
    grid_z = np.zeros_like(grid_x)
    for vali, val in enumerate(values):
        grid_z += val_weights[:, :, vali] * val["eng"]
    logging.debug('heatmaptime.interpolateVals ' + str(time.clock() - stime))
    return grid_z
