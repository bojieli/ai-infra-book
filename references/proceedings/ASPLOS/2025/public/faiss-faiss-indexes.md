# Summary of methods

The basic indexes are given hereafter:

| Method                                     | Class name      | `index_factory` | Main parameters | Bytes/vector | Exhaustive | Comments |
|--------------------------------------------|-----------------|-----------------|-----------------|--------------|------------|----------|
| Exact Search for L2                        | `IndexFlatL2`   | `"Flat"`        | `d`             | `4*d`             | yes | brute-force |
| Exact Search for Inner Product             | `IndexFlatIP`   | `"Flat"`        | `d`        | `4*d`             | yes | also for cosine (normalize vectors beforehand) |
| Hierarchical Navigable Small World graph exploration | `IndexHNSWFlat` | `"HNSW,Flat"` | `d`, `M` | `4*d + x * M * 2 * 4`  | no | 
| Inverted file with exact post-verification | `IndexIVFFlat`  | `"IVFx,Flat"`   |`quantizer`, `d`, `nlists`, `metric`| `4*d  + 8` | no | Takes another index to assign vectors to inverted lists. The 8 additional bytes are the vector id that needs to be stored. |
| Locality-Sensitive Hashing (binary flat index) | `IndexLSH`  | -               |`d`, `nbits` | `ceil(nbits/8)` | yes | optimized by using random rotation instead of random projections |
| Scalar quantizer (SQ) in flat mode          | `IndexScalarQuantizer` | `"SQ8"`   | `d`              | `d`              |  yes | 4 and 6 bits per component are also implemented.
| Product quantizer (PQ) in flat mode         | `IndexPQ`       | `"PQx"`, `"PQ"M"x"nbits`          |`d`, `M`, `nbits` | `ceil(M * nbits / 8)`  | yes |
| IVF and scalar quantizer | `IndexIVFScalarQuantizer` | "IVFx,SQ4" "IVFx,SQ8" | `quantizer`, `d`, `nlists`, `qtype` | SQfp16: 2 * `d` + 8, SQ8: `d` + 8 or SQ4: `d/2` + 8 | no | Same as the `IndexScalarQuantizer` |
| IVFADC (coarse quantizer+PQ on residuals)  | `IndexIVFPQ` | `"IVFx,PQ"y"x"nbits`         | `quantizer`, `d`, `nlists`, `M`, `nbits` |  `ceil(M * nbits/8)+8` | no | 
| IVFADC+R (same as IVFADC with re-ranking based on codes) |`IndexIVFPQR` | `"IVFx,PQy+z"`         | `quantizer`, `d`, `nlists`, `M`, `nbits`, `M_refine`, `nbits_refine` | `M+M_refine+8`  | no |

The index can be constructed explicitly with the class constructor, or by using `index_factory`.

## Flat indexes

Flat indexes just encode the vectors into codes of a fixed size and store them in an array of `ntotal * code_size` bytes. 

At search time, all the indexed vectors are decoded sequentially and compared to the query vectors. 
For the `IndexPQ` the comparison is done in the compressed domain, which is faster.

### Supported operations

Flat indexes are similar to C++ vectors. 
They do not store vector ids, since in many cases sequential numbering is enough. 
Therefore: 

- they don't support `add_with_id` (but they can be wrapped in an `IndexIDMap` to add that functionality).

- they do support efficient direct vector access (with `reconstruct` and `reconstruct_n`)

- they support removal with `remove`. Note that this shrinks the index and changes the numbering.

### Vectors encodings

The available encodings are (from least to strongest compression): 

- no encoding at all (`IndexFlat`): the vectors are stored without compression;
- 16-bit float encoding (`IndexScalarQuantizer` with `QT_fp16`): the vectors are compressed to 16-bit floats, which may cause some loss of precision;
- 8/6/4-bit integer encoding (`IndexScalarQuantizer` with `QT_8bit`/`QT_6bit`/`QT_4bit`): vectors quantized to 256/64/16 levels;
- PQ encoding (`IndexPQ`): vectors are split into sub-vectors that are each quantized to a few bits (usually 8). See the example below.
- Residual encodings (`IndexResidual`): vectors are quantized and progressively refined by residual. At each quantization stage, the size of the codebook can be refined.

## Cell-probe methods (`IndexIVF*` indexes) 

A typical way to speed-up the process at the cost of loosing the guarantee to find the nearest neighbor is to employ a partitioning technique such as k-means. The corresponding algorithms are sometimes referred to as _cell-probe methods_.

We use a partition-based method based on Multi-probing.

- The feature space is partitioned into `nlist` cells.
- The database vectors are assigned to one of these cells thanks using a quantization function (in the case of k-means, the assignment to the centroid closest to the query), and stored in an inverted file structure formed of `nlist` inverted lists.
- At query time, a set of `nprobe` inverted lists is selected
- The query is compared to each of the database vector assigned to these lists.

Doing so, only a fraction of the database is compared to the query: as a first approximation, this fraction is `nprobe/nlist`, but this approximation is usually under-estimated because the inverted lists have not equal lengths.
The failure case appears when the cell of the nearest neighbor of a given query is not selected.

The constructor takes an index as a parameter (the `quantizer` or coarse quantizer), which is used to do the assignment to the inverted lists. The query is searched in this index, and the returned vector id(s) are the inverted list(s) that should be visited.

### Cell probe method with a flat index as coarse quantizer

Typically, one would use a Flat index as coarse quantizer. The train method of the IndexIVF adds the centroids to the flat index. The `nprobe` is specified at query time (useful for measuring trade-offs between speed and accuracy).

**NOTE:** As a rule of thumb, denoting by `n` the number of points to be indexed, a typical way to select the number of centroids is to aim at balancing the cost of the assignment to the centroids (`nlist * d` for a plain k-means) with the number of distance computations performed when parsing the inverted lists (in the order of `nprobe / nlist * n * C`, where the constant accounts for the uneven distribution of the list and the fact that a single vector comparison is done more efficiently when done by batch with centroids, say C=10 to give an idea). This leads to a number of centroids of the form `nlist = C * sqrt (n)`.

### Other types of coarse quantizers

In some contexts it is beneficial to use other types of quantizers, for example a GPU based quantizer, a `MultiIndexQuantizer`, a `ResidualCoarseQuantizer` (see "Indexes based on a residual quantizer" section below) or ` a HNSW based quantizer. 

### Encoding of vectors in an `IndexIVF`

The elements of inverted lists are encoded vectors (+ the corresponding vector id). 
The encoding is mainly to make the vectors more compact.
Those elements are just scanned sequentially, and the search function returns the top-k smallest distances seen so far.

The supported codes are the same as for the Flat index, just convert the name of the index class by inserting `IVF`: `IndexFlat` becomes `IndexIVFFlat`.

## `IndexHNSW` variants

The Hierarchical Navigable Small World indexing method is based on a graph built on the indexed vectors. 
At search time, the graph is explored in a way that converges to the nearest neighbors as quickly as possible. 
The `IndexHNSW` uses a flat index as underlying storage to quickly access the database vectors and abstract the compression / decompression of vectors. 
HNSW depends on a few important parameters: 

- `M` is the number of neighbors used in the graph. A larger M is more accurate but uses more memory

- `efConstruction` is the depth of exploration at add time

- `efSearch` is the depth of exploration of the search 

### Supported encodings

`IndexHNSW` supports the following Flat indexes: `IndexHNSWFlat` (no encoding), `IndexHNSWSQ` (scalar quantizer), `IndexHNSWPQ` (product quantizer), `IndexHNSW2Level` (two-level encoding).

### Supported operations

In addition to the restrictions of the Flat index HNSW uses, HNSW does not support removing vectors from the index. 
This would destroy the graph structure. 

## `IndexLSH` and its relationship with cell-probe methods 

The most popular cell-probe method is probably the original Locality Sensitive Hashing method referred to as  [E2LSH] (http://www.mit.edu/~andoni/LSH/). However this method and its derivatives suffer from two drawbacks:

- They require a lot of hash functions (=partitions) to achieve acceptable results, leading to a lot of extra memory. Memory is not cheap.
- The hash function are not adapted to the input data. This is good for proofs but leads to suboptimal choice results in practice.

### Binary LSH codes

In Faiss, the `IndexLSH` is just a Flat index with binary codes. 
The database vectors and query vectors are hashed into binary codes that are compared with Hamming distances. 

In C++, a LSH index (binary vector mode, See Charikar STOC'2002) is declared as follows:

```c++
  IndexLSH * index = new faiss::IndexLSH (d, nbits);
```

where `d` is the input vector dimensionality and `nbits` the number of bits use per stored vector.


In Python, the (improved) LSH index is constructed and search as follows

```python
n_bits = 2 * d
lsh = faiss.IndexLSH (d, n_bits)
lsh.train (x_train)
lsh.add (x_base)
D, I = lsh.search (x_query, k)
```

**NOTE:** The algorithm is **not** vanilla-LSH, but a better choice. Instead of set of orthogonal projectors is used if n_bits <= d, or a tight frame if n_bits > d.


## Indexes based on Product Quantization codes 

In C++, the indexes based on product quantization are identified by the keyword PQ. For instance, the most common indexes based on product quantization are declared as follows:

<details><summary>C++ PQ example</summary>

```c++
  #include <faiss/IndexPQ.h>
  #include <faiss/IndexIVFPQ.h>

  // Define a product quantizer for vectors of dimensionality d=128,
  // with 8 bits per subquantizer and M=16 distinct subquantizer
  size_t d = 128;
  int M = 16;
  int nbits = 8;
  faiss:IndexPQ * index_pq = new faiss::IndexPQ (d, M, nbits);

  // Define an index using both PQ and an inverted file with nlists to avoid exhaustive search
  // The index 'quantizer' must be already declared
  faiss::IndexIVFPQ * ivfpq = new faiss::IndexIVFPQ (quantizer, d, nlists, M, nbits);

  // Same but with another level of refinement
  faiss::IndexIVFPQR * ivfpqr = new faiss::IndexIVFPQR (quantizer, d, nclust, M, nbits, M_refine, nbits);
```

</details>

In Python, a product quantizer is defined by:

<details><summary>Python PQ example</summary>

```python
m = 16                                   # number of subquantizers
n_bits = 8                               # bits allocated per subquantizer
pq = faiss.IndexPQ (d, m, n_bits)        # Create the index
pq.train (x_train)                       # Training
pq.add (x_base)                          # Populate the index
D, I = pq.search (x_query, k)            # Perform a search
```
</details>

The number of bits `n_bits` must be equal to 8, 12 or 16. The dimension `d` should be a multiple of `m`

### Inverted file with PQ refinement

The `IndexIVFPQ` is probably the most useful indexing structure for large-scale search. It is used like

```python
coarse_quantizer = faiss.IndexFlatL2 (d)
index = faiss.IndexIVFPQ (coarse_quantizer, d,
                          ncentroids, code_size, 8)
index.nprobe = 5
```

See the chapter about `IndexIVFFlat` for the setting of `ncentroids`. The `code_size` is typically a power of two between 4 and 64. Like for `IndexPQ`, `d` should be a multiple of `m`.

## Indexes based on a residual quantizer

The [`ResidualQuantizer` object](https://github.com/facebookresearch/faiss/blob/master/faiss/impl/ResidualQuantizer.h#L25) encodes a vector using a vector quantizer that progressively refines the residuals of the previous quantization. 
A greedy version of this produces sub-optimal vectors, and computing the codes of all possible centroids is too expensive. 
Therefore, as a tradeoff, the residual quantization is implemented with a beam search. 
The beam size is set via the `max_beam_size` field of the ResidualQuantizer object: the larger the slower and the more accurate.

The ResidualQuantizer object takes in its constructor the number of bits of each quantizer step. 
For example [16, 8, 8] means that there is one 16-bit quantizer (65536 centroids) followed by two 8-bit quantizers.

Example usage can be found in the tests [test_residual_quantizer.py](https://github.com/facebookresearch/faiss/blob/master/tests/test_residual_quantizer.py)

The `ResidualQuantizer` object is used in two types of indexes:

- the `IndexResidual` index is a straightforward use of it to encode vectors. It can also be used as a codec.

- the `ResidualCoarseQuantizer` can be used as a coarse quantizer for an `IndexIVF`. 