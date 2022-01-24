# -*- coding: utf-8 -*-
"""
Created on 2020/9/14
@project: SNNFlow
@filename: Torch_Backend
@author: Hong Chaofei
@contact: hongchf@gmail.com
@description:
"""
from .Backend import Backend, backends
import torch

import numpy as np
from torch import jit
#from torch.nn import Module, Parameter
import torch.nn.functional as fn
from typing import Tuple, Dict, Callable

class Torch_Backend(Backend):
    simulator_name = 'pytorch'

    def __init__(self, device='cpu'):
        super(Torch_Backend, self).__init__()

        self.device = device
        self.data_type = torch.float
        self.debug_data = []
        pass

    def build(self):
        # self._graph_var_dicts = {'variables_dict': self._variables, 'temp_dict': dict(), 'update_dict': dict(),
        #                          'reduce_dict': dict()}
        # self._graph_var_dicts['temp_dict']['example_temp_dict_pytorch_datatype'] = torch.empty(1)
        # self._graph_var_dicts['update_dict']['example_temp_dict_pytorch_datatype'] = torch.empty(1)
        # self._graph_var_dicts['reduce_dict']['example_temp_dict_pytorch_datatype'] = torch.empty(1)
        #
        # #self.update_step = jit.trace(self.update_step)
        # self.graph_update_step = jit.trace(self.graph_update_step,[])
        pass


    # def graph_update_step(self):
    #
    #     for op in self._graph_operations:
    #         inputs = []
    #         for var in op[2]:
    #             inputs.append(self._graph_var_dicts[var[0]][var[1]])
    #
    #         if op[0][0] is 'reduce_dict':
    #             self._graph_var_dicts['reduce_dict'][op[0][1]].append(op[1](*inputs))
    #         else:
    #             self._graph_var_dicts[op[0][0]][op[0][1]] = op[1](*inputs)
    #
    #     return tuple(self._graph_var_dicts['variables_dict'].values())

    def add_backend_variable(self, name, shape, value=None, grad=False, is_sparse=False, init=None):
        '''
        Parameters
        ----------
        name
        shape
        value
        init
        Returns
        -------
        '''
        # TODO: 现在先尝试一下在backend简单建立一个跑一下，以后再改
        if value is not None:
            if hasattr(value, "__len__"):
                if value.shape != shape:
                    raise ValueError("Value is not scalar and the shape of Value is not equal to shape")
                # add a sparse matrices with all dimensions greater than 2
                if is_sparse:
                    i = np.nonzero(value)
                    v = value[i]

                    # Index for sparse matrix
                    sparse_index = name + '_sparse_index'
                    self._variables[sparse_index] = torch.LongTensor(i).to(device=self.device)
                    self._InitVariables_dict[sparse_index] = self._variables[sparse_index]

                    # Value for sparse matrix
                    sparse_value = name + '_sparse_value'
                    if init is not None:
                        # self._variables[sparse_value] = self.init_param(True, init)
                        data = torch.empty(shape, dtype=torch.float32, device=self.device, requires_grad=True)
                        self._variables[sparse_value] = self.param_init_operate[init](data)
                    else:
                        self._variables[sparse_value] = torch.tensor(v, dtype=torch.float32, requires_grad=True, device=self.device)
                    self._parameters_dict[sparse_value] = self._variables[sparse_value]

                    # The shape of sparse matrix
                    sparse_shape = name + '_sparse_shape'
                    self._variables[sparse_shape] = torch.Size(shape)
                    self._InitVariables_dict[sparse_shape] = self._variables[sparse_shape]

                    # Sparse matrix
                    self._variables[name] = torch.sparse.FloatTensor(self._variables[sparse_index], self._variables[sparse_value], self._variables[sparse_shape])
                else:
                    # add a non sparse matrices with all dimensions greater than 2
                    if init is not None:
                        data = torch.empty(shape, dtype=torch.float32, device=self.device, requires_grad=grad)
                        self._variables[name] = self.param_init_operate[init](data)
                    else:
                        self._variables[name] = torch.tensor(value, dtype=torch.float32, device=self.device,
                                                                 requires_grad=grad)
            elif len(shape) == 0:
                # add constant
                self._variables[name] = torch.tensor(value, dtype=torch.float32, device=self.device, requires_grad=grad)
            else:
                # add a matrix through constant
                if init is not None:
                    # self._variables[name] = self.init_param(grad, init)
                    data = torch.empty(shape, dtype=torch.float32, device=self.device, requires_grad=grad)
                    self._variables[name] = self.param_init_operate[init](data)
                else:
                    self._variables[name] = value*torch.ones(shape, dtype=torch.float32, device=self.device, requires_grad=grad)
                # self._variables[name] = value*torch.ones(shape, dtype=torch.float32, device=self.device, requires_grad=grad)
        return self._variables[name]

    # def init_param(self, grad, *init):
    #     if init[0] in self.param_init_operate:
    #         init_op = self.param_init_operate[init[0]]
    #     else:
    #         raise ValueError("No init operate %s in param_init_operate" % init[0])
    #     inputs = []
    #     shape = init[1]
    #     data = torch.empty(shape, dtype=torch.float32, device=self.device, requires_grad=grad)
    #     inputs.append(data)
    #
    #     for var in init[2:]:
    #         inputs.append(var)
    #     return init_op(*inputs)

    def get_str(self, level):
        return level*' ' + 'torch_backend'

    def threshold(self, x, v_th):
        return torch.gt(x, v_th).float()

    def cat(self, x, dim=1):
        return torch.cat(x, dim)

    def stack(self, x, dim=1):       # 在指定维度dim上连接（concatenate）若干个张量。
        try:
            return torch.stack(x, dim)
        except:
            # patch for SLIF 2[O]
            for ii in range(len(x)):
                if x[ii].dim() ==2:
                    tmp = torch.zeros_like(x[ii])
                    tmp = torch.stack([x[ii], tmp], dim=1)
                    x[ii] = tmp
            return torch.stack(x, dim)

    def reduce_sum(self, x, *dim):
        if len(dim)==0:
            dim = 1
        return torch.sum(x, dim=dim)

    def index_select(self, x,  indices, dim=1):
        return torch.index_select(x, dim=dim, index=indices)

    def scatter(self, x, indices):
        return torch.scatter(x, dim=0, index=indices)

    def conv1d(self, x, kernel):
        return torch.conv1d(x, kernel)

    def conv_trans1d(self, x, kernel):
        return torch.conv_transpose1d(x, kernel)

    def conv_2d(self, x, kernel, stride, padding, dilation, groups):
        if x.dim() == kernel.dim() + 1:
            xshape = list(x.shape)
            xshape[0] = xshape[0]*xshape[1]
            extend_size = xshape[1]
            xshape.pop(1)
            out = fn.conv2d(x.reshape(xshape), kernel, stride=int(stride), padding=int(padding), dilation=int(dilation), groups=int(groups))
            outshape = list(out.shape)
            outshape[0] = outshape[0]//extend_size
            outshape.insert(1, extend_size)
            return out.view(outshape)
        else:
            return fn.conv2d(x, kernel, stride=int(stride), padding=int(padding), dilation=int(dilation), groups=int(groups))


    def conv_max_pool2d(self, x, kernel, max_kernel, stride, padding, dilation, groups):

        return fn.max_pool2d(fn.conv2d(x, kernel, stride=int(stride), padding=int(padding), dilation=int(dilation), groups=int(groups)), int(max_kernel[0]))

    def reshape_mat_mult(self, A, X):

        if A.dim() == 4:
            (batchsize, outchannels, H, W) = A.shape
            A = A.view(batchsize, -1)
        elif A.dim() == 5:
            (batchsize, extend, outchannels, H, W) = A.shape
            A = A.view(batchsize, extend, -1)

        return torch.matmul(A, X.permute(1, 0))

    def add(self, x, y):

        return x + y

    def minus(self, x, y):
        return x - y

    def div(self, x, y):
        return torch.div(x, y)

    def relu(self, x):
        return torch.relu(x)

    def sigmoid(self, x):
        return torch.sigmoid(x)

    def mat_mult(self, A, X):
        '''
        Parameters
        ----------
        A--->preGroup:input
        X--->postGroup:weight
        Returns
        -------
        '''
        X = X.permute(1, 0)
        return torch.matmul(A, X)

    def mat_mult_pre(self, A, X):
        '''
        Parameters
        ----------
        A---> postGroup
        X---> preGroup
        Returns
        -------
        '''
        A = A.permute(1, 0)
        return torch.matmul(A, X)

    def sparse_mat_mult(self, A, X):
        '''
       Parameters
       ----------
       A--->preGroup:sparseWeight(post, pre)
       X--->postGroup:input(batch, pre)
       Returns
       -------
       '''

        X = X.permute(1, 0)
        result = torch.sparse.mm(A, X)
        result = result.permute(1, 0)
        return result

    def var_mult(self, A, X):
        return A * X


    def mult_sum(self, A, X):
        try:
            X = X.permute(1, 0)
            A = A.permute(0,2,1)
            return torch.sum(torch.matmul(A, X), dim=-2)
        except:
            pass

    def mat_linear(self, A, X, b):
        return torch.matmul(A, X) + b

    def var_linear(self, A, X, b):

        return A*X+b

    def to_numpy(self, data: torch.Tensor):
        return data.detach().cpu().numpy()

    def to_tensor(self, data):
        if isinstance(data, torch.Tensor):
            return data.to(torch.float).to(self.device)
        else:
            return torch.tensor(data, dtype=torch.float, device=self.device)

    def exp(self, x):
        return torch.exp(x)


    def clamp_(self, data, min, max):
        with torch.no_grad():
            data.clamp_(min, max)


    def clamp_max_(self, data, max):
        with torch.no_grad():
            data.clamp_max_(max)



    def clamp_min_(self, data, min):
        with torch.no_grad():
            data.clamp_min_(min)


    def uniform(self, data, a=0.0, b=1.0):
        '''
        Args:
            data(tensor): an n-dimensional torch.Tensor
            a(float): the lower bound of the uniform distribution
            b(float): the upper bound of the uniform distribution
        Returns:
            torch.nn.init.uniform_(data, a=0.0, b=1.0)
        '''
        return torch.nn.init.uniform_(data, a, b)


    def normal(self, data, mean=0.0, std=1.0):
        '''
        Args:
            data(tensor): an n-dimensional torch.Tensor
            mean(float): the mean of the normal distribution
            std(float): the standard deviation of the normal distribution
        Returns:
            torch.nn.init.normal_(data, mean=0.0, std=1.0)
        '''
        return torch.nn.init.normal_(data, mean, std)



    def xavier_normal(self, data, gain=1.0):
        '''
        Args:
            data(tensor): an n-dimensional torch.Tensor
            gain: an optional scaling factor
        Returns:
            torch.nn.init.xavier_normal_(data, gain=1.0)
        '''
        return torch.nn.init.xavier_normal_(data, gain)


    def xavier_uniform(self, data, gain=1.0):
        '''
        Args:
            data(tensor): an n-dimensional torch.Tensor
            gain: an optional scaling factor
        Returns:
            torch.nn.init.xavier_uniform_(data, gain=1.0)
        '''
        return torch.nn.init.xavier_uniform_(data, gain)


    def kaiming_normal(self, data, a=0, mode='fan_in', nonlinearity='leaky_relu'):
        '''
        Args:
            data(tensor): an n-dimensional torch.Tensor
            a: the negative slope of the rectifier used after this layer (only used with 'leaky_relu')
            mode: either 'fan_in' (default) or 'fan_out'. Choosing 'fan_in' preserves the magnitude of the variance of the weights in the forward pass. Choosing 'fan_out' preserves the magnitudes in the backwards pass.
            nonlinearity: the non-linear function (nn.functional name), recommended to use only with 'relu' or 'leaky_relu' (default).
        Returns:
            torch.nn.init.kaiming_normal_(data, a=0, mode='fan_in', nonlinearity='leaky_relu')
        '''
        return torch.nn.init.kaiming_normal_(data, a, mode, nonlinearity)


    def kaiming_uniform(self, data, a=0, mode='fan_in', nonlinearity='leaky_relu'):
        '''
        Args:
            data(tensor): an n-dimensional torch.Tensor
            a: the negative slope of the rectifier used after this layer (only used with 'leaky_relu')
            mode: either 'fan_in' (default) or 'fan_out'. Choosing 'fan_in' preserves the magnitude of the variance of the weights in the forward pass. Choosing 'fan_out' preserves the magnitudes in the backwards pass.
            nonlinearity: the non-linear function (nn.functional name), recommended to use only with 'relu' or 'leaky_relu' (default).
        Returns:
            torch.nn.init.kaiming_uniform_(data, a=0, mode='fan_in', nonlinearity='leaky_relu')
        '''
        return torch.nn.init.kaiming_uniform_(data, a, mode, nonlinearity)

    # def reset(self, x, v_reset, u_reset, spike):
    #
    #     # if hasattr(x, "__len__"):
    #     #     if x.shape != spike.shape:
    #     #         raise ValueError("%s and %s do not match" % (x.shape, spike.shape))
    #     mask = torch.eq(spike, 1)
    #     x[mask] = v_reset
    #     x[mask] += u_reset
    #     return x

    # def izh_v(self, v, u, psp):
    #     v = v+self.dt*(0.04*v*v+5*v+140-u+psp)
    #     return v
    #
    # def izh_u(self, a, b, v, u):
    #     u = u+self.dt*a*(b*v-u)
    #     return u

backends[Torch_Backend.simulator_name] = Torch_Backend

# test = Torch_Backend()
# th = test.basic_operate['threshold']
# print(th(-1.0))