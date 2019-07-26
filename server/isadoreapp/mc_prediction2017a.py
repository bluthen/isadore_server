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

import numpy as np
import scg
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
from torch import Tensor, LongTensor, optim

M_I = 4; M_H = [2]; scgI = 1
inputNames = ["cum absh","cum inH20", "cum absh*inH20", "depth"]

class FFANN(nn.Module):
    def __init__(self,M_I,M_H):
        super(FFANN, self).__init__()
        self.M_H = M_H; self.M_I = M_I;
        if M_H:
            self.h0 = nn.Linear(M_I,M_H[0])
        for li in range(1,len(self.M_H)):
            attrName = "h%i"%li
            setattr(self, attrName,
                    nn.Linear(self.M_H[li-1],M_H[li]))
        if M_H:
            self.head = nn.Linear(M_H[-1],1)
        else:
            self.head = nn.Linear(M_I,1)

    def forward(self, x):
        for li in range(0,len(self.M_H)):
            layer = getattr(self,"h%i"%li)
            #x = F.tanh(layer(x))
            x = F.relu(layer(x))
        return F.tanh(self.head(x))

# ##################################################
# DATA PRE-PROCESSING FUNCTIONS
def scaleInput(X):
    N_X = X.size()[0]
    X.sub_(Tensor([[scaleInput.cum_absh_diff_rng[0],
                    scaleInput.cum_inH20_diff_rng[0],
                    scaleInput.cum_absh_inH20_prod_diff_rng[0],
                    scaleInput.depth_rng[0]]]).expand(N_X,M_I))
    X.copy_(torch.div(X, Tensor([[scaleInput.cum_absh_diff_rng[1]-scaleInput.cum_absh_diff_rng[0],
                                  scaleInput.cum_inH20_diff_rng[1]-scaleInput.cum_inH20_diff_rng[0],
                                  scaleInput.cum_absh_inH20_prod_diff_rng[1]-scaleInput.cum_absh_inH20_prod_diff_rng[0],
                                  scaleInput.depth_rng[1] - scaleInput.depth_rng[0]]]).expand(N_X,M_I)))
scaleInput.cum_absh_diff_rng = (0,2000.)
scaleInput.cum_inH20_diff_rng = (0,1700.)
scaleInput.cum_absh_inH20_prod_diff_rng = (0.,5400.)
scaleInput.depth_rng = (0,14.)
scaleInput.preMC_rng = (12.5,40.)

def unscaleInput(X):
    N_X = X.size()[0]
    X.copy_(torch.mul(X, Tensor([[scaleInput.cum_absh_diff_rng[1]-scaleInput.cum_absh_diff_rng[0],
                                  scaleInput.cum_inH20_diff_rng[1]-scaleInput.cum_inH20_diff_rng[0],
                                  scaleInput.cum_absh_inH20_prod_diff_rng[1]-scaleInput.cum_absh_inH20_prod_diff_rng[0],
                                  scaleInput.depth_rng[1] - scaleInput.depth_rng[0]]]).expand(N_X,M_I)))
    X.add_(Tensor([[scaleInput.cum_absh_diff_rng[0],
                    scaleInput.cum_inH20_diff_rng[0],
                    scaleInput.cum_absh_inH20_prod_diff_rng[0],
                    scaleInput.depth_rng[0]]]).expand(N_X,M_I))

def scaleOutput(Y):
    Y.sub_(scaleOutput.MC_lost_rng[0])
    Y.copy_(torch.div(Y, scaleOutput.MC_lost_rng[1] - scaleOutput.MC_lost_rng[0]))
scaleOutput.MC_lost_rng = (0.,30.)

def unScaleOutput(A_O):
    A_O.mul_(scaleOutput.MC_lost_rng[1] - scaleOutput.MC_lost_rng[0])
    A_O.add_(scaleOutput.MC_lost_rng[0])
# ##################################################

def MC_predict_beta2017(modelFile,M_H,inH20_diff,absh_diff,depth,initMC):

    # ##################################################
    # LOAD TRAINED MODEL PARAMETERS FROM FILE
    net = FFANN(M_I,M_H)
    net.load_state_dict(torch.load(modelFile))
    # ##################################################
    # ##################################################
    # COMPUTE MODEL INPUTS THEN
    # SCALE MODEL INPUTS
    N = len(absh_diff)
    # cum_absh_diff = Tensor(absh_diff).sub(Tensor(absh_diff))
    # cum_inH20_diff = Tensor(inH20_diff).sub(Tensor(inH20_diff))
    cum_absh_diff = Tensor(absh_diff).cumsum(0)
    cum_inH20_diff = Tensor(inH20_diff).cumsum(0)
    cum_absh_inH20_prod_diff = torch.mul(Tensor(absh_diff),Tensor(inH20_diff)).cumsum(0)
    depth_vec = Tensor(N); depth_vec[:] = depth
    X_in = torch.stack((cum_absh_diff,
                      cum_inH20_diff,
                      cum_absh_inH20_prod_diff,
                      depth_vec), dim=1)
    scaleInput(X_in)
    # ##################################################
    # ##################################################
    # RUN INPUTS THROUGH MODEL THEN
    # UNSCALE MODEL OUTPUTS
    A_out = net.forward(Variable(X_in, volatile=True)).data
    unScaleOutput(A_out)
    # ##################################################
    # ##################################################
    # SUBTRACT FROM INITIAL MC VALUES TO GIVE A
    # MC PREDICTION
    A_out.mul_(-1.0)
    A_out.add_(initMC)
    # ##################################################
    return A_out.tolist()
