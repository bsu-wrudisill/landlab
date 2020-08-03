#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Functions to set up a finite-volume solution matrix for a landlab grid."""

import numpy as np
from scipy.sparse import lil_matrix
from .cfuncs import fill_matrix, fill_matrix_with_coefficients


def matrix_row_at_node(grid):
    """Create and return a node array with corresponding matrix row, or -1 if none.

    Examples
    --------
    >>> from landlab import RasterModelGrid
    >>> grid = RasterModelGrid((4, 5))
    >>> grid.status_at_node[13] = grid.BC_NODE_IS_FIXED_VALUE
    >>> grid.status_at_node[2] = grid.BC_NODE_IS_CLOSED
    >>> matrix_row_at_node(grid)
    array([-1, -1, -1, -1, -1, -1,  0,  1,  2, -1, -1,  3,  4, -1, -1, -1, -1, -1, -1, -1])
    """
    matrix_row_at_node = -np.ones(grid.number_of_nodes, dtype=np.int)
    matrix_row_at_node[grid.core_nodes] = np.arange(
        grid.number_of_core_nodes, dtype=np.int
    )
    return matrix_row_at_node


def make_core_node_matrix(grid, value, sparse=False):
    """
    Construct and return a matrix for the core nodes, plus a right-hand side vector
    containing values based on the input array `value`.

    Examples
    --------
    >>> from landlab import RasterModelGrid
    >>> grid = RasterModelGrid((4, 5))
    >>> grid.status_at_node[13] = grid.BC_NODE_IS_FIXED_VALUE
    >>> grid.status_at_node[2] = grid.BC_NODE_IS_CLOSED
    >>> vals = np.arange(grid.number_of_nodes, dtype=np.double)  # made-up state variable array
    >>> mat, rhs = make_core_node_matrix(grid, vals)
    >>> mat
    array([[-4.,  1.,  0.,  1.,  0.],
       [ 1., -3.,  1.,  0.,  1.],
       [ 0.,  1., -4.,  0.,  0.],
       [ 1.,  0.,  0., -4.,  1.],
       [ 0.,  1.,  0.,  1., -4.]])
    >>> rhs
    array([[ -6.],
           [  0.],
           [-25.],
           [-26.],
           [-30.]])
    >>> mat, rhs = make_core_node_matrix(grid, vals, sparse=True)
    >>> mat.toarray()
    array([[-4.,  1.,  0.,  1.,  0.],
       [ 1., -3.,  1.,  0.,  1.],
       [ 0.,  1., -4.,  0.,  0.],
       [ 1.,  0.,  0., -4.,  1.],
       [ 0.,  1.,  0.,  1., -4.]])
    """
    # Get the various types of active link
    core2core = grid.link_with_node_status(
        status_at_tail=grid.BC_NODE_IS_CORE, status_at_head=grid.BC_NODE_IS_CORE
    )
    fv2core = grid.link_with_node_status(
        status_at_tail=grid.BC_NODE_IS_FIXED_VALUE, status_at_head=grid.BC_NODE_IS_CORE
    )
    core2fv = grid.link_with_node_status(
        status_at_tail=grid.BC_NODE_IS_CORE, status_at_head=grid.BC_NODE_IS_FIXED_VALUE
    )

    # Make the matrix and right-hand side vector
    if sparse:
        mat = lil_matrix((grid.number_of_core_nodes, grid.number_of_core_nodes))
    else:
        mat = np.zeros((grid.number_of_core_nodes, grid.number_of_core_nodes))
    rhs = np.zeros((grid.number_of_core_nodes, 1))

    # Get matrix row indices for each of the nodes
    matrow = matrix_row_at_node(grid)

    mat, rhs = fill_matrix(
        core2core,
        core2fv,
        fv2core,
        grid.node_at_link_tail,
        grid.node_at_link_head,
        matrow,
        value,
        rhs,
        mat,
    )

    if sparse:
        mat = mat.tocsr()  # convert to Compressed Sparse Row format

    return mat, rhs


def make_core_node_matrix_var_coef(grid, value, coef, sparse=False):
    """
    Construct and return a matrix for the core nodes, plus a right-hand side vector
    containing values based on the input array `value`. This version includes a
    coefficient for each link.

    Examples
    --------
    >>> from landlab import RasterModelGrid
    >>> grid = RasterModelGrid((4, 5))
    >>> grid.status_at_node[13] = grid.BC_NODE_IS_FIXED_VALUE
    >>> grid.status_at_node[2] = grid.BC_NODE_IS_CLOSED
    >>> vals = np.arange(grid.number_of_nodes, dtype=np.double)  # made-up state variable array
    >>> coefs = np.ones(grid.number_of_links, dtype=np.double)  # coefficient array
    >>> mat, rhs = make_core_node_matrix_var_coef(grid, vals, coefs)
    >>> mat
    array([[-4.,  1.,  0.,  1.,  0.],
       [ 1., -3.,  1.,  0.,  1.],
       [ 0.,  1., -4.,  0.,  0.],
       [ 1.,  0.,  0., -4.,  1.],
       [ 0.,  1.,  0.,  1., -4.]])
    >>> rhs
    array([[ -6.],
           [  0.],
           [-25.],
           [-26.],
           [-30.]])
    >>> mat, rhs = make_core_node_matrix_var_coef(grid, vals, coefs, sparse=True)
    >>> mat.toarray()
    array([[-4.,  1.,  0.,  1.,  0.],
       [ 1., -3.,  1.,  0.,  1.],
       [ 0.,  1., -4.,  0.,  0.],
       [ 1.,  0.,  0., -4.,  1.],
       [ 0.,  1.,  0.,  1., -4.]])
    """

    # Get the various types of active link
    core2core = grid.link_with_node_status(
        status_at_tail=grid.BC_NODE_IS_CORE, status_at_head=grid.BC_NODE_IS_CORE
    )
    fv2core = grid.link_with_node_status(
        status_at_tail=grid.BC_NODE_IS_FIXED_VALUE, status_at_head=grid.BC_NODE_IS_CORE
    )
    core2fv = grid.link_with_node_status(
        status_at_tail=grid.BC_NODE_IS_CORE, status_at_head=grid.BC_NODE_IS_FIXED_VALUE
    )

    # Make the matrix and right-hand side vector
    if sparse:
        mat = lil_matrix((grid.number_of_core_nodes, grid.number_of_core_nodes))
    else:
        mat = np.zeros((grid.number_of_core_nodes, grid.number_of_core_nodes))
    rhs = np.zeros((grid.number_of_core_nodes, 1))

    # Get matrix row indices for each of the nodes
    matrow = matrix_row_at_node(grid)

    mat, rhs = fill_matrix_with_coefficients(
        core2core,
        core2fv,
        fv2core,
        grid.node_at_link_tail,
        grid.node_at_link_head,
        matrow,
        value,
        rhs,
        coef,
        mat,
    )

    if sparse:
        mat = mat.tocsr()  # convert to Compressed Sparse Row format

    return mat, rhs