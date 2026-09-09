/* Copyright 2024 The Shardy Authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
==============================================================================*/

#include <algorithm>
#include <cassert>
#include <cstdint>
#include <functional>
#include <iterator>
#include <list>
#include <memory>  // IWYU pragma: keep
#include <numeric>
#include <optional>
#include <utility>

#include "llvm/ADT/ArrayRef.h"
#include "llvm/ADT/DenseMap.h"
#include "llvm/ADT/DenseSet.h"
#include "llvm/ADT/STLExtras.h"
#include "llvm/ADT/SmallVector.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"  // IWYU pragma: keep
#include "mlir/IR/Attributes.h"
#include "mlir/IR/BuiltinAttributes.h"
#include "mlir/IR/Diagnostics.h"
#include "mlir/IR/MLIRContext.h"
#include "mlir/IR/PatternMatch.h"
#include "mlir/Pass/Pass.h"  // IWYU pragma: keep
#include "mlir/Rewrite/FrozenRewritePatternSet.h"
#include "mlir/Support/LLVM.h"
#include "mlir/Support/LogicalResult.h"
#include "mlir/Transforms/DialectConversion.h"
#include "shardy/dialect/sdy/ir/dialect.h"
#include "shardy/dialect/sdy/ir/utils.h"
#include "shardy/dialect/sdy/transforms/export/passes.h"  // IWYU pragma: keep
#include "shardy/dialect/sdy/transforms/export/utils.h"
#include "shardy/dialect/sdy/transforms/propagation/utils.h"

namespace mlir {
namespace sdy {

#define GEN_PASS_DEF_RESHARDTOCOLLECTIVESPASS
#include "shardy/dialect/sdy/transforms/export/passes.h.inc"

namespace {

using AxesPerDim = SmallVector<SmallVector<AxisRefAttr>>;

using AxisSet = llvm::SmallDenseSet<AxisRefAttr>;

struct DimAndIndex {
  int64_t dim;
  int64_t index;

  DimAndIndex(int64_t dim, int64_t index) : dim(dim), index(index) {}
};

using AxisToDimAndIndex = llvm::SmallDenseMap<AxisRefAttr, DimAndIndex>;

// Returns a set containing all axes in `axesPerDim`.
AxisSet getAxisSet(ArrayRef<AxisList> axesPerDim) {
  AxisSet result;
  for (const AxisList& axes : axesPerDim) {
    result.insert(axes.begin(), axes.end());
  }
  return result;
}

// Returns a map from `AxisRefAttr` to the dimension in `axesPerDim` in which
// this axis appears and the index within the respective `AxisList`.
AxisToDimAndIndex getAxisToDimAndIndex(ArrayRef<AxisList> axesPerDim) {
  AxisToDimAndIndex result;
  for (auto [dim, axes] : llvm::enumerate(axesPerDim)) {
    for (auto [index, axis] : llvm::enumerate(axes)) {
      result.try_emplace(axis, dim, index);
    }
  }
  return result;
}

AxisList concatAxisLists(MutableArrayRef<AxisList> axisLists) {
  AxisList result;
  for (AxisList& axes : axisLists) {
    result.splice(result.end(), axes);
  }
  return result;
}

// Remove the common prefix of `inAxesPerDim` and `outAxesPerDim`.
void removeCommonPrefix(SmallVector<AxisList>& inAxesPerDim,
                        SmallVector<AxisList>& outAxesPerDim) {
  for (auto [inAxes, outAxes] : llvm::zip_equal(inAxesPerDim, outAxesPerDim)) {
    while (!inAxes.empty() && !outAxes.empty() &&
           inAxes.front() == outAxes.front()) {
      inAxes.pop_front();
      outAxes.pop_front();
    }
  }
}

// Removes the axes in `axesToPop` from the back of `currentAxes`.
//
// Note that `axesToPop` can have decomposed sub-axes of an axis in
// `currentAxes`, which is taken into account.
void popBackFromCurrentAxes(SmallVector<AxisRefAttr>& currentAxes,
                            const AxisList& axesToPop,
                            AxisList::iterator startIt) {
  for (auto it = axesToPop.rbegin(); it != std::make_reverse_iterator(startIt);
       ++it) {
    if (auto prefix = currentAxes.back().getPrefixWithoutOverlap(*it)) {
      currentAxes.back() = *prefix;
    } else {
      currentAxes.pop_back();
    }
  }
}

// Returns the product of axis sizes in `axes`.
template <class AxisContainer>
int64_t getShardedSize(const AxisContainer& axes, MeshAttr mesh) {
  return std::accumulate(
      axes.begin(), axes.end(), 1,
      [&](int64_t cur, AxisRefAttr axis) { return cur * axis.getSize(mesh); });
}

// Returns true if `a` is divisible by `b` or vice versa.
bool areDivisible(int64_t a, int64_t b) { return a % b == 0 || b % a == 0; }

// Returns true if the size of `a` is divisible by the size of `b` or vice
// versa.
bool areSizesDivisible(AxisRefAttr a, AxisRefAttr b, MeshAttr mesh) {
  return areDivisible(a.getSize(mesh), b.getSize(mesh));
}

// When an `AxisRefAttr` needs to fit in a given capacity, we may need to split
// it into two sub-axes, one that fits (`withinAxis`) and another that doesn't
// (`remainderAxis`).
struct AxisWithinCapacity {
  OptionalAxisRef withinAxis;
  OptionalAxisRef remainderAxis;
};

// Returns an `AxisWithinCapacity` for the given `axis` w.r.t. to the given
// `capacity`.
//
// In addition, updates `capacity` by dividing it by the size of the axis that
// fits.
AxisWithinCapacity getAxisWithinCapacity(AxisRefAttr axis, int64_t& capacity,
                                         MeshAttr mesh) {
  int64_t axisSize = axis.getSize(mesh);
  // We could use `std::gcd(axisSize, capacity)` instead, but in practice this
  // isn't needed because how all-slice insertion works for non-divisible case.
  if (capacity <= 1 || !areDivisible(axisSize, capacity)) {
    return {};
  }
  if (capacity >= axisSize) {
    capacity /= axisSize;
    return {axis, /*remainderAxis=*/std::nullopt};
  }

  auto withinAxis = AxisRefAttr::get(mesh.getContext(), axis.getName(),
                                     axis.getSubAxisPreSize(), capacity);
  auto remainderAxis = AxisRefAttr::get(
      mesh.getContext(), axis.getName(),
      withinAxis.getNextPreSizeOrFullSize(mesh), axisSize / capacity);
  capacity = 1;
  return {withinAxis, remainderAxis};
}

// Holds the axes and target dimension of an all-to-all.
struct AllToAllInfo {
  SmallVector<AxisRefAttr> axes;
  int64_t tgtDim;

  explicit AllToAllInfo(int64_t tgtDim) : tgtDim(tgtDim) {}
};

// A class that applies an algorithm to transform an input sharding into an
// output sharding via a sequence of collectives.
//
// The current sharding is initialized with the input sharding, and after each
// collective insertion, the current sharding is updated w.r.t. the collective,
// until it matches the output sharding and we are done.
//
// We define the current state of the transformation as follows:
//
// - `inAxesPerDim` - the axes in the current sharding per dimension, such that
//   the common prefix with the output sharding is removed.
// - `outAxesPerDim` - the axes in the output sharding per dimension, such that
//   the common prefix with the current sharding is removed.
// - `currentAxesPerDim` - the axes in the current sharding, including the
//   common prefix with the output sharding.
//
// These invariants are maintained throughout the algorithm, and specifically
// after each collective insertion.
//
// We also maintain the following two data structures for convenience:
//
// - `inAxisSet` - set containing all axes in `inAxesPerDim`. Updated when in
//   axes are added or removed.
// - `outAxisToDimAndIndex` - map to the dimension in `outAxesPerDim` in which
//   this axis appears and the index within the respective `AxisList`, i.e., if
//   `A = outAxesPerDim[d][i]`, then `outAxisToDimAndIndex[A] == {d, i}`.
//   Updated only when an out axis is split into two sub-axes.
//
// Note that `inAxesPerDim` and `outAxesPerDim` represent the *diff* between the
// current and output sharding, i.e., when they are empty the shardings match
// exactly. The algorithm inserts collectives and updates the current state
// accordingly, until both `inAxesPerDim` and `outAxesPerDim` are empty.
class CollectiveInserter {
 public:
  CollectiveInserter(TensorShardingAttr inSharding,
                     TensorShardingAttr outSharding, Value result,
                     ConversionPatternRewriter& rewriter, Operation* op)
      : rewriter(rewriter),
        loc(op->getLoc()),
        result(result),
        mesh(inSharding.getMesh(op)),
        curMeshOrRef(inSharding.getMeshOrRef()),
        outMeshOrRef(outSharding.getMeshOrRef()),
        unreducedAxes(outSharding.getUnreducedAxes()),
        inAxesPerDim(getAxesPerDim<AxisList>(inSharding)),
        outAxesPerDim(getAxesPerDim<AxisList>(outSharding)),
        currentAxesPerDim(getAxesPerDim<SmallVector<AxisRefAttr>>(inSharding)),
        capacityPerDim(inSharding.getRank(), 1),
        collectiveAxesPerDim(inSharding.getRank()) {
    // Unreduced axes in the input and output sharding must match, given we
    // insert an all-reduce if an unreduced axis becomes replicated/sharded, and
    // never insert a reshard that goes from replicated/sharded to unreduced.
    assert(inSharding.getUnreducedAxes() == outSharding.getUnreducedAxes());

    // We align sub-axes between the input and output axes, so that we can treat
    // sub-axes like full axes and assume any two sub-axes that overlap are also
    // equal, which allows using them as keys in a hash map.
    alignSubAxesByDecomposition(inAxesPerDim, outAxesPerDim, mesh);
    // We remove the common prefix of `inAxesPerDim` and `outAxesPerDim`, since
    // those axes stay exactly the same during the reshard. We are left with
    // `inAxesPerDim` and `outAxesPerDim` that need to become empty, via a
    // sequence of collectives.
    removeCommonPrefix(inAxesPerDim, outAxesPerDim);

    inAxisSet = getAxisSet(inAxesPerDim);
    outAxisToDimAndIndex = getAxisToDimAndIndex(outAxesPerDim);
  }

  // Inserts a sequence of collectives to transform the input sharding into the
  // output sharding, and returns the result of the final collective.
  //
  // If the input and output sharding are the same, returns the input value
  // without inserting any collective.
  Value insert() {
    // In the common case where all axes are a power of 2, in which case a
    // bigger axis is always divisible by a smaller axis, we are guaranteed to
    // be done after trying all-slice -> collective-permute -> all-to-alls ->
    // all-gather. The high level reasoning is that before trying to insert an
    // all-gather, we are left with an empty `outAxesPerDim`, since all out axes
    // can be handled by the previous collectives, so we are left with
    // all-gathering all axes in `inAxesPerDim` and we're done.
    //
    // Otherwise, we need at most 2 iterations.

    // TODO(tomnatan): consider looping only over all-to-all and collective
    // permute as long as one of them was inserted.
    for (int i = 0; i < 2 && !isDone(); ++i) {
      // 1. Try to insert an all-slice, that decreases the size of the tensor.
      tryAllSlice();

      // 2. Try to insert a collective permute, that preserves the size of the
      // tensor and only communicates from each device to another device.
      tryCollectivePermute();

      // 3. Try to insert all-to-alls, that preserves the size of the tensor.
      //
      // We first try to insert all-to-alls that move axes to the right position
      // at the target dimension, to make sure multiple all-to-alls from
      // different source dimensions to the same target dimension are inserted
      // in the right order (to avoid the need for a collective permute), then
      // we lift that constraint.
      tryAllToAlls(/*allowOutOfOrderTarget=*/false);
      tryAllToAlls(/*allowOutOfOrderTarget=*/true);

      // 4. Try to insert an all-gather, that increases the size of the tensor.
      tryAllGather();
    }
    assert(isDone());

    return result;
  }

 private:
  // Returns true if the input sharding has been transformed into the output
  // sharding, i.e., both `inAxesPerDim` and `outAxesPerDim` are empty and
  // `curMeshOrRef == outMeshOrRef`.
  bool isDone() const {
    return curMeshOrRef == outMeshOrRef &&
           llvm::all_of(inAxesPerDim, std::mem_fn(&AxisList::empty)) &&
           llvm::all_of(outAxesPerDim, std::mem_fn(&AxisList::empty));
  }

  MLIRContext* getContext() const { return rewriter.getContext(); }

  int64_t getRank() const { return inAxesPerDim.size(); }

  TensorShardingAttr getCurrentSharding() const {
    return TensorShardingAttr::getClosed(getContext(), curMeshOrRef,
                                         currentAxesPerDim, unreducedAxes);
  }

  // If an all-gather can be performed on `dim`, returns the axes to gather for
  // that dimension.
  //
  // We gather the suffix of axes (`gatheringAxes`) in `inAxesPerDim[dim]` that
  // aren't present in `outAxesPerDim`, and update the internal state as
  // follows: `gatheringAxes` are popped from the back of `inAxesPerDim[dim]`
  // and `currentAxesPerDim[dim]`.
  //
  // For example:
  //
  // Input: `dim = 1`
  //
  // Initial state:
  // - `inAxesPerDim = [[], ["x", "y", "z", "w"]]`
  // - `outAxesPerDim = [["y"], []]`
  // - `currentAxesPerDim = [[], ["x", "y", "z", "w"]]`
  //
  // Returns: `["z", "w"]`, and updates:
  // - `inAxesPerDim = [[], ["x", "y"]]`
  // - `currentAxesPerDim = [[], ["x", "y"]]`
  SmallVector<AxisRefAttr> getGatheringAxes(int64_t dim) {
    AxisList& inAxes = inAxesPerDim[dim];
    if (inAxes.empty()) {
      return {};
    }
    SmallVector<AxisRefAttr>& currentAxes = currentAxesPerDim[dim];
    SmallVector<AxisRefAttr> gatheringAxes;
    gatheringAxes.reserve(inAxes.size());
    auto axisRevIt = inAxes.rbegin();
    while (axisRevIt != inAxes.rend() &&
           !outAxisToDimAndIndex.contains(*axisRevIt)) {
      inAxisSet.erase(*axisRevIt);
      --axisRevIt;
    }
    auto inAxisIt = axisRevIt.base();
    popBackFromCurrentAxes(currentAxes, inAxes, inAxisIt);
    while (inAxisIt != inAxes.end()) {
      addAxisOrMerge(gatheringAxes, *inAxisIt, mesh);
      inAxisIt = inAxes.erase(inAxisIt);
    }
    return gatheringAxes;
  }

  // Tries to insert an `sdy.all_gather`.
  void tryAllGather() {
    bool hasGatheringAxes = false;
    for (auto [dim, collectiveAxes] : llvm::enumerate(collectiveAxesPerDim)) {
      SmallVector<AxisRefAttr> gatheringAxes = getGatheringAxes(dim);
      if (!gatheringAxes.empty()) {
        hasGatheringAxes = true;
      }
      collectiveAxes = AxisRefListAttr::get(getContext(), gatheringAxes);
    }
    if (hasGatheringAxes) {
      result = AllGatherOp::create(rewriter, loc, result, collectiveAxesPerDim,
                                   getCurrentSharding());
    }
  }

  // For each dimension d, distribute axes from `getAvailableAxes(d)` in
  // `inAxesPerDim[d]` based on the capacity for that dimension
  // (`capacityPerDim[d]`).
  //
  // For each dimension d, as long as `capacityPerDim[d] > 1` , pops the first
  // axis A in `getAvailableAxes(d), and either:
  // - Adds A as a whole to `inAxesPerDim[d]` if `size(A) >= capacityPerDim[d]`.
  // - Splits A into two sub-axes A1 and A2, such that
  //   `size(A1) == capacityPerDim[d]`, adds A1 to `inAxesPerDim[d]`, and adds
  //   A2 back to the front of `getAvailableAxes(d)`.
  // - Skips A if it isn't divisible by `capacityPerDim[d]` or vice versa, and
  //   adds it back to the front of `getAvailableAxes(d)`.
  //
  // For each axis A that is added to `inAxesPerDim[d]`, calls
  // `consumeAxisToAdd(A, d)`.
  void distributeInAxesWithinCapacity(
      bool addToFront, std::function<AxisList&(int64_t)> getAvailableAxes,
      std::function<void(AxisRefAttr, int64_t)> consumeAxisToAdd =
          [](AxisRefAttr, int64_t) {}) {
    SmallVector<AxisRefAttr> splitAddedAxes;
    for (auto [dim, inAxesAndCapacity] :
         llvm::enumerate(llvm::zip_equal(inAxesPerDim, capacityPerDim))) {
      auto [inAxes, dimCapacity] = inAxesAndCapacity;
      auto inAxesIt = addToFront ? inAxes.begin() : inAxes.end();
      AxisList& availableAxes = getAvailableAxes(dim);
      auto availableIt = availableAxes.begin();
      while (availableIt != availableAxes.end() && dimCapacity > 1) {
        auto [withinAxis, remainderAxis] =
            getAxisWithinCapacity(*availableIt, dimCapacity, mesh);
        if (!withinAxis) {
          ++availableIt;
          continue;
        }
        availableIt = availableAxes.erase(availableIt);
        inAxes.insert(inAxesIt, *withinAxis);
        inAxisSet.insert(*withinAxis);
        consumeAxisToAdd(*withinAxis, dim);
        if (remainderAxis) {
          splitAddedAxes.push_back(*withinAxis);
          availableAxes.push_front(*remainderAxis);
        }
      }
    }
    // We need to align sub-axes again if an axis from `availableAxes` was split
    // due to capacity constraint.
    llvm::sort(splitAddedAxes);
    alignSubAxesByDecomposition(outAxesPerDim, splitAddedAxes, mesh);
  }

  // Same as the overload above, but takes a single `availableAxes` to
  // distribute across all dimensions.
  void distributeInAxesWithinCapacity(
      AxisList& availableAxes, bool addToFront,
      std::function<void(AxisRefAttr, int64_t)> consumeAxisToAdd =
          [](AxisRefAttr, int64_t) {}) {
    distributeInAxesWithinCapacity(
        addToFront, /*getAvailableAxes=*/
        [&](int64_t) -> AxisList& { return availableAxes; }, consumeAxisToAdd);
  }

  // For an future all-to-all from source dimension `d1` to target dimension
  // `d2`, Holds the range of out axes in that dimension to slice at `d1`.
  struct AxesToSliceForAllToAll {
    AxisList::iterator outAxisBeginIt;
    AxisList::iterator outAxisEndIt;
  };

  // Return axes to slice at a given source dimension `srcDim` to perform an
  // all-to-all to a target dimension (`tgtDim`) with additional axes, if
  // certain conditions are met that indicate that a redundant
  // collective-permute can be avoided by slicing at `srcDim` rather than
  // `tgtDim`.
  //
  // All the following must hold:
  //
  // - `inAxesPerDim[srcDim]` isn't empty, otherwise an all-to-all isn't needed
  //   from that dimension.
  //
  // - `outAxesPerDim[srcDim]` is empty, otherwise it means the source dimension
  //   has misplaced axes that a collective-permute can replace.
  //
  // - `inAxesPerDim[tgtDim]` is empty, otherwise it means the target dimension
  //   has misplaced axes that a collective-permute can replace.
  //
  // - The first axis in `outAxesPerDim[tgtDim]` beyond
  //   `inAxesPerDim[srcDim].back()` isn't present in `inAxisSet` (i.e.,
  //   available to slice), otherwise there is no axis to slice at `srcDim`.
  //
  // - A suffix of `inAxesPerDim[srcDim]` is contained within
  //   `outAxesPerDim[tgtDim]` (in the same order) and other axes in
  //   `inAxesPerDim[srcDim]` don't appear in `outAxesPerDim[tgtDim]`, otherwise
  //   a collective-permute will be needed to reorder or replace axes.
  //
  // - `srcDim` can accommodate all available axes in `outAxesPerDim[tgtDim]`
  //   beyond `inAxesPerDim[srcDim].back()`. Otherwise, slicing those axes at
  //   `srcDim` would require padding as the dimension size isn't divisible by
  //   the product of axis sizes.
  //
  // In which case, returns a range containing all axes in
  // `outAxesPerDim[tgtDim]` that are available to slice beyond
  // `inAxesPerDim[srcDim].back()`
  //
  // In addition, divides the capacity of `tgtDim` by the product of axis sizes
  // in `srcDim` that will be moved to `tgtDim` after slicing along the
  // returned axes, as we are effectively "borrowing" the capacity for `srcDim`.
  //
  // For example:
  //
  // Input: `srcDim = 1`
  //
  // Initial state:
  // - `mesh = {"x": 2, "y": 2, "z": 2, "w": 2}`
  // - `getTensorShape(result)` = [4, 8, 32]
  // - `inAxesPerDim = [["w"], ["x"], []]`
  // - `outAxesPerDim = [[], [], ["x", "y", "z", "w"]]`
  // - `capacityPerDim = [1, 1, 16]`
  //
  // Returns: `["y", "z"]` and updates `capacityPerDim = [1, 1, 2]`
  std::optional<AxesToSliceForAllToAll> getAxesToSliceForAllToAll(
      int64_t srcDim) {
    AxisList& srcInAxes = inAxesPerDim[srcDim];
    if (srcInAxes.empty() || !outAxesPerDim[srcDim].empty()) {
      // No axes at source dimension to move, or source dimension has other axes
      // in output sharding.
      return std::nullopt;
    }
    auto outAxisEntryIt = outAxisToDimAndIndex.find(srcInAxes.back());
    if (outAxisEntryIt == outAxisToDimAndIndex.end()) {
      // First in axis at source isn't present in `outAxesPerDim`.
      return std::nullopt;
    }

    int64_t tgtDim = outAxisEntryIt->second.dim;
    if (!inAxesPerDim[tgtDim].empty()) {
      // The target dimension is currently sharded on a misplaced axis.
      return std::nullopt;
    }

    AxisList& tgtOutAxes = outAxesPerDim[tgtDim];
    // Find the first out axis beyond `srcInAxes.back()`.
    auto startOutAxisIt = ++llvm::find(tgtOutAxes, srcInAxes.back());
    if (startOutAxisIt == tgtOutAxes.end() ||
        inAxisSet.contains(*startOutAxisIt)) {
      // `tgtOutAxes` doesn't have any axes beyond `srcInAxes.back()` or the
      // first of those axes isn't available to slice.
      return std::nullopt;
    }

    // Advance `inAxisRevIt` beyond the suffix of `srcInAxes` that is contained
    // in `tgtOutAxes`.
    auto inAxisRevIt = srcInAxes.rbegin();
    auto outAxisRevIt = std::make_reverse_iterator(startOutAxisIt);
    int64_t commonAxesSize = 1;
    while (inAxisRevIt != srcInAxes.rend() &&
           outAxisRevIt != tgtOutAxes.rend() && *inAxisRevIt == *outAxisRevIt) {
      commonAxesSize *= inAxisRevIt->getSize(mesh);
      ++inAxisRevIt;
      ++outAxisRevIt;
    }

    for (; inAxisRevIt != srcInAxes.rend(); ++inAxisRevIt) {
      if (outAxisEntryIt = outAxisToDimAndIndex.find(*inAxisRevIt);
          outAxisEntryIt != outAxisToDimAndIndex.end() &&
          outAxisEntryIt->second.dim == tgtDim) {
        // There is an out of order axis in `srcInAxes` that appears in
        // `tgtOutAxes`.
        return std::nullopt;
      }
    }

    auto curOutAxisIt = startOutAxisIt;
    int64_t addedSlicingAxesSize = 1;
    while (curOutAxisIt != tgtOutAxes.end() &&
           !inAxisSet.contains(*curOutAxisIt)) {
      // Current out axis is available to slice.
      addedSlicingAxesSize *= (curOutAxisIt++)->getSize(mesh);
    }

    // After slicing, `srcDim` will be sharded by the current axes and the added
    // slicing axes.
    int64_t newShardedSizeOnSrcDim =
        getShardedSize(currentAxesPerDim[srcDim], mesh) * addedSlicingAxesSize;
    // If the dimension size is not divisible by the product of these axis
    // sizes, we cannot slice.
    if (getTensorShape(result)[srcDim] % newShardedSizeOnSrcDim != 0) {
      return std::nullopt;
    }

    // Divide the capacity of `tgtDim` by the new sharded size of `srcDim`.
    capacityPerDim[tgtDim] /= commonAxesSize * addedSlicingAxesSize;

    return AxesToSliceForAllToAll{startOutAxisIt, curOutAxisIt};
  }

  // If an all-slice can be performed, returns the axes to slice for each
  // dimension, otherwise returns std::nullopt.
  //
  // We define the term capacity per dimension for all-slice - the product of
  // axis sizes in `outAxesPerDim[d]` divided by the product of axis sizes in
  // `inAxesPerDim[d]` for each dimension d, or the former divided by their GCD,
  // if the former is not divisible by the latter (as the dimension size needs
  // to be a multiplier of both). In other words, the capacity represents how
  // much the output is sharded more than the input along a specific dimension.
  //
  // Constraint: we can only slice dimension d along axes whose product of
  // sizes doesn't exceed the capacity for that dimension, otherwise we will
  // incur a redundant all-to-all. Under certain conditions (see
  // `getAxesToSliceForAllToAll`), we would use the capacity in one dimension to
  // slice in another dimension.
  //
  // Let `capacityPerDim[d]` be the capacity for dimension d. We update this
  // value as we pick slicing axes, i.e., if we slice dimension d along an axis
  // of size n, we divide `capacityPerDim[d]` by n.
  //
  // We pick the slicing axes across all dimensions in three stages:
  //
  // 1. For each dimension `d1`, if certain conditions are met for another
  //    dimension `d2`, slice axes from `outAxesPerDim[d2]` at dimension `d1`,
  //    for a future all-to-all from `d1` to `d2` (see
  //   `getAxesToSliceForAllToAll`).
  //
  // 2. For each dimension `d`, each axis A in `outAxesPerDim[d]` that isn't
  //    present in `inAxisSet` (i.e., available to slice) is sliced on dimension
  //    d as long as `capacityPerDim[d] > 1`.
  //
  // 3. Then, we iterate over all remaining axes in `outAxesPerDim` that aren't
  //    present in `inAxisSet` (i.e., available to slice), and slice each on the
  //    first dimension d such that `capacityPerDim[d] > 1`.
  //
  // In case `size(A) > capacityPerDim[d]`, we split A into two sub-axes A1 and
  // A2, such that `size(A1) == capacityPerDim[d]`, and slice along A1 (filling
  // in the gap).
  //
  // The internal state is updated as follows for each dimension `d` and the
  // slicing axes on that dimension (`slicingAxes`):
  //
  // - `slicingAxes` are appended to `inAxesPerDim[d]` and
  //   `currentAxesPerDim[d]`.
  // - The common prefix between `inAxesPerDim[d]` and `outAxesPerDim[d]` is
  //   removed from both.
  //
  // Note that this brings us closer to being done, i.e., having both
  // `inAxesPerDim` and `outAxesPerDim` empty, because we take axes that are
  // present in `outAxesPerDim` but not in `inAxesPerDim`, and either:
  //
  // - Remove them from `outAxesPerDim`, if they are where they need to be.
  // - Add them to `inAxesPerDim` otherwise, which brings the current sharded
  //   size closer to the output sharded size, and will allow us to perform an
  //   all-to-all or collective-permute to get them to the right place.
  //
  // Example 1:
  //
  // Initial state:
  // - `mesh = {"x": 2, "y": 2, "z": 2, "w": 2}`
  // - `inAxesPerDim = [["y"], [], []]`,
  // - `outAxesPerDim = [["x"], ["y"], ["z"]]`
  // - `currentAxesPerDim = [["w", "y"], [], []]`
  //
  // Returns: `[[], ["x"], ["z"]]`, and updates:
  // - `inAxesPerDim = [["y"], ["x"], []]`
  // - `outAxesPerDim = [["x"], ["y"], []]`
  // - `currentAxesPerDim = [["w", "y"], ["x"], ["z"]]`
  //
  // Example 2:
  //
  // Initial state:
  // - `mesh = {"x": 2, "y": 2, "z": 2, "w": 2}`
  // - `inAxesPerDim = [["y"], ["z"], []]`
  // - `outAxesPerDim = [["x"], [], ["w"]]`
  // - `currentAxesPerDim = [["y"], ["z"], []]`
  //
  // Returns: `[[], [], ["w"]]`, and updates:
  // - `inAxesPerDim = [["y"], ["z"], []]`
  // - `outAxesPerDim = [["x"], [], []]`
  // - `currentAxesPerDim = [["y"], ["z"], ["w"]]`
  //
  // Example 3 (`getAxesToSliceForAllToAll`):
  //
  // Initial state:
  // - `mesh = {"x": 2, "y": 2, "z": 2, "w": 2}`
  // - `getTensorShape(result)` = [4, 8, 32]
  // - `inAxesPerDim = [["w"], ["x"], []]`
  // - `outAxesPerDim = [[], [], ["x", "y", "z", "w"]]`
  // - `capacityPerDim = [1, 1, 16]`
  //
  // Returns: `[[], ["y", "z"], []]`, and updates:
  // - `inAxesPerDim = [["w"], ["x", "y" "z"], []]`
  // - `outAxesPerDim = [[], [], ["x", "y", "z", "w"]]`
  // - `currentAxesPerDim = [["w"], ["x", "y", "z"], []]`
  std::optional<AxesPerDim> getSlicingAxesPerDim() {
    AxesPerDim slicingAxesPerDim(getRank());
    bool hasSlicingAxes = false;

    // Initialize capacity per dimension.
    for (auto [inAxes, outAxes, dimCapacity] :
         llvm::zip_equal(inAxesPerDim, outAxesPerDim, capacityPerDim)) {
      int64_t inShardedSize = getShardedSize(inAxes, mesh);
      int64_t outShardedSize = getShardedSize(outAxes, mesh);
      dimCapacity = outShardedSize / std::gcd(inShardedSize, outShardedSize);
    }

    // 1. For a future all-to-all from a source dimension `d1` to a target
    // dimension `d2`, slice axes from `outAxesPerDim[d2]` at the source
    // dimension `d1`.
    for (int64_t srcDim = 0; srcDim < getRank(); ++srcDim) {
      std::optional<AxesToSliceForAllToAll> axesToSlice =
          getAxesToSliceForAllToAll(srcDim);
      if (!axesToSlice) {
        continue;
      }
      hasSlicingAxes = true;
      std::for_each(axesToSlice->outAxisBeginIt, axesToSlice->outAxisEndIt,
                    [&](AxisRefAttr outAxis) {
                      inAxesPerDim[srcDim].push_back(outAxis);
                      inAxisSet.insert(outAxis);
                      addAxisOrMerge(slicingAxesPerDim[srcDim], outAxis, mesh);
                      addAxisOrMerge(currentAxesPerDim[srcDim], outAxis, mesh);
                    });
    }

    // 2. Slice axes in the dimension they appear in `outAxesPerDim`, i.e. the
    // desired dimension, as long as the per-dim capacity allows.
    AxisList availableOutAxes;
    for (auto [inAxes, outAxes, currentAxes, slicingAxes, dimCapacity] :
         llvm::zip_equal(inAxesPerDim, outAxesPerDim, currentAxesPerDim,
                         slicingAxesPerDim, capacityPerDim)) {
      auto outIt = outAxes.begin();
      while (outIt != outAxes.end()) {
        AxisRefAttr outAxis = *outIt;
        if (inAxisSet.contains(outAxis)) {
          // Out axis isn't available to slice.
          ++outIt;
          continue;
        }
        // Out axis is available to slice.

        auto [withinAxis, remainderAxis] =
            getAxisWithinCapacity(outAxis, dimCapacity, mesh);
        if (!withinAxis) {
          // We still want to add available axes in this dimension to
          // `availableOutAxes` so they can be added in the 2nd stage to another
          // dimension.
          availableOutAxes.push_back(outAxis);
          ++outIt;
          continue;
        }
        hasSlicingAxes = true;
        addAxisOrMerge(slicingAxes, *withinAxis, mesh);
        addAxisOrMerge(currentAxes, *withinAxis, mesh);
        if (inAxes.empty() && outIt == outAxes.begin()) {
          // Slicing axis is where it needs to be.
          outIt = outAxes.erase(outIt);
        } else {
          inAxisSet.insert(*withinAxis);
          inAxes.push_back(*withinAxis);
          *outIt = *withinAxis;
          ++outIt;
        }
        if (remainderAxis) {
          outAxes.insert(outIt, *remainderAxis);
          availableOutAxes.push_back(*remainderAxis);
        }
      }
    }

    // 3. Slice axes in the first dimension that has enough capacity.
    distributeInAxesWithinCapacity(
        availableOutAxes, /*addToFront=*/false,
        /*consumeAxisToAdd=*/[&](AxisRefAttr axisToAdd, int64_t dim) {
          hasSlicingAxes = true;
          addAxisOrMerge(slicingAxesPerDim[dim], axisToAdd, mesh);
          addAxisOrMerge(currentAxesPerDim[dim], axisToAdd, mesh);
        });
    // We need to recreate the map because we might have split an out axis due
    // to capacity constraint.
    outAxisToDimAndIndex = getAxisToDimAndIndex(outAxesPerDim);

    return hasSlicingAxes ? std::make_optional(slicingAxesPerDim)
                          : std::nullopt;
  }

  // Tries to insert an `sdy.all_slice`.
  void tryAllSlice() {
    if (std::optional<AxesPerDim> slicingAxesPerDim = getSlicingAxesPerDim()) {
      for (auto [collectiveAxes, slicingAxes] :
           llvm::zip_equal(collectiveAxesPerDim, *slicingAxesPerDim)) {
        collectiveAxes = AxisRefListAttr::get(getContext(), slicingAxes);
      }
      result = AllSliceOp::create(rewriter, loc, result, collectiveAxesPerDim,
                                  getCurrentSharding());
    }
  }

  // We should insert a collective permute if one of the following holds:
  //
  // 1. Both `inAxesPerDim[d]` and `outAxesPerDim[d]` aren't empty for a certain
  //    dimension d and their front axes are divisible. This means we can
  //    replace a prefix of `inAxesPerDim[d]` with a prefix of
  //    `outAxesPerDim[d]`, such that the prefixes sharded size is the minimum
  //    of the two sharded sizes. The in and out prefixes might contain
  //    different permutations of the same axes.
  //
  // 2. There is an axis A in `outAxesPerDim` that is not in `inAxesPerDim`
  //    (needs to be added to the current sharding), and an axis B in
  //    `inAxesPerDim` that is not in `outAxesPerDim` (needs to be removed from
  //    the current sharding), and A is divisible by B or vice versa. This means
  //    we can replace B with A or a sub-axis of it.
  //
  // 3. `inAxesPerDim[d1] = [..., A, ..., B, C, ...]` such that A and C are
  //    in `outAxesPerDim[d2]` (d1 != d2) but B isn't, This means we can reorder
  //    `inAxesPerDim[d1]` such that A and C are contiguous and in the desired
  //    order in `outAxesPerDim[d2]`.
  //
  // 4. `inAxesPerDim[d1] = [..., A, B, ...]` such that A and B are in
  //    `outAxesPerDim[d2]` (d1 and d2 can be the same) but in different order
  //    or discontiguous. This means we can replace A and B in
  //    `inAxesPerDim[d1]` with axes C and D respectively such that
  //    `outAxesPerDim[d2] = [..., C, D, ...]` (note that both C and D can be
  //    either A, B, or a different axis).
  //
  // 5. `inAxesPerDim[d1] = [..., A, B, ...]` such that `outAxesPerDim[d]` is
  //    empty, A is in `outAxesPerDim[d2]` (d2 != d1) but B isn't in
  //    `outAxesPerDim`. This means that we can reorder `inAxesPerDim[d]` such
  //    that B is before A, and A can be moved to d2 via an all-to-all before B
  //    is all-gathered.
  bool shouldCollectivePermute() {
    OptionalAxisRef availableInAxis;
    OptionalAxisRef availableOutAxis;
    for (auto [dim, inOutAxes] :
         llvm::enumerate(llvm::zip_equal(inAxesPerDim, outAxesPerDim))) {
      auto [inAxes, outAxes] = inOutAxes;
      if (!inAxes.empty() && !outAxes.empty() &&
          areSizesDivisible(inAxes.front(), outAxes.front(), mesh)) {
        // We can replace in axes with out axes (condition #1).
        return true;
      }
      for (AxisRefAttr outAxis : outAxes) {
        if (!inAxisSet.contains(outAxis)) {
          availableOutAxis = outAxis;
        }
      }
      std::optional<int64_t> lastOutDim;
      int64_t lastOutIndex = 0;
      BitVector seenDims(getRank());
      for (AxisRefAttr inAxis : inAxes) {
        std::optional<int64_t> curOutDim;
        if (auto outAxisEntryIt = outAxisToDimAndIndex.find(inAxis);
            outAxisEntryIt != outAxisToDimAndIndex.end()) {
          curOutDim = outAxisEntryIt->second.dim;
          int64_t curOutIndex = outAxisEntryIt->second.index;
          if ((curOutDim == dim || seenDims.test(*curOutDim)) &&
              (lastOutDim != curOutDim || curOutIndex != lastOutIndex + 1)) {
            // Discontiguous destination dim or axes out of order at current or
            // destination dim (condition #3 & #4).
            return true;
          }
          seenDims.set(*curOutDim);
          lastOutIndex = curOutIndex;
        } else if (lastOutDim && outAxes.empty()) {
          // Axis to all-gather not at the front and this dimension has no out
          // axes (condition #5).
          return true;
        } else {
          availableInAxis = inAxis;
        }
        lastOutDim = curOutDim;
      }
    }
    // We can replace available in axes (axes that need to be gathered) with
    // available out axes (axes that need to be sliced) (condition #2).
    return availableOutAxis && availableInAxis &&
           areSizesDivisible(*availableOutAxis, *availableInAxis, mesh);
  }

  // Performs a collective-permute, assuming `shouldCollectivePermute` is true.
  //
  // We define the term capacity per dimension for collective permute - the
  // product of axis sizes in `inAxesPerDim[d]` for each dimension d, or 1 if
  // the former is not divisible by the latter. In other words, the capacity
  // represents how much the input is sharded along a specific dimension.
  //
  // Constraint: for each dimension d, we can replace the axes sharding that
  // dimension in the current sharding with any list of available axes (we can't
  // use the same axis twice) as long as product of axis sizes is equal to the
  // capacity for that dimension.
  //
  // Let `capacityPerDim[d]` be the capacity for dimension d. We update this
  // value as we pick new axes (or a different permutation) for the current
  // sharding, i.e., if we pick an axis of size n for dimension d, we divide
  // `capacityPerDim[d]` by n.
  //
  // We first clear `inAxesPerDim` (let `prevInAxesPerDim` be the previous
  // value), then pick new axes across all dimensions in three stages:
  //
  // 1. For each dimension d, we pop the first axis A in `outAxesPerDim[d]` as
  //    long as `curCapacity[d] > 1`, since the axis is now in the right place.
  //
  // 2. Then, we iterate over all remaining axes in `outAxesPerDim`, i.e., axes
  //    that will need to stay in the current sharding, and add each to the
  //    *back* of `inAxesPerDim[d]` for the first dimension d such that
  //    `curCapacity[d] > 1`.
  //
  // 3. Then, for each dimension d, we add axes in `prevInAxesPerDim[d]` that
  //    are not in `outAxesPerDim[d]`, i.e., axes that will need to be
  //    all-gathered, to the *front* of `inAxesPerDim[d]` as long as
  //    `curCapacity[d] > 1`. We add to the front so that those axes can be
  //    all-gathered *after* axes in the back are moved to another dimension via
  //    an all-to-all. Those axes will essentially be added back in the same
  //    place as they were before, which makes the collective-permute simpler.
  //
  // 4. Finally, we iterate over all remaining axes in `prevInAxesPerDim` that
  //    are not in `outAxesPerDim` (those not used in #3), and add each to the
  //    *front* of `inAxesPerDim[d]` for the first dimension d such that
  //    `curCapacity[d] > 1`.
  //
  // In case `size(A) > curCapacity[d]`, we split A into two sub-axes A1 and A2,
  // such that `size(A1) == curCapacity[d]`, and pick A1 for that dimension
  // (filling in the gap).
  //
  // The internal state is updated as follows for each dimension `d`:
  //
  // - Axes in `inAxesPerDim[d]` that were replaced with axes in
  //   `outAxesPerDim[d]` at the right place, are removed from
  //   `outAxesPerDim[d]` (they are part of the common prefix).
  // - Otherwise, axes are replaced in `inAxesPerDim[d]` without changing
  //   `outAxesPerDim[d]` (they aren't part of the common prefix).
  // - For every axis we replaced with another for dimension d, we do the same
  //   in `currentAxesPerDim[d]`
  //
  // Note that this brings us closer to being done, i.e., having both
  // `inAxesPerDim` and `outAxesPerDim` empty, because we either:
  //
  // - Remove axes from `outAxesPerDim`, if they are placed in the right place.
  // - Places axes that are present in `outAxesPerDim[d1]` into
  //   `inAxesPerDim[d2]`, trying to keep them together and in the right order,
  //   which will allow us to perform all-to-all to get them to the right place.
  // - Moves axes that were present in `inAxesPerDim[d]` but not in
  //   `outAxesPerDim` to the front, so we can all-gather them *after* other
  //   axes are moved to the right place via all-to-all.
  //
  // Example 1:
  //
  // Initial state:
  // - `mesh = {"x": 2, "y": 2, "z": 2, "w": 2, "u": 2}`
  // - `inAxesPerDim = [["x", "u"], [], ["z", "w"]]`
  // - `outAxesPerDim = [[], ["y"], ["w", "z"]]`
  // - `currentAxesPerDim = [["x", "u"], [], ["z", "w"]]`
  //
  // Updates:
  // - `inAxesPerDim = [["x", "y"], [], []]`,
  // - `outAxesPerDim = [[], ["y"], []]`
  // - `currentAxesPerDim = [["x", "y"], [], ["w", "z"]]`
  //
  // Example 2:
  //
  // Initial state:
  // - `mesh = {"x": 2, "y": 2, "z": 2}`
  // - `inAxesPerDim = [["z", "y", "x"], [], []]`
  // - `outAxesPerDim = [[], ["y"], ["x", "z"]]`
  // - `currentAxesPerDim = [["z", "y", "x"], [], []]`
  //
  // Updates:
  // - `inAxesPerDim = [["y", "x", "z"], [], []]`,
  // - `outAxesPerDim = [[], ["y"], ["x", "z"]]`
  // - `currentAxesPerDim = [["y", "x", "z"], [], []]`
  //
  // Example 3:
  //
  // Initial state:
  // - `mesh = {"x": 2, "y": 2, "z": 2}`
  // - `inAxesPerDim = [["x", "y"], ["z"]]`
  // - `outAxesPerDim = [["z"], []]`
  // - `currentAxesPerDim = [["x", "y"], ["z"]]`
  //
  // Updates:
  // - `inAxesPerDim = [["y"], ["x"]]`,
  // - `outAxesPerDim = [[], []]`
  // - `currentAxesPerDim = [["z", "y"], ["x"]]`
  void performCollectivePermute() {
    AxisList availableOutAxes;
    SmallVector<AxisList> availableInAxesPerDim(getRank());

    // 1. Place out axes in the right position.
    inAxisSet.clear();
    for (auto [inAxes, outAxes, currentAxes, dimCapacity, availableInAxes] :
         llvm::zip_equal(inAxesPerDim, outAxesPerDim, currentAxesPerDim,
                         capacityPerDim, availableInAxesPerDim)) {
      // TODO(tomnatan): consider reusing from `getSlicingAxesPerDim`.
      dimCapacity = getShardedSize(inAxes, mesh);
      int64_t usedCapacity = dimCapacity;
      popBackFromCurrentAxes(currentAxes, inAxes, inAxes.begin());
      while (dimCapacity > 1 && !outAxes.empty()) {
        auto [withinAxis, remainderAxis] =
            getAxisWithinCapacity(outAxes.front(), dimCapacity, mesh);
        if (!withinAxis) {
          // Size of `outAxes.front()` not divisible by capacity or vice versa.
          break;
        }
        outAxes.pop_front();
        addAxisOrMerge(currentAxes, *withinAxis, mesh);
        if (remainderAxis) {
          outAxes.push_front(*remainderAxis);
        }
      }
      llvm::copy(outAxes, std::back_inserter(availableOutAxes));

      usedCapacity /= dimCapacity;
      // Collect available in axes for this dimension. Place axes or sub-axes
      // that weren't replaced by out axes (i.e., past `usedCapacity`) at the
      // front, so we can put them back in their original position in step #3.
      inAxes.remove_if([&](AxisRefAttr axis) {
        return outAxisToDimAndIndex.contains(axis);
      });
      while (usedCapacity > 1 && !inAxes.empty()) {
        auto [withinAxis, remainderAxis] =
            getAxisWithinCapacity(inAxes.front(), usedCapacity, mesh);
        if (!withinAxis) {
          // Size of `inAxes.front()` not divisible by capacity or vice versa.
          break;
        }
        inAxes.pop_front();
        availableInAxes.push_back(*withinAxis);
        if (remainderAxis) {
          inAxes.push_front(*remainderAxis);
        }
      }
      availableInAxes.splice(availableInAxes.begin(), inAxes);
    }

    // TODO(b/394552553): we should keep `availableOutAxes` in clusters by dim
    // and prioritize big clusters to big capacity.

    // 2. Distribute available out axes in any dimension with capacity.
    distributeInAxesWithinCapacity(availableOutAxes, /*addToFront=*/false);
    // 3. Distribute available in axes in their original position.
    distributeInAxesWithinCapacity(
        /*addToFront=*/true,
        [&](int64_t dim) -> AxisList& { return availableInAxesPerDim[dim]; });
    // 4. Distribute available in axes in any dimension with capacity.
    AxisList availableInAxes = concatAxisLists(availableInAxesPerDim);
    distributeInAxesWithinCapacity(availableInAxes, /*addToFront=*/true);

    // We need to recreate the map because we might have split an out axis due
    // to capacity constraint.
    outAxisToDimAndIndex = getAxisToDimAndIndex(outAxesPerDim);

    for (auto [inAxes, currentAxes] :
         llvm::zip_equal(inAxesPerDim, currentAxesPerDim)) {
      for (AxisRefAttr axis : inAxes) {
        addAxisOrMerge(currentAxes, axis, mesh);
      }
    }
  }

  // Tries to insert an `sdy.collective_permute`.
  void tryCollectivePermute() {
    // We separate the decision of whether to insert a collective permute from
    // the actual creation of the collective permute, since the latter isn't
    // guaranteed to maintain the order of axes in case a collective permute is
    // actually redundant.
    if (shouldCollectivePermute()) {
      performCollectivePermute();
    } else if (curMeshOrRef == outMeshOrRef) {
      return;
    }
    // If `curMeshOrRef != outMeshOrRef`, it means the output sharding has a
    // mesh with a different order of device ids than that of the input
    // sharding, which requires a collective permute. If
    // `shouldCollectivePermute()` is false, we want to insert a collective
    // permute to reorder the device ids without changing the sharding axes.
    curMeshOrRef = outMeshOrRef;

    // TODO(b/392797233): if the order of device ids changes, but the input or
    // output sharding is fully replicated, we can skip the collective permute.

    result = CollectivePermuteOp::create(rewriter, loc, result,
                                         getCurrentSharding());
  }

  // TODO(b/392952931): currently we are greedily all-to-all-ing axes even if
  // the destination dimension is too small to accommodate the extra axes. This
  // would introduce padding which is sub-optimal, thus we should only do this
  // if the dimension has enough space left.

  // If an all-to-all can be performed for the given source dimension `srcDim`,
  // returns the axes and target dimension of this all-to-all.
  //
  // The suffix of axes in `inAxesPerDim[srcDim]`, such that all axes within the
  // suffix are mapped to the same dimension in `outAxisToDimAndIndex`
  // (`allToAllAxes`), are all-to-all-ed with the mapped dimension as the target
  // (`tgtDim`).
  //
  // The internal state is updated as follows for `allToAllAxes` and `tgtDim`:
  //
  // - `allToAllAxes` are popped from the back of `inAxesPerDim[srcDim]` and
  //   `currentAxesPerDim[srcDim]`.
  // - `allToAllAxes` are appended to `inAxesPerDim[tgtDim]` and
  //   `currentAxesPerDim[tgtDim]`.
  // - The common prefix between `inAxesPerDim[tgtDim]` and
  //   `outAxesPerDim[tgtDim]` is removed from both.
  //
  // If `allowOutOfOrderTarget` is false, we enforce an addition constraint -
  // we only all-to-all if the axes are moved to the target dimension at the
  // right place, i.e., `allToAllAxes` is a prefix of `outAxesPerDim[tgtDim]`.
  //
  // Note that this brings us closer to being done, i.e., having both
  // `inAxesPerDim` and `outAxesPerDim` empty, because we move axes from
  // `inAxesPerDim[srcDim]` to either:
  //
  // - Where they need to be in `tgtDim`, in which case they are removed from
  //   `outAxesPerDim[tgtDim]`.
  // - Move axes from `inAxesPerDim[srcDim]` to `inAxesPerDim[tgtDim]`, which
  //   will allow us to perform a collective permute on them to get them to the
  //   right place.
  //
  // Example 1:
  //
  // Input: `srcDim = 1`, `allowOutOfOrderTarget = true`
  //
  // Initial state:
  // - `inAxesPerDim = [["w"], ["x", "y", "z"], []]`,
  // - `outAxesPerDim = [["x"], [], ["y", "z"]]`
  // - `currentAxesPerDim = [["w"], ["x", "y", "z"], []]`
  //
  // First call returns: `{axes = ["y", "z"], tgtDim = 2}`, and updates:
  // - `inAxesPerDim = [["w"], ["x"], []]`
  // - `outAxesPerDim = [["x"], [], []]`
  // - `currentAxesPerDim = [["w"], ["x"], ["y", "z"]]`
  //
  // Second call returns: `{axes = ["x"], tgtDim = 0}`, and updates:
  // - `inAxesPerDim = [["w", "x"], [], []]`
  // - `outAxesPerDim = [["x"], [], []]`
  // - `currentAxesPerDim = [["w", "x"], [], ["y", "z"]]`
  //
  // Example 2:
  //
  // Input: `srcDim = 0`, `allowOutOfOrderTarget = false`
  //
  // Initial state:
  // - `inAxesPerDim = [["y"], ["x"], []]`,
  // - `outAxesPerDim = [[], [], ["x", "y"]]`
  // - `currentAxesPerDim = [["y"], ["x"], []]`
  //
  // Returns `std::nullopt`, because "y" won't be moved from source dimension
  // (dim 0) to the right position in the target dimension (dim 2).
  //
  // Another call with `srcDim = 0` would return `{axes = ["x"], tgtDim = 2}`,
  // then a call with `srcDim = 1` would return `{axes = ["y"], tgtDim = 2}`,
  // since both axes are moved to the right position.
  std::optional<AllToAllInfo> getAllToAllInfo(int64_t srcDim,
                                              bool allowOutOfOrderTarget) {
    AxisList& srcInAxes = inAxesPerDim[srcDim];

    auto axisRevIt = srcInAxes.rbegin();
    int64_t numAxes = 0;
    std::optional<int64_t> tgtDim;
    for (; axisRevIt != srcInAxes.rend(); ++axisRevIt) {
      auto outAxisEntryIt = outAxisToDimAndIndex.find(*axisRevIt);
      if (outAxisEntryIt == outAxisToDimAndIndex.end()) {
        break;
      }
      int64_t outAxisDim = outAxisEntryIt->second.dim;
      if (outAxisDim == srcDim || (tgtDim && outAxisDim != *tgtDim)) {
        break;
      }
      tgtDim = outAxisDim;
      ++numAxes;
    }

    if (!tgtDim) {
      // Can't do an all-to-all from `srcDim` to any dimension.
      return std::nullopt;
    }

    auto startInAxisIt = axisRevIt.base();

    AxisList& tgtOutAxes = outAxesPerDim[*tgtDim];
    if (!allowOutOfOrderTarget &&
        !std::equal(startInAxisIt, srcInAxes.end(), tgtOutAxes.begin())) {
      // We don't all-to-all if axes aren't moved to the target dimension at the
      // right position.
      return std::nullopt;
    }

    AllToAllInfo result(*tgtDim);
    result.axes.reserve(numAxes);

    SmallVector<AxisRefAttr>& srcCurrentAxes = currentAxesPerDim[srcDim];
    SmallVector<AxisRefAttr>& tgtCurrentAxes = currentAxesPerDim[*tgtDim];

    popBackFromCurrentAxes(srcCurrentAxes, srcInAxes, startInAxisIt);

    AxisList& tgtInAxes = inAxesPerDim[*tgtDim];
    auto srcInAxisIt = startInAxisIt;
    while (srcInAxisIt != srcInAxes.end()) {
      AxisRefAttr axis = *srcInAxisIt;
      addAxisOrMerge(result.axes, axis, mesh);
      addAxisOrMerge(tgtCurrentAxes, axis, mesh);
      srcInAxisIt = srcInAxes.erase(srcInAxisIt);
      inAxisSet.erase(axis);
      if (tgtInAxes.empty() && tgtOutAxes.front() == axis) {
        tgtOutAxes.pop_front();
      } else {
        tgtInAxes.push_back(axis);
        inAxisSet.insert(axis);
      }
    }

    return result;
  }

  // Tries to insert a sequence of `sdy.all_to_all`s.
  //
  // If `allowOutOfOrderTarget` is false, we only all-to-all if the axes are
  // moved to the target dimension at the right position.
  void tryAllToAlls(bool allowOutOfOrderTarget) {
    for (int64_t srcDim = 0; srcDim < getRank(); ++srcDim) {
      while (auto info = getAllToAllInfo(srcDim, allowOutOfOrderTarget)) {
        result = AllToAllOp::create(
            rewriter, loc, result,
            AllToAllParamAttr::get(rewriter.getContext(), info->axes, srcDim,
                                   info->tgtDim),
            getCurrentSharding());
      }
    }
  }

  ConversionPatternRewriter& rewriter;
  Location loc;
  Value result;
  MeshAttr mesh;
  mlir::Attribute curMeshOrRef, outMeshOrRef;
  ArrayRef<AxisRefAttr> unreducedAxes;
  SmallVector<AxisList> inAxesPerDim, outAxesPerDim;
  AxesPerDim currentAxesPerDim;
  SmallVector<int64_t> capacityPerDim;
  SmallVector<AxisRefListAttr> collectiveAxesPerDim;
  AxisSet inAxisSet;
  AxisToDimAndIndex outAxisToDimAndIndex;
};

// Assumes both `inSharding` and `outSharding` are non-null.
bool isEquivalentOnMesh(TensorShardingAttr inSharding,
                        TensorShardingAttr outSharding, ReshardOp reshardOp) {
  if (inSharding.getMeshOrRef() == outSharding.getMeshOrRef()) {
    return true;
  }
  MeshAttr inMesh = inSharding.getMesh(reshardOp);
  MeshAttr outMesh = outSharding.getMesh(reshardOp);
  return inMesh.equals(outMesh, /*ignoreDeviceOrder=*/true);
}

TensorShardingAttr getOrCreateShardingBypassingBarriers(
    Value value, Attribute meshOrRef, bool closedIfMissing = false) {
  while (auto barrierOp = value.getDefiningOp<PropagationBarrierOp>()) {
    value = barrierOp.getInput();
  }
  return getOrCreateSharding(value, meshOrRef, closedIfMissing);
}

class ReshardPattern : public OpConversionPattern<ReshardOp> {
 public:
  using OpConversionPattern::OpConversionPattern;

 private:
  LogicalResult matchAndRewrite(
      ReshardOp op, OpAdaptor adaptor,
      ConversionPatternRewriter& rewriter) const override {
    TensorShardingAttr outSharding = adaptor.getSharding();
    Value bypassedInput = adaptor.getInput();
    while (auto barrierOp =
               bypassedInput.getDefiningOp<PropagationBarrierOp>()) {
      bypassedInput = barrierOp.getInput();
    }

    TensorShardingAttr inSharding = getOrCreateShardingBypassingBarriers(
        bypassedInput, outSharding.getMeshOrRef());
    if (inSharding) {
      MeshAttr inMesh = inSharding.getMesh(op);
      if (inMesh && inMesh.isMaximal()) {
        return rewriter.notifyMatchFailure(
            op, [](Diagnostic& diag) { diag << "Single device inSharding"; });
      }
    }
    if (outSharding) {
      MeshAttr outMesh = outSharding.getMesh(op);
      if (outMesh && outMesh.isMaximal()) {
        return rewriter.notifyMatchFailure(
            op, [](Diagnostic& diag) { diag << "Single device outSharding"; });
      }
    }
    // We support both symbol and inlined meshes.
    if (inSharding.getRank() != outSharding.getRank()) {
      return rewriter.notifyMatchFailure(
          op, [](Diagnostic& diag) { diag << "Incompatible shardings"; });
    }
    if (outSharding.isFullyReplicated()) {
      if (inSharding.isFullyReplicated()) {
        rewriter.replaceOp(op, adaptor.getInput());
        return success();
      }
      // TODO(enver): Hard fail if output sharding has a different unreduced
      // axes than the input sharding. Note that the out sharding may be fully
      // replicated and still have different unreduced axes than the input
      // sharding.
      outSharding = TensorShardingAttr::getFullyClosedLike(inSharding);
    }
    // TODO(enver): Set input mesh to output mesh if input sharding is fully
    // replicated. It requires sdy.all_slice can handle that input and output
    // has a different meshes.
    if (!isEquivalentOnMesh(inSharding, outSharding, op)) {
      // We currently only support a reshard between different meshes if
      // they have the same axes and different device ids, and at least one
      // of the sharding isn't fully replicated.
      return rewriter.notifyMatchFailure(
          op, [](Diagnostic& diag) { diag << "Incompatible meshes"; });
    }

    // TODO(tomnatan): we should verify that the operand of ReshardOp has a
    // sharding.
    // TODO(tomnatan): use a SymbolTable.

    CollectiveInserter collectiveInserter(inSharding, outSharding,
                                          bypassedInput, rewriter, op);
    rewriter.replaceOp(op, collectiveInserter.insert());

    return success();
  }
};

struct ReshardToCollectivesPass
    : public impl::ReshardToCollectivesPassBase<ReshardToCollectivesPass> {
  using ReshardToCollectivesPassBase::ReshardToCollectivesPassBase;

 private:
  LogicalResult initialize(MLIRContext* context) final {
    target = std::make_shared<ConversionTarget>(*context);
    target->addLegalOp<AllGatherOp, AllSliceOp, AllToAllOp,
                       CollectivePermuteOp>();
    target->addDynamicallyLegalOp<ReshardOp>([&](ReshardOp op) {
      TensorShardingAttr inSharding =
          getShardingBypassingBarriers(op.getInput());
      TensorShardingAttr outSharding = op.getSharding();
      if (keepRedundantReshards && isEquivalent(inSharding, outSharding)) {
        return true;
      }
      if (inSharding) {
        MeshAttr inMesh = inSharding.getMesh(op);
        if (inMesh && inMesh.isMaximal()) {
          return true;
        }
      }
      if (outSharding) {
        MeshAttr outMesh = outSharding.getMesh(op);
        if (outMesh && outMesh.isMaximal()) {
          return true;
        }
      }
      // In case out sharding is fully replicated, the reshard is either erased
      // (if input sharding is fully replicated too) or it adds an all gather
      // (if input sharding is sharded), either way it is handled and it should
      // be marked as illegal.
      if (outSharding.isFullyReplicated()) {
        return false;
      }
      if (inSharding && !isEquivalentOnMesh(inSharding, outSharding, op)) {
        return true;
      }
      return false;
    });

    RewritePatternSet patternsInternal(context);
    patternsInternal.add<ReshardPattern>(context);
    patterns = std::move(patternsInternal);

    return success();
  }

  void runOnOperation() final {
    if (failed(applyPartialConversion(getOperation(), *target, patterns))) {
      signalPassFailure();
    }
  }

 private:
  std::shared_ptr<ConversionTarget> target;
  FrozenRewritePatternSet patterns;
};

}  // namespace

}  // namespace sdy
}  // namespace mlir
