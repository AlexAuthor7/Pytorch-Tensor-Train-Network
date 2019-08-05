#!/usr/bin/env python3 

import numpy as np 
import torch 
from torch.nn import Parameter
from tc_cores import TensorTrain 

torch.manual_seed(42)

def _validate_input_parameters(is_tensor, shape, **params):
    r"""Internal function for validating input parameters
    Args:
        is_tensor: bool, determines whether we attempt to construct a TT-tensor or
                    a TT-matrix (needed for the correct shape checks).
        shape: array, the desired shape of the generated TT object
        params: optional, possible values:
        batch_size: int, for constructing batches
        tt_rank: array or int, desired TT-ranks
  """
    if is_tensor:
        if len(shape.shape) != 1:
            raise ValueError('shape should be 1d array, got %a' % shape)
        if np.any(shape < 1):
            raise ValueError('all elements in `shape` should be positive, got %a' %shape)
        if not all(isinstance(sh, np.integer) for sh in shape):
            raise ValueError('all elements in `shape` should be integers, got %a' %shape)
    else:
        if len(shape.shape) != 2:
            raise ValueError('shape should be 2d array, got %a' % shape)
        if shape[0].size != shape[1].size:
            raise ValueError('shape[0] should have the same length as shape[1], but'
                       'got %d and %d' % (shape[0].size, shape[1].size))
        if np.any(shape.flatten() < 1):
            raise ValueError('all elements in `shape` should be positive, got %a' %shape)
        if not all(isinstance(sh, np.integer) for sh in shape.flatten()):
            raise ValueError('all elements in `shape` should be integers, got %a' %shape)

    if 'batch_size' in params:
        batch_size = params['batch_size']
        if not isinstance(batch_size, (int, np.integer)):
            raise ValueError('`batch_size` should be integer, got %f' % batch_size)
        if batch_size < 1:
            raise ValueError('Batch size should be positive, got %d' % batch_size)
    if 'tt_rank' in params:
        tt_rank = params['tt_rank']
        if tt_rank.size == 1:
            if not isinstance(tt_rank[()], np.integer):
                raise ValueError('`tt_rank` should be integer, got %f' % tt_rank[()])
        if tt_rank.size > 1:
            if not all(isinstance(tt_r, np.integer) for tt_r in tt_rank):
                raise ValueError('all elements in `tt_rank` should be integers, got %a' % tt_rank)
        if np.any(tt_rank < 1):
            raise ValueError('`tt_rank` should be positive, got %a' % tt_rank)

        if is_tensor:
            if tt_rank.size != 1 and tt_rank.size != (shape.size + 1):
                raise ValueError('`tt_rank` array has inappropriate size, expected'
                                '1 or %d, got %d' % (shape.size + 1, tt_rank.size))
        else:
            if tt_rank.size != 1 and tt_rank.size != (shape[0].size + 1):
                raise ValueError('`tt_rank` array has inappropriate size, expected'
                         '1 or %d, got %d' % (shape[0].size + 1, tt_rank.size))


def tensor_ones(shape):
    r"""Generate TT-tensor of the given shape with all entries equal to 1.
    Args:
        shape: array representing the shape of the future tensor
    Returns:
        TensorTrain object containing a TT-tensor"""
    shape = np.array(shape)
    _validate_input_parameters(is_tensor=True, shape=shape)
    num_dims = shape.size 
    tt_rank = np.ones(num_dims + 1)

    tt_cores = num_dims * [None]
    for i in range(num_dims):
        curr_core_shape = (1, shape[i], 1)
        tt_cores[i] = torch.ones(curr_core_shape)

    return TensorTrain(tt_cores, shape, tt_rank)


def tensor_zeros(shape):
    r"""Generate a TT-tensor of the given shape with all entries equal to 0.
    Args:
        shape: array representing the shape of the future tensor
    Returns:
        TensorTrain object containing a TT-tensor
    """
    shape = np.array(shape)
    _validate_input_parameters(is_tensor=True, shape=shape)
    num_dims = shape.size 
    tt_rank = np.ones(num_dims + 1)
    tt_cores = num_dims * [None]
    for i in range(num_dims):
        curr_core_shape = (1, shape[i], 1)
        tt_cores[i] = torch.zeros(curr_core_shape)
    
    return TensorTrain(tt_cores, shape, tt_rank)


def eye(shape):
    r"""Creates an identity TT-matrix.
    Args:
        shape: array which defines the shape of the matrix row and column indices.
    Returns:
        TensorTrain containing an identity TT-matrix of size
        np.prod(shape) x np.prod(shape)
    """
    shape = np.array(shape)
    # In this special case shape is in the same format as in the TT-tensor case
    _validate_input_parameters(is_tensor=True, shape=shape)
    num_dims = shape.size
    tt_ranks = np.ones(num_dims + 1)

    tt_cores = num_dims * [None]
    for i in range(num_dims):
        curr_core_shape = (1, shape[i], shape[i], 1)
     #   tt_cores[i] = torch.reshape(torch.eye(shape[i]), curr_core_shape)
        tt_cores[i] = torch.eye(int(shape[i])).reshape(curr_core_shape).type(dtype)
    true_shape = np.vstack([shape, shape])
    return TensorTrain(tt_cores, true_shape, tt_ranks)


def matrix_ones(shape):
    """Generate a TT-matrix of the given shape with each entry equal to 1.
    Args:
        shape: 2d array, shape[0] is the shape of the matrix row-index,
            shape[1] is the shape of the column index.
            shape[0] and shape[1] should have the same number of elements (d)
            Also supports omitting one of the dimensions for vectors, e.g.
                matrix_ones([[2, 2, 2], None])
            and
                matrix_ones([None, [2, 2, 2]])
            will create an 8-element column and row vectors correspondingly.
    Returns:
        TensorTrain containing a TT-matrix of size
            np.prod(shape[0]) x np.prod(shape[1]) with each entry equal to 1
    """
    shape = list(shape)
    # In case shape represents a vector, e.g. [None, [2, 2, 2]]
    if shape[0] is None:
        shape[0] = np.ones(len(shape[1]), dtype=int)
    # In case shape represents a vector, e.g. [[2, 2, 2], None]
    if shape[1] is None:
        shape[1] = np.ones(len(shape[0]), dtype=int)
    shape = np.array(shape)

    _validate_input_parameters(is_tensor=False, shape=shape)
    num_dims = shape[0].size 
    tt_rank = np.ones(shape[0].size + 1)

    tt_cores = [None] * num_dims 
    for i in range(num_dims):
        curr_core_shape = (1, shape[0][i], shape[1][i], 1)
        tt_cores[i] = torch.ones(curr_core_shape)

    return TensorTrain(tt_cores, shape, tt_rank)


def matrix_zeros(shape):
    r"""Generate a TT-matrix of the given shape with each entry equal to 0.
    Args:
        shape: 2d array, shape[0] is the shape of the matrix row-index,
            shape[1] is the shape of the column index.
            shape[0] and shape[1] should have the same number of elements (d)
            Also supports omitting one of the dimensions for vectors, e.g.
                matrix_zeros([[2, 2, 2], None])
            and
                matrix_zeros([None, [2, 2, 2]])
            will create an 8-element column and row vectors correspondingly.
    Returns:
        TensorTrain containing a TT-matrix of size
            np.prod(shape[0]) x np.prod(shape[1]) with each entry equal to 0
    """   
    shape = list(shape)
    # In case shape represents a vector, e.g. [None, [2, 2, 2]]
    if shape[0] is None:
        shape[0] = np.ones(len(shape[1]), dtype=int)
    # In case shape represents a vector, e.g. [[2, 2, 2], None]
    if shape[1] is None:
        shape[1] = np.ones(len(shape[0]), dtype=int)
    shape = np.array(shape)

    _validate_input_parameters(is_tensor=False, shape=shape)
    num_dims = shape[0].size 
    tt_rank = np.ones(shape[0].size + 1)
    
    tt_cores = [None] * num_dims
    for i in range(num_dims):
        curr_core_shape = (1, shape[0][i], shape[1][i], 1)
        tt_cores[i] = torch.zeros(curr_core_shape)

    return TensorTrain(tt_cores, shape, tt_rank)


def tensor_with_random_cores(shape, tt_rank=2, mean=0., stddev=1.):
    r"""Generate a TT-tensor of the given shape with N(mean, stddev^2) cores.
    Args:
        shape: array representing the shape of the future tensor.
        tt_rank: a number or a (d+1)-element array with the desired ranks.
        mean: a number, the mean of the normal distribution used for initializing TT-cores.
        stddev: a number, the standard deviation of the normal distribution used for
                initializing TT-cores. 
    Returns:
        Tensorizing containing a TT-tensor
    """
    # TODO: good distribution to initialize the training.
    # TODO: support the shape and tt_ranks as Torch.tensor.
    # TODO: support None as a dimension.
    shape = np.array(shape)
    tt_rank = np.array(tt_rank)
    _validate_input_parameters(is_tensor=True, shape=shape, tt_rank=tt_rank)
    num_dims = shape.size
    if tt_rank.size == 1:
        tt_rank = tt_rank * np.ones(num_dims - 1)
        tt_rank = np.insert(tt_rank, 0, 1)
        tt_rank = np.append(tt_rank, 1)
    
    tt_rank = tt_rank.astype(int)
    tt_cores = [None] * num_dims
    for i in range(num_dims):
        curr_core_shape = (tt_rank[i], shape[i], tt_rank[i+1])
        tt_cores[i] = torch.randn(curr_core_shape).normal_(mean=mean, std=stddev)

    return TensorTrain(tt_cores, shape, tt_rank)


def matrix_with_random_cores(shape, tt_rank=2, mean=0., stddev=1.):
    r"""Generate a TT-matrix of the given shape with N gaussian cores.
    Args:
        shape: 2d array, shape[0] is the shape of the matrix row-index,
            shape[1] is the shape of teh column index.
            shape[0] and shape[1] should have the same number of elements (d)
            Also supports omitting one of the dimensions of vectors, e.g.
                matrix_with_random_cores([[2, 2, 2], None])
            and 
                matrix_with_random_cores([None, [2, 2, 2]])
            will create an 8-elemnt column and row vectors correspondingly.
        tt_rank: a number or a (d+1)-element array with ranks.
    Returns:
        TensorTrain containing a TT-matrix of the size np.prod(shape[0]) x np.prod(shape[1])
    """
    shape = list(shape)
    # In case shape represents a vector, e.g. [None, [2, 2, 2]]
    if shape[0] is None:
        shape[0] = np.ones(len(shape[1]), dtype=int)
    # In case shape represents a vector, e.g. [[2, 2, 2], None]
    if shape[1] is None:
        shape[1] = np.ones(len(shape[0]), dtype=int)
    shape = np.array(shape)
    tt_rank = np.array(tt_rank)
    _validate_input_parameters(is_tensor=False, shape=shape, tt_rank=tt_rank)

    num_dims = shape[0].size 
    if tt_rank.size == 1:
        tt_rank = tt_rank * np.ones(num_dims - 1)
        tt_rank = np.concatenate([[1], tt_rank, [1]])

    tt_rank = tt_rank.astype(int)
    tt_cores = [None] * num_dims
    for i in range(num_dims):
        curr_core_shape = (tt_rank[i], shape[0][i], shape[1][i], tt_rank[i+1])
        tt_cores[i] = torch.randn(curr_core_shape).normal_(mean=mean, std=stddev)
    
    return TensorTrain(tt_cores, shape, tt_rank)


def ones_like(tt):
    r"""Constructs t3f.ones with the shape of `tt`.
    In the case when `tt` is TensorTrainBatch constructs t3f.ones with the shape
    of a TensorTrain in `tt`.
    Args:
        tt: TensorTrain object
    Returns:
        TensorTrain object of the same shape as `tt` but with all entries equal to 1.
    """
    if not (isinstance(tt, TensorTrain) or isinstance(tt, TensorTrainBatch)):
        raise ValueError("`tt' has to be a Tensor Train object.")
    else:
        shape = tt.get_raw_shape()
        if tt.is_tt_matrix():
            return matrix_ones(shape)
        else:
            return tensor_ones(shape[0])


def zeros_like(tt):
    r"""Constructs t3f.zeros with the shape of `tt`.
    In the case when `tt` is a TensorTrainBatch constructs t3f.zeros with
    the shape of a TensorTrain in `tt`.
    Args:
        tt: TensorTrain object
    Returns:
        TensorTrain object of the same shape as `tt` but with all entries equal to 0.
    """
    if not (isinstance(tt, TensorTrain) or isinstance(tt, TensorTrainBatch)):
        raise ValueError("`tt' has to be a Tensor Train object")
    else:
        shape = tt.get_raw_shape()
        if tt.is_tt_matrix():
            return matrix_zeros(shape)
        else:
            return tensor_zeros(shape[0])


def random_tensor(shape, tt_rank=2, mean=0., stddev=1.):
    r"""Generate a random TT-tensor of the given shape with given mean and stddev.
    Entries of the generated tensor (in the full format) will be iid and satisfy
    E[x_{i1i2..id}] = mean, Var[x_{i1i2..id}] = stddev^2, but the distribution is
    in fact not Gaussian (but is close for large tensors).
    In the current implementation only mean 0 is supported. To get
    a random_tensor with specified mean but tt_rank greater by 1 you can call
        x = t3f.random_tensor(shape, tt_rank, stddev=stddev)
        x = mean * t3f.ones_like(x) + x
    Args:
        shape: array representing the shape of the future tensor.
        tt_rank: a number or a (d+1)-element array with the desired ranks.
        mean: a number, the desired mean for the distribution of entries.
        stddev: a number, the desired standard deviation for the distribution of entries.
    Returns:
        TensorTrain containing a TT-tensor
    """
    shape = np.array(shape)
    tt_rank = np.array(tt_rank)
    _validate_input_parameters(is_tensor=True, shape=shape, tt_rank=tt_rank)

    num_dims = shape.size 
    if tt_rank.size == 1:
        tt_rank = tt_rank * np.ones(num_dims - 1)
        tt_rank = np.insert(tt_rank, 0, 1)
        tt_rank = np.append(tt_rank, 1)
    
    tt_rank = tt_rank.astype(int)
    
    # Empirically entries of a TT tensor with cores initialized from N(0, 1)
    # will have variances np.prod(tt_rank) and mean 0.
    # We scale each TT-core to obtain the desired stddev

    cr_exponent = -1.0 / (2 * num_dims)
    var = np.prod(tt_rank ** cr_exponent)
    core_stddev = stddev ** (1.0 / num_dims) * var
    tt = tensor_with_random_cores(shape, tt_rank=tt_rank, stddev=core_stddev)

    if np.abs(mean) < 1e-8:
        return tt
    else:
        raise NotImplementedError('non-zero mean is not supported yet')

    
def random_matrix(shape, tt_rank=2, mean=0., stddev=1.):
    r"""Generate a random TT-matrix of the given shape with given mean and stddev.
    Entries of the generated matrix (in the full format) will be iid and satisfy
    E[x_{i1i2..id}] = mean, Var[x_{i1i2..id}] = stddev^2, but the distribution is
    in fact not Gaussian.
    In the current implementation only mean 0 is supported. To get
    a random_matrix with specified mean but tt_rank greater by 1 you can call
        x = t3f.random_matrix(shape, tt_rank, stddev=stddev)
        x = mean * t3f.ones_like(x) + x
    Args:
        shape: 2d array, shape[0] is the shape of the matrix row-index,
        shape[1] is the shape of the column index.
        shape[0] and shape[1] should have the same number of elements (d)
        Also supports omitting one of the dimensions for vectors, e.g.
            random_matrix([[2, 2, 2], None])
        and
            random_matrix([None, [2, 2, 2]])
        will create an 8-element column and row vectors correspondingly.
        tt_rank: a number or a (d+1)-element array with ranks.
        mean: a number, the desired mean for the distribution of entries.
        stddev: a number, the desired standard deviation for the distribution of entries.
    Returns:
        TensorTrain containing a TT-matrix of size
        np.prod(shape[0]) x np.prod(shape[1])
    """
    # TODO: good distribution to init training.
    # In case the shape is immutable.
    shape = list(shape)
    # In case shape represents a vector, e.g. [None, [2, 2, 2]]
    if shape[0] is None:
        shape[0] = np.ones(len(shape[1]), dtype=int)
    # In case shape represents a vector, e.g. [[2, 2, 2], None]
    if shape[1] is None:
        shape[1] = np.ones(len(shape[0]), dtype=int)
    shape = np.array(shape)
    tt_rank = np.array(tt_rank)

    _validate_input_parameters(is_tensor=False, shape=shape, tt_rank=tt_rank)

    num_dims = shape[0].size
    if tt_rank.size == 1:
        tt_rank = tt_rank * np.ones(num_dims - 1)
        tt_rank = np.concatenate([[1], tt_rank, [1]])

    tt_rank = tt_rank.astype(int)
    var = np.prod(tt_rank)

    # Empirically entries of a TT tensor with cores initialized from N(0, 1)
    # will have variances np.prod(tt_rank) and mean 0.
    # We scale each TT-core to obtain the desired stddev

    cr_exponent = -1.0 / (2 * num_dims)
    var = np.prod(tt_rank ** cr_exponent)
    core_stddev = stddev ** (1.0 / num_dims) * var
    tt = matrix_with_random_cores(shape, tt_rank=tt_rank, stddev=core_stddev)

    if np.abs(mean) < 1e-8:
        return tt
    else:
        raise NotImplementedError('non-zero mean is not supported yet')


def glorot_initializer(shape, tt_rank=2):
    r"""Constructs a random TT matrix with entrywise variance 2.0 / (n_in + n_out)
    Args:
        shape: 2d array, shape[0] is the shape of the matrix row-index,
        shape[1] is the shape of the column index.
        shape[0] and shape[1] should have the same number of elements (d)
        Also supports omitting one of the dimensions for vectors, e.g.
            glorot_initializer([[2, 2, 2], None])
        and
            glorot_initializer([None, [2, 2, 2]])
        will create an 8-element column and row vectors correspondingly.
        tt_rank: a number or a (d+1)-element array with ranks.
    Returns:
        TensorTrain containing a TT-matrix of size
        np.prod(shape[0]) x np.prod(shape[1])
    """

    # In case the shape is immutable.
    shape = list(shape)
    # In case shape represents a vector, e.g. [None, [2, 2, 2]]
    if shape[0] is None:
        shape[0] = np.ones(len(shape[1]), dtype=int)
    # In case shape represents a vector, e.g. [[2, 2, 2], None]
    if shape[1] is None:
        shape[1] = np.ones(len(shape[0]), dtype=int)
    shape = np.array(shape)
    tt_rank = np.array(tt_rank)
    _validate_input_parameters(is_tensor=False, shape=shape, tt_rank=tt_rank)
    n_in = np.prod(shape[0])
    n_out = np.prod(shape[1])
    lamb = 2.0 / (n_in + n_out)

    return random_matrix(shape, tt_rank=tt_rank, stddev=np.sqrt(lamb))


def he_initializer(shape, tt_rank=2):
    r"""Constructs a random TT matrix with entrywise variance 2.0 / n_in
    Args:
        shape: 2d array, shape[0] is the shape of the matrix row-index,
        shape[1] is the shape of the column index.
        shape[0] and shape[1] should have the same number of elements (d)
        Also supports omitting one of the dimensions for vectors, e.g.
            he_initializer([[2, 2, 2], None])
        and
            he_initializer([None, [2, 2, 2]])
        will create an 8-element column and row vectors correspondingly.
        tt_rank: a number or a (d+1)-element array with ranks.
    Returns:
        TensorTrain containing a TT-matrix of size
        np.prod(shape[0]) x np.prod(shape[1])
    """
    # In case the shape is immutable.
    shape = list(shape)
    # In case shape represents a vector, e.g. [None, [2, 2, 2]]
    if shape[0] is None:
        shape[0] = np.ones(len(shape[1]), dtype=int)
    # In case shape represents a vector, e.g. [[2, 2, 2], None]
    if shape[1] is None:
        shape[1] = np.ones(len(shape[0]), dtype=int)
    shape = np.array(shape)
    tt_rank = np.array(tt_rank)
    _validate_input_parameters(is_tensor=False, shape=shape, tt_rank=tt_rank)
    n_in = np.prod(shape[0])
    lamb = 2.0 / n_in

    return random_matrix(shape, tt_rank=tt_rank, stddev=np.sqrt(lamb))


def lecun_initializer(shape, tt_rank=2):
    r"""Constructs a random TT matrix with entrywise variance 1.0 / n_in
    Args:
        shape: 2d array, shape[0] is the shape of the matrix row-index,
        shape[1] is the shape of the column index.
        shape[0] and shape[1] should have the same number of elements (d)
        Also supports omitting one of the dimensions for vectors, e.g.
            lecun_initializer([[2, 2, 2], None])
        and
            lecun_initializer([None, [2, 2, 2]])
        will create an 8-element column and row vectors correspondingly.
        tt_rank: a number or a (d+1)-element array with ranks.
    Returns:
        TensorTrain containing a TT-matrix of size
        np.prod(shape[0]) x np.prod(shape[1])
    """
    # In case the shape is immutable.
    shape = list(shape)
    # In case shape represents a vector, e.g. [None, [2, 2, 2]]
    if shape[0] is None:
        shape[0] = np.ones(len(shape[1]), dtype=int)
    # In case shape represents a vector, e.g. [[2, 2, 2], None]
    if shape[1] is None:
        shape[1] = np.ones(len(shape[0]), dtype=int)
    shape = np.array(shape)
    tt_rank = np.array(tt_rank)
    _validate_input_parameters(is_tensor=False, shape=shape, tt_rank=tt_rank)
    n_in = np.prod(shape[0])
    lamb = 1.0 / n_in
  
    return random_matrix(shape, tt_rank=tt_rank, stddev=np.sqrt(lamb))


def get_variables(initializer=None):
    if initializer is None:
        raise ValueError('Initializer is not provided.')

    variable_cores = torch.nn.ParameterList()
    num_dims = initializer.ndims
    for i in range(num_dims):
        curr_core_var = Parameter(initializer.tt_cores[i])
        variable_cores.append(curr_core_var)

    return variable_cores 



if __name__=="__main__":

    shape = [[4, 7, 4, 7], [5, 5, 5, 5]]
    tt1 = matrix_with_random_cores(shape, tt_rank=2)
    tt2 = matrix_zeros(shape)

    print(lecun_initializer(shape, tt_rank=3).tt_cores[0])
    print(glorot_initializer(shape, tt_rank=3).tt_cores[0])
    print(he_initializer(shape, tt_rank=3).tt_cores[0])

