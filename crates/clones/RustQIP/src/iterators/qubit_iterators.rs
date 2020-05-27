extern crate num;

use std::marker::PhantomData;

use num::complex::Complex;

use self::num::One;
use crate::types::Precision;
use crate::utils::*;

/// Iterator which provides the indices of nonzero columns for a given row of a matrix
#[derive(Debug)]
pub struct MatrixOpIterator<'a, P: Precision> {
    n: u64,
    data: &'a [Complex<P>],
    last_col: Option<u64>,
}

impl<'a, P: Precision> MatrixOpIterator<'a, P> {
    /// Build a new iterator using the row index, the number of qubits in the matrix, and the
    /// complex values of the matrix.
    pub fn new(row: u64, n: u64, data: &'a [Complex<P>]) -> MatrixOpIterator<P> {
        let lower = get_flat_index(n, row, 0) as usize;
        let upper = get_flat_index(n, row, 1 << n) as usize;
        MatrixOpIterator {
            n,
            data: &data[lower..upper],
            last_col: None,
        }
    }
}

impl<'a, P: Precision> Iterator for MatrixOpIterator<'a, P> {
    type Item = (u64, Complex<P>);

    fn next(&mut self) -> Option<Self::Item> {
        let pos = if let Some(last_col) = self.last_col {
            last_col + 1
        } else {
            0
        };
        self.last_col = None;
        for col in pos..(1 << self.n) {
            let val = self.data[col as usize];
            if val != Complex::default() {
                self.last_col = Some(col);
                return Some((col, val));
            }
        }
        None
    }
}

/// Iterator which provides the indices of nonzero columns for a given row of a sparse matrix
#[derive(Debug)]
pub struct SparseMatrixOpIterator<'a, P: Precision> {
    data: &'a [(u64, Complex<P>)],
    last_index: Option<u64>,
}

impl<'a, P: Precision> SparseMatrixOpIterator<'a, P> {
    /// Build a new iterator using the row index, and the sparse matrix data.
    pub fn new(row: u64, data: &'a [Vec<(u64, Complex<P>)>]) -> SparseMatrixOpIterator<P> {
        SparseMatrixOpIterator {
            data: &data[row as usize],
            last_index: None,
        }
    }
}

impl<'a, P: Precision> Iterator for SparseMatrixOpIterator<'a, P> {
    type Item = (u64, Complex<P>);

    fn next(&mut self) -> Option<Self::Item> {
        let pos = if let Some(last_index) = self.last_index {
            last_index + 1
        } else {
            0
        };

        if pos as usize >= self.data.len() {
            self.last_index = None;
            None
        } else {
            self.last_index = Some(pos);
            Some(self.data[pos as usize])
        }
    }
}

/// Iterator which provides the indices of nonzero columns for a given row of a COp
#[derive(Debug)]
pub struct ControlledOpIterator<P: Precision, It: Iterator<Item = (u64, Complex<P>)>> {
    row: u64,
    index_threshold: u64,
    op_iter: Option<It>,
    last_col: Option<u64>,
}

impl<P: Precision, It: Iterator<Item = (u64, Complex<P>)>> ControlledOpIterator<P, It> {
    /// Build a new iterator using the row index, the number of controlling indices, the number of
    /// op indices, and the iterator for the op.
    pub fn new<F: FnOnce(u64) -> It>(
        row: u64,
        n_control_indices: u64,
        n_op_indices: u64,
        iter_builder: F,
    ) -> ControlledOpIterator<P, It> {
        let n_indices = n_control_indices + n_op_indices;
        let index_threshold = (1 << n_indices) - (1 << n_op_indices);
        let op_iter = if row >= index_threshold {
            Some(iter_builder(row - index_threshold))
        } else {
            None
        };
        ControlledOpIterator {
            row,
            index_threshold,
            op_iter,
            last_col: None,
        }
    }
}

impl<P: Precision, It: Iterator<Item = (u64, Complex<P>)>> Iterator
    for ControlledOpIterator<P, It>
{
    type Item = (u64, Complex<P>);

    fn next(&mut self) -> Option<Self::Item> {
        if let Some(it) = &mut self.op_iter {
            let cval = it.next();
            let ret_val = cval.map(|(i, val)| (i + self.index_threshold, val));
            self.last_col = ret_val.map(|(i, _)| i);
            ret_val
        } else {
            if let Some(last_col) = self.last_col {
                if last_col < self.row {
                    self.last_col = Some(self.row);
                } else {
                    self.last_col = None;
                }
            } else {
                self.last_col = Some(self.row);
            }
            self.last_col.map(|c| (c, Complex::<P>::one()))
        }
    }
}

/// Iterator which provides the indices of nonzero columns for a given row of a SwapOp
#[derive(Debug)]
pub struct SwapOpIterator<P: Precision> {
    row: u64,
    half_n: u64,
    last_col: Option<u64>,
    phantom: PhantomData<P>,
}

impl<P: Precision> SwapOpIterator<P> {
    /// Build a new iterator using the row index, and the total number of qubits being swapped
    /// (should be a multiple of 2).
    pub fn new(row: u64, n_qubits: u64) -> SwapOpIterator<P> {
        SwapOpIterator {
            row,
            half_n: n_qubits >> 1,
            last_col: None,
            phantom: PhantomData,
        }
    }
}

impl<P: Precision> Iterator for SwapOpIterator<P> {
    type Item = (u64, Complex<P>);

    fn next(&mut self) -> Option<Self::Item> {
        if self.last_col.is_none() {
            let lower_mask: u64 = !(std::u64::MAX << self.half_n);
            let lower = self.row & lower_mask;
            let upper = self.row >> self.half_n;
            self.last_col = Some((lower << self.half_n) + upper);
        } else {
            self.last_col = None;
        }
        self.last_col.map(|col| (col, Complex::<P>::one()))
    }
}

/// Iterator which provides the indices of nonzero columns for a given function.
#[derive(Debug)]
pub struct FunctionOpIterator<P: Precision> {
    output_n: u64,
    x: u64,
    fx_xor_y: u64,
    theta: P,
    last_col: Option<u64>,
    phantom: PhantomData<P>,
}

impl<P: Precision> FunctionOpIterator<P> {
    /// Build a new iterator using the row index, the number of qubits in the input register, the
    /// number in the output register, and a function which maps rows to a column and a phase.
    pub fn new<F: Fn(u64) -> (u64, f64)>(
        row: u64,
        input_n: u64,
        output_n: u64,
        f: F,
    ) -> FunctionOpIterator<P> {
        let x = row >> output_n;
        let (fx, theta) = f(flip_bits(input_n as usize, x));
        let y = row & ((1 << output_n) - 1);
        let fx_xor_y = y ^ flip_bits(output_n as usize, fx);
        let theta = P::from(theta).unwrap();
        FunctionOpIterator {
            output_n,
            x,
            fx_xor_y,
            theta,
            last_col: None,
            phantom: PhantomData,
        }
    }
}

impl<P: Precision> Iterator for FunctionOpIterator<P> {
    type Item = (u64, Complex<P>);

    fn next(&mut self) -> Option<Self::Item> {
        if self.last_col.is_some() {
            self.last_col = None;
        } else {
            let colbits = (self.x << self.output_n) | self.fx_xor_y;
            self.last_col = Some(colbits);
        };
        self.last_col
            .map(|col| (col, Complex::from_polar(&P::one(), &self.theta)))
    }
}

#[cfg(test)]
mod iterator_tests {
    use crate::state_ops::from_reals;

    use super::num::One;
    use super::*;

    #[test]
    fn test_mat_iterator() {
        let n = 1u64;
        let mat: Vec<Vec<f64>> = (0..1 << n)
            .map(|i| -> Vec<f64> {
                let d = from_reals(&vec![0.0, 1.0, 1.0, 0.0]);
                let it = MatrixOpIterator::new(i, n, &d);
                let v: Vec<f64> = (0..1 << n).map(|_| 0.0).collect();
                it.fold(v, |mut v, (indx, _)| {
                    v[indx as usize] = 1.0;
                    v
                })
            })
            .collect();

        let expected = vec![vec![0.0, 1.0], vec![1.0, 0.0]];

        assert_eq!(mat, expected);
    }

    #[test]
    fn test_sparse_mat_iterator() {
        let n = 1u64;
        let one = Complex::<f64>::one();
        let mat: Vec<Vec<f64>> = (0..1 << n)
            .map(|i| -> Vec<f64> {
                let d = vec![vec![(1, one)], vec![(0, one)]];
                let it = SparseMatrixOpIterator::new(i, &d);
                let v: Vec<f64> = (0..1 << n).map(|_| 0.0).collect();
                it.fold(v, |mut v, (indx, _)| {
                    v[indx as usize] = 1.0;
                    v
                })
            })
            .collect();

        let expected = vec![vec![0.0, 1.0], vec![1.0, 0.0]];

        assert_eq!(mat, expected);
    }

    #[test]
    fn test_swap_iterator() {
        let n = 2u64;
        let mat: Vec<Vec<f64>> = (0..1 << n)
            .map(|i| -> Vec<f64> {
                let it = SwapOpIterator::<f64>::new(i, n);
                let v: Vec<f64> = (0..1 << n).map(|_| 0.0).collect();
                it.fold(v, |mut v, (indx, _)| {
                    v[indx as usize] = 1.0;
                    v
                })
            })
            .collect();

        let expected = vec![
            vec![1.0, 0.0, 0.0, 0.0],
            vec![0.0, 0.0, 1.0, 0.0],
            vec![0.0, 1.0, 0.0, 0.0],
            vec![0.0, 0.0, 0.0, 1.0],
        ];

        assert_eq!(mat, expected);
    }

    #[test]
    fn test_c_iterator() {
        let n = 2u64;

        let d = from_reals(&vec![0.0, 1.0, 1.0, 0.0]);
        let builder = |r: u64| MatrixOpIterator::new(r, n >> 1, &d);

        let mat: Vec<Vec<f64>> = (0..1 << n)
            .map(|i| -> Vec<f64> {
                let it = ControlledOpIterator::new(i, n >> 1, n >> 1, builder);
                let v: Vec<f64> = (0..1 << n).map(|_| 0.0).collect();
                it.fold(v, |mut v, (indx, _)| {
                    v[indx as usize] = 1.0;
                    v
                })
            })
            .collect();

        let expected = vec![
            vec![1.0, 0.0, 0.0, 0.0],
            vec![0.0, 1.0, 0.0, 0.0],
            vec![0.0, 0.0, 0.0, 1.0],
            vec![0.0, 0.0, 1.0, 0.0],
        ];
        assert_eq!(mat, expected);
    }

    #[test]
    fn test_f_iterator() {
        let n = 2u64;
        let mat: Vec<Vec<f64>> = (0..1 << n)
            .map(|i| -> Vec<f64> {
                let it =
                    FunctionOpIterator::<f64>::new(i, n >> 1, n >> 1, |x| ((x != 1) as u64, 0.0));
                let v: Vec<f64> = (0..1 << n).map(|_| 0.0).collect();
                it.fold(v, |mut v, (indx, _)| {
                    v[indx as usize] = 1.0;
                    v
                })
            })
            .collect();

        let expected = vec![
            vec![0.0, 1.0, 0.0, 0.0],
            vec![1.0, 0.0, 0.0, 0.0],
            vec![0.0, 0.0, 1.0, 0.0],
            vec![0.0, 0.0, 0.0, 1.0],
        ];

        assert_eq!(mat, expected);
    }
}
