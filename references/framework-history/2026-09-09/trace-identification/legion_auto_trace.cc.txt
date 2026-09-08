/* Copyright 2023 Stanford University, NVIDIA Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "legion/legion_auto_trace.h"
#include "legion/legion_auto_trace.inl"
#include "legion/suffix_tree.h"

#include <cmath>
#include <iterator>
#include <unordered_set>

namespace Legion {
  namespace Internal {

    TraceHashHelper::TraceHashHelper() : hasher() {}

    Murmur3Hasher::Hash TraceHashHelper::hash(Operation* op) {
      Operation::OpKind kind = op->get_operation_kind();
      // First just hash the operation kind.
      hasher.hash(kind);
      switch (kind) {
        case Operation::OpKind::TASK_OP_KIND: {
          TaskOp* task = dynamic_cast<TaskOp*>(op);
          switch (task->get_task_kind()) {
            case TaskOp::TaskKind::INDIVIDUAL_TASK_KIND:
            case TaskOp::TaskKind::INDEX_TASK_KIND: {
              this->hash(task);
              break;
            }
            default: {
              std::cout << "Attempting to has unexpected TaskOp kind: "
                        << int(task->get_task_kind())
                        << std::endl;
              assert(false);
            }
          }
          break;
        }
        case Operation::OpKind::FILL_OP_KIND: {
          this->hash(dynamic_cast<FillOp*>(op));
          break;
        }
        case Operation::OpKind::FENCE_OP_KIND: {
          this->hash(dynamic_cast<FenceOp*>(op));
          break;
        }
        case Operation::OpKind::COPY_OP_KIND: {
          this->hash(dynamic_cast<CopyOp*>(op));
          break;
        }
        case Operation::OpKind::ALL_REDUCE_OP_KIND: {
          this->hash(dynamic_cast<AllReduceOp*>(op));
          break;
        }
        case Operation::OpKind::ACQUIRE_OP_KIND: {
          this->hash(dynamic_cast<AcquireOp*>(op));
          break;
        }
        case Operation::OpKind::RELEASE_OP_KIND: {
          this->hash(dynamic_cast<ReleaseOp*>(op));
          break;
        }
        default: {
          std::cout << "Attempting to hash an unsupported operation kind:"
                    << std::string(Operation::get_string_rep(kind))
                    << std::endl;
          assert(false);
        }
      }
      Murmur3Hasher::Hash result;
      hasher.finalize(result);
      return result;
    }

    void TraceHashHelper::hash(TaskOp* op) {
      hasher.hash(op->task_id);
      // Choosing to skip the fields indexes, futures, grants, wait_barriers, arrive_barriers, ...
      for (std::vector<RegionRequirement>::const_iterator it = op->regions.begin();
           it != op->regions.end(); it++) {
        this->hash(*it);
      }
      assert(op->output_regions.size() == 0);
      hasher.hash<bool>(op->is_index_space);
      if (op->is_index_space) {
        hasher.hash<bool>(op->concurrent_task);
        hasher.hash<bool>(op->must_epoch_task);
        hasher.hash(op->index_domain);
      }
    }

    void TraceHashHelper::hash(FillOp* op) {
      this->hash(op->requirement);
      // Choosing to skip the fields grants, wait_barriers, arrive_barriers.
      hasher.hash<bool>(op->is_index_space);
      if (op->is_index_space) {
        hasher.hash(op->index_domain);
      }
      // The value inside the fill is also part of the hash criteria.
      if (op->future.exists()) {
        hasher.hash(op->future.impl->did);
      } else {
        hasher.hash((const void*)op->value, op->value_size);
      }
    }

    void TraceHashHelper::hash(FenceOp* op) {
      hasher.hash(op->get_fence_kind());
    }

    void TraceHashHelper::hash(CopyOp* op) {
      for (std::vector<RegionRequirement>::const_iterator it = op->src_requirements.begin();
           it != op->src_requirements.end(); it++) {
        this->hash(*it);
      }
      for (std::vector<RegionRequirement>::const_iterator it = op->dst_requirements.begin();
           it != op->dst_requirements.end(); it++) {
        this->hash(*it);
      }
      for (std::vector<RegionRequirement>::const_iterator it = op->src_indirect_requirements.begin();
           it != op->src_indirect_requirements.end(); it++) {
        this->hash(*it);
      }
      for (std::vector<RegionRequirement>::const_iterator it = op->dst_indirect_requirements.begin();
           it != op->dst_indirect_requirements.end(); it++) {
        this->hash(*it);
      }
      // Not including the fields grants, wait_barriers, arrive_barriers.
      hasher.hash<bool>(op->is_index_space);
      if (op->is_index_space) {
        hasher.hash(op->index_domain);
      }
    }

    void TraceHashHelper::hash(AllReduceOp* op) {
      // TODO (rohany): I'm not sure if anything else needs to
      //  go into the hash other than just the operation kind.
    }

    void TraceHashHelper::hash(AcquireOp* op) {
      hasher.hash(op->logical_region);
      hasher.hash(op->parent_region);
      for (std::set<FieldID>::const_iterator it = op->fields.begin();
           it != op->fields.end(); it++) {
        hasher.hash(*it);
      }
    }

    void TraceHashHelper::hash(ReleaseOp* op) {
      hasher.hash(op->logical_region);
      hasher.hash(op->parent_region);
      for (std::set<FieldID>::const_iterator it = op->fields.begin();
           it != op->fields.end(); it++) {
        hasher.hash(*it);
      }
    }

    void TraceHashHelper::hash(const RegionRequirement& req) {
      if (req.region.exists()) {
        hasher.hash<bool>(true); // is_reg
        this->hash(req.region);
      } else {
        hasher.hash<bool>(false); // is_reg
        hasher.hash(req.partition.get_index_partition().get_id());
        hasher.hash(req.partition.get_field_space().get_id());
        hasher.hash(req.partition.get_tree_id());
      }
      for (std::set<FieldID>::const_iterator it = req.privilege_fields.begin();
           it != req.privilege_fields.end(); it++) {
        hasher.hash(*it);
      }
      for (std::vector<FieldID>::const_iterator it = req.instance_fields.begin();
           it != req.instance_fields.end(); it++) {
        hasher.hash(*it);
      }
      hasher.hash(req.privilege);
      hasher.hash(req.prop);
      this->hash(req.parent);
      hasher.hash(req.redop);
      // Excluding the fields: tag and flags.
      hasher.hash(req.handle_type);
      hasher.hash(req.projection);
    }

    void TraceHashHelper::hash(const LogicalRegion& region) {
      hasher.hash(region.get_index_space().get_id());
      hasher.hash(region.get_field_space().get_id());
      hasher.hash(region.get_tree_id());
    }

    bool is_operation_traceable(Operation* op) {
      MemoizableOp* memo = op->get_memoizable();
      if (memo == nullptr) {
        return false;
      }
      switch (memo->get_operation_kind()) {
        case Operation::OpKind::TASK_OP_KIND: {
          TaskOp* task = dynamic_cast<TaskOp*>(memo);
          // Tasks with output regions cannot be traced.
          if (task->output_regions.size() > 0) {
            return false;
          }
          return true;
        }
        case Operation::OpKind::FRAME_OP_KIND: {
          return false;
        }
        default:
          return true;
      }
    }

    bool is_operation_ignorable_in_traces(Operation* op) {
      switch (op->get_operation_kind()) {
        case Operation::OpKind::DISCARD_OP_KIND:
          return true;
        default:
          return false;
      }
    }

    void auto_trace_process_repeats(const void* args_) {
      const InnerContext::AutoTraceProcessRepeatsArgs* args = (const InnerContext::AutoTraceProcessRepeatsArgs*)args_;
      std::vector<NonOverlappingRepeatsResult> result;
      if (args->raw_operations != nullptr) {
        log_auto_trace.debug() << "Executing processing repeats meta task on "
                               << args->raw_operations_len << " operations.";
        // If raw_operations is not null, then we have to copy out the contents
        // of raw_operations into a vector and append the sentinel.
        std::vector<Murmur3Hasher::Hash> hashes(args->raw_operations_len + 1);
        for (uint64_t i = 0; i < args->raw_operations_len; i++) {
          hashes[i] = args->raw_operations[i];
        }
        hashes[args->raw_operations_len] = TraceIdentifier::SENTINEL;
        result = compute_longest_nonoverlapping_repeats(
            hashes, args->min_trace_length, args->alg);
        *args->operations_dest = std::move(hashes);
      } else {
        log_auto_trace.debug() << "Executing processing repeats meta task on "
                               << args->operations->size() << " operations.";
        // Otherwise, we have all the information to call the analysis directly.
        result = compute_longest_nonoverlapping_repeats(
            *args->operations, args->min_trace_length, args->alg);
      }
      *args->result = std::move(result);
    }

    TraceIdentifier::TraceIdentifier(
        TraceProcessingJobExecutor* executor_,
        TraceOccurrenceWatcher& watcher_,
        NonOverlappingAlgorithm repeats_alg_,
        uint64_t max_add_,
        uint64_t max_inflight_requests_,
        bool wait_on_async_job_,
        uint64_t min_trace_length_,
        uint64_t max_trace_length_
        )
        : executor(executor_),
          watcher(watcher_),
          repeats_alg(repeats_alg_),
          max_add(max_add_),
          min_trace_length(min_trace_length_),
          max_trace_length(max_trace_length_),
          max_in_flight_requests(max_inflight_requests_),
          wait_on_async_job(wait_on_async_job_) {}

    TraceIdentifier::Algorithm TraceIdentifier::parse_algorithm(const std::string &str) {
      if (str == "batched") {
        return TraceIdentifier::Algorithm::BATCHED;
      } else if (str == "multi-scale") {
        return TraceIdentifier::Algorithm::MULTI_SCALE;
      }
      return TraceIdentifier::Algorithm::NO_ALG;
    }

    const char *TraceIdentifier::algorithm_to_string(Algorithm alg) {
      switch (alg) {
        case TraceIdentifier::Algorithm::BATCHED: {
          return "batched";
        }
        case TraceIdentifier::Algorithm::MULTI_SCALE: {
          return "multi-scale";
        }
        default:
          return "NO_ALG";
      }
    }

    void TraceIdentifier::process(Murmur3Hasher::Hash hash, uint64_t opidx) {
      this->hashes.push_back(hash);
      // Dispatch to specializations of this class for actually launching
      // async jobs and managing the hashes vector.
      this->maybe_issue_repeats_job(opidx);

      // If there are no pending jobs, early exit.
      if (this->jobs_in_flight.size() == 0) return;

      // If we've hit the maximum number of inflight requests, then wait
      // on one of them to make sure that it gets processed.
      if (this->jobs_in_flight.size() == this->max_in_flight_requests) {
        this->jobs_in_flight.front().finish_event.wait();
      }

      // Query the completion queue to see if any of our jobs finished. If
      // we did a wait above, then we are expecting to be able to pop a
      // finished task here.
      RtEvent finish_event = this->executor->poll_pending_tasks(
          opidx, this->jobs_in_flight.size() == this->max_in_flight_requests);
      // Mark the corresponding in flight descriptor as completed.
      if (finish_event != RtEvent::NO_RT_EVENT) {
        for (auto& it : this->jobs_in_flight) {
          if (it.finish_event == finish_event) {
            it.completed = true;
            break;
          }
        }
        // We'll process at most one of the completed jobs so that
        // we don't pile up a bunch of work all at once.
        auto& finished = this->jobs_in_flight.front();
        if (finished.completed) {
          // Insert the received traces into the occurrence watcher.
          uint64_t count = 0;
          for (auto trace : finished.result) {
            // TODO (rohany): Deal with the maximum number of traces permitted in the trie.
            if (this->maybe_add_trace(finished.hashes, opidx, trace.start, trace.end)) {
              count++;
              // Only insert max_add traces at a time.
              if (count == this->max_add) {
                break;
              }
            }
          }
          this->jobs_in_flight.pop_front();
        }
      }
    }

    bool TraceIdentifier::maybe_add_trace(
      const std::vector<Murmur3Hasher::Hash> &hashes,
      uint64_t opidx,
      uint64_t start,
      uint64_t end
    ) {
      if ((end - start) < this->min_trace_length) return false;
      // Check that we aren't uint64_t max before attempting to do
      // some arithmetic that will overflow.
      if (this->max_trace_length != -1 &&
          (end - start) > (this->max_trace_length + this->min_trace_length)) {
        // If we're larger than the max trace length (plus a little slack),
        // then break up this trace into smaller pieces that we'll insert
        // into our watched data structures. First, insert a trace of the
        // maximum length, then insert the rest of the trace.
        bool first = maybe_add_trace(hashes, opidx, start, start + this->max_trace_length);
        bool second = maybe_add_trace(hashes, opidx, start + this->max_trace_length, end);
        return first || second;
      }
      auto istart = hashes.begin() + start;
      auto iend = hashes.begin() + end;
      TrieQueryResult query = this->watcher.query(istart, iend);
      // If we're trying to insert a trace that is either a prefix
      // of another recorded trace, or is already inside the set of
      // recorded traces, then there's nothing to do.
      if (query.prefix || query.contains) return false;
      // If the trace we're trying to insert is also not a superstring
      // of an existing trace, then this is the easy case where we can
      // just insert it and move on.
      if (!query.superstring) {
        this->watcher.insert(istart, iend, opidx);
        return true;
      }
      assert(query.superstring);
      // If the trace we're inserting is a superstring of another
      // string in the recorded set of traces, then splice out the
      // contained prefix and try to insert the rest of the trace.
      return this->maybe_add_trace(hashes, opidx, start + query.superstring_match, end);
    }

    BatchedTraceIdentifier::BatchedTraceIdentifier(
      uint64_t batchsize,
      TraceProcessingJobExecutor *executor,
      TraceOccurrenceWatcher &watcher,
      NonOverlappingAlgorithm repeats_alg,
      uint64_t max_add,
      uint64_t max_inflight_requests,
      bool wait_on_async_job,
      uint64_t min_trace_length,
      uint64_t max_trace_length
    ) : TraceIdentifier(
          executor,
          watcher,
          repeats_alg,
          max_add,
          max_inflight_requests,
          wait_on_async_job,
          min_trace_length,
          max_trace_length
        ),
        batchsize(batchsize)
    {
      // Reserve one extra place so that we can insert the sentinel
      // character at the end of the string.
      this->hashes.reserve(this->batchsize + 1);
    }

    void BatchedTraceIdentifier::maybe_issue_repeats_job(uint64_t opidx) {
      if (this->hashes.size() != this->batchsize) return;
      // Insert the sentinel token before sending the string off to the meta task.
      this->hashes.push_back(TraceIdentifier::SENTINEL);
      // Initialize a descriptor for the pending result.
      this->jobs_in_flight.push_back(InFlightProcessingRequest{});
      InFlightProcessingRequest& request = this->jobs_in_flight.back();
      // Move the existing vector of hashes into the descriptor, and
      // allocate a result space for the meta task to write into.
      request.hashes = std::move(this->hashes);
      InnerContext::AutoTraceProcessRepeatsArgs args(
          &request.hashes,
          &request.result,
          this->min_trace_length,
          this->repeats_alg
      );
      // Launch the meta task and record the finish event.
      request.finish_event = this->executor->enqueue_task(args, opidx, this->wait_on_async_job);
      // Finally, allocate a new vector to accumulate hashes into. As before,
      // allocate one extra spot for the sentinel hash.
      this->hashes = std::vector<Murmur3Hasher::Hash>();
      this->hashes.reserve(this->batchsize + 1);
    }

    MultiScaleBatchedTraceIdentifier::MultiScaleBatchedTraceIdentifier(
      uint64_t batchsize,
      uint64_t scale,
      TraceProcessingJobExecutor *executor,
      TraceOccurrenceWatcher &watcher,
      NonOverlappingAlgorithm repeats_alg,
      uint64_t max_add,
      uint64_t max_inflight_requests,
      bool wait_on_async_job,
      uint64_t min_trace_length,
      uint64_t max_trace_length
    ) : BatchedTraceIdentifier(
          batchsize,
          executor,
          watcher,
          repeats_alg,
          max_add,
          max_inflight_requests,
          wait_on_async_job,
          min_trace_length,
          max_trace_length
        ),
        scale(scale)
    { }

    void MultiScaleBatchedTraceIdentifier::maybe_issue_repeats_job(uint64_t opidx) {
      if (this->hashes.size() == this->batchsize) {
        // If we're launching an analysis on the entire buffer of operations,
        // then we'll do pretty much the same thing as the BatchedTraceIdentifier.
        BatchedTraceIdentifier::maybe_issue_repeats_job(opidx);
      } else if ((this->hashes.size() > 0) && (this->hashes.size() % this->scale == 0)) {
        // Otherwise, we are launching an analysis job on a portion of the
        // buffer, given by 2^(ruler function) of the current buffer size.
        // We can conveniently find this value by using the value of the
        // right-most set bit in the index.
        uint64_t index = this->hashes.size() / this->scale;
        uint64_t window_size = (index & ~(index - 1)) * this->scale;
        uint64_t start = this->hashes.size() - window_size;

        // Initialize a descriptor for the pending result.
        this->jobs_in_flight.push_back(InFlightProcessingRequest{});
        InFlightProcessingRequest& request = this->jobs_in_flight.back();
        // We construct the analysis arguments out of a pointer to the hashes
        // vector's data. We do this instead of passing a pointer to the vector
        // itself because in the hashes.size() == this->batchsize case, we will
        // move the vector out of `this` into another request, so the pointer
        // will be invalid. However, the pointer to the underlying data will not
        // be affected, and will remain live until the final job completes, Since
        // we are going to require that jobs occur in-order with the previous
        // completion event as a precondition, the memory will not get collected
        // out from underneath us.
        InnerContext::AutoTraceProcessRepeatsArgs args(
            this->hashes.data() + start,
            window_size,
            &request.hashes,
            &request.result,
            this->min_trace_length,
            this->repeats_alg
        );
        // We're going to be a little sneaky around re-using memory for the
        // async jobs, so we're going to make sure that our processing jobs
        // execute in order, because we'll have earlier jobs point to the
        // same memory that later jobs will also use.
        request.finish_event = this->executor->enqueue_task(
            args, opidx, this->wait_on_async_job, this->prev_job_completion);
        this->prev_job_completion = request.finish_event;
      }
    }

    TraceOccurrenceWatcher::TraceOccurrenceWatcher(
        TraceReplayer& replayer_, uint64_t visit_threshold_)
      : replayer(replayer_), visit_threshold(visit_threshold_) { }

    void TraceOccurrenceWatcher::process(Murmur3Hasher::Hash hash, uint64_t opidx) {
      this->active_pointers.emplace_back(this->trie.get_root(), opidx);
      // We'll avoid any allocations here by copying in pointers
      // as we process them.
      uint64_t copyidx = 0;
      for (uint64_t i = 0; i < this->active_pointers.size(); i++) {
        // Try to advance the pointer.
        TriePointer pointer = this->active_pointers[i];
        if (!pointer.advance(hash)) {
          continue;
        }
        this->active_pointers[copyidx] = pointer;
        copyidx++;
        // Check to see if the pointer completed.
        if (pointer.complete()) {
          // If this pointer corresponds to a completed trace, then we have
          // some work to do. First, increment the number of visits on the node.
          TrieNode<Murmur3Hasher::Hash, TraceMeta>* node = pointer.node;
          auto& value = node->get_value();
          // Visits only count if they occur at least len(trace) operations
          // after the previous visit. This avoids overcounting traces that
          // look like ABCABC with a count at each repetition of ABC rather
          // than at each occurrence of ABCABC.
          if (opidx - value.previous_visited_opidx >= pointer.depth) {
            value.visits++;
            value.previous_visited_opidx = opidx;
          }
          if (value.visits >= this->visit_threshold && !value.completed) {
            value.completed = true;
            std::vector<Murmur3Hasher::Hash> trace(pointer.depth);
            for (uint64_t j = 0; j < pointer.depth; j++) {
              assert(node != nullptr);
              trace[pointer.depth - j - 1] = node->get_token();
              node = node->get_parent();
            }
            // TODO (rohany): Do we need to think about superstrings here?
            if (!this->replayer.prefix(trace.begin(), trace.end())) {
              log_auto_trace.debug() << "Committing trace: "
                                     << value.opidx  << " of length: "
                                     << pointer.depth;
              this->replayer.insert(trace.begin(), trace.end(), opidx);
            }
          }
        }
      }
      // Erase the remaining elements from active_pointers.
      this->active_pointers.erase(this->active_pointers.begin() + copyidx, this->active_pointers.end());
    }

    bool TraceOccurrenceWatcher::TriePointer::advance(Murmur3Hasher::Hash token) {
      // We couldn't advance the pointer. Importantly, we can't check
      // node.end here, as this node could be the prefix of another
      // trace in the trie.
      auto it = this->node->get_children().find(token);
      if (it == this->node->get_children().end()) {
        return false;
      }
      // Otherwise, move down to the node's child.
      this->node = it->second;
      this->depth++;
      return true;
    }

    bool TraceOccurrenceWatcher::TriePointer::complete() {
      return this->node->get_end() && this->opidx >= this->node->get_value().opidx;
    }

    // Have to also provide declarations of the static variables.
    constexpr Murmur3Hasher::Hash TraceIdentifier::SENTINEL;
    constexpr double TraceReplayer::TraceMeta::R;
    constexpr double TraceReplayer::TraceMeta::SCORE_CAP_MULT;
    constexpr double TraceReplayer::TraceMeta::REPLAY_SCALE;
    constexpr double TraceReplayer::TraceMeta::IDEMPOTENT_VISIT_SCALE;

    void TraceReplayer::TraceMeta::visit(uint64_t opidx) {
      // First, compute the difference in trace lengths that
      // this trace was last visited at.
      uint64_t previous_visit = this->last_visited_opidx;
      uint64_t diff_in_traces = (opidx - previous_visit) / this->length;
      // Visits only count if they are at least 1 trace length away.
      if (diff_in_traces == 0) { return; }
      // Compute the new visit count by decaying the old visit count
      // and then adding one.
      this->decaying_visits = (pow(R, diff_in_traces) * this->decaying_visits) + 1;
      // If we visited this trace exactly len(trace) operations after
      // the previous visit, then we're able to replay this trace back-to-back,
      // which is nice to know for scoring. Check previous_visit != 0 to ensure
      // that we at least have one visit before counting idempotent visits.
      if (previous_visit != 0 && (opidx - previous_visit) == this->length) {
        uint64_t previous_idemp_visit = this->last_idempotent_visit_opidx;
        uint64_t idemp_diff = (opidx - previous_idemp_visit) / this->length;
        this->decaying_idempotent_visits = (pow(R, idemp_diff) * this->decaying_idempotent_visits) + 1;
        this->last_idempotent_visit_opidx = opidx;
      }
      this->last_visited_opidx = opidx;
    }

    double TraceReplayer::TraceMeta::score(uint64_t opidx) const {
      // Do a similar calculation as visit, where we decay the score
      // of the trace as if reading from opidx.
      // TODO (rohany): I'm not entirely convinced that this is necessary,
      //  because if we're computing the score of something, then it should
      //  have just been visited, i.e. it's score was just updated. However,
      //  this worked well in the simulator so I'll start with it before
      //  switching it up.
      uint64_t previous_visit = this->last_visited_opidx;
      uint64_t diff_in_traces = (opidx - previous_visit) / this->length;
      // Increase the visit count by 1 when computing the score so that
      // traces that haven't been visited before don't have a 0 score.
      // The initial score is num_visits * length.
      double score = ((pow(R, diff_in_traces) * this->decaying_visits) + 1) * this->length;
      // Next, we cap the score so that the first trace that gets replayed
      // doesn't get replayed forever.
      score = std::min(score, SCORE_CAP_MULT * ((double)this->length));
      // Then, increase the score a little bit if a trace has already been
      // replayed to favor replays.
      double capped_replays = std::max(std::min(REPLAY_SCALE, (double)this->replays), (double)1);
      double capped_idemp_visits = std::max(std::min(IDEMPOTENT_VISIT_SCALE, this->decaying_idempotent_visits), 1.0);
      return score * capped_replays * capped_idemp_visits;
    }

    void TraceReplayer::flush_buffer() {
      uint64_t num_ops = this->operations.size();
      this->operation_start_idx += num_ops;
      while (!this->operations.empty()) {
        auto& pending = this->operations.front();
        this->executor->issue_operation(pending.operation, pending.dependences);
        this->operations.pop();
      }
    }

    void TraceReplayer::flush_buffer(uint64_t opidx) {
      // If we've already advanced beyond this point, then there's nothing to do.
      if (this->operation_start_idx > opidx) {
        return;
      }
      uint64_t difference = opidx - this->operation_start_idx;
      this->operation_start_idx += difference;
      for (uint64_t i = 0; i < difference; i++) {
        auto& pending = this->operations.front();
        this->executor->issue_operation(pending.operation, pending.dependences);
        this->operations.pop();
      }
    }

    void TraceReplayer::replay_trace(uint64_t opidx, Legion::TraceID tid) {
      // If we've already advanced beyond this point, then there's nothing to do.
      // TODO (rohany): I don't think that this should happen when we're actually
      //  calling replay, but better safe than sorry.
      if (this->operation_start_idx > opidx) {
        return;
      }
      // Similar logic as flush_buffer, but issue a begin and end trace
      // around the flushed operations.
      this->executor->issue_begin_trace(tid);
      uint64_t difference = opidx - this->operation_start_idx;
      this->operation_start_idx += difference;
      uint64_t traced_ops = 0;
      for (uint64_t i = 0; i < difference; i++) {
        auto& pending = this->operations.front();
        this->executor->issue_operation(pending.operation, pending.dependences);
        if (!is_operation_ignorable_in_traces(pending.operation)) traced_ops++;
        this->operations.pop();
      }
      log_auto_trace.info() << "Replaying trace " << tid
                            << " of length "
                            << traced_ops
                            << " at opidx: " << opidx;
      this->executor->issue_end_trace(tid);
    }

    bool TraceReplayer::WatchPointer::advance(Murmur3Hasher::Hash token) {
      // We couldn't advance the pointer. Importantly, we can't check
      // node.end here, as this node could be the prefix of another
      // trace in the trie.
      auto it = this->node->get_children().find(token);
      if (it == this->node->get_children().end()) {
        return false;
      }
      // Otherwise, move down to the node's child.
      this->node = it->second;

      // If we've hit the end of a string, mark it as visited and update the score.
      if (this->node->get_end() && this->opidx >= this->node->get_value().opidx) {
        this->node->get_value().visit(opidx);
      }
      return true;
    }

    bool TraceReplayer::CommitPointer::advance(Murmur3Hasher::Hash token) {
      // We couldn't advance the pointer. Importantly, we can't check
      // node.end here, as this node could be the prefix of another
      // trace in the trie.
      auto it = this->node->get_children().find(token);
      if (it == this->node->get_children().end()) {
        return false;
      }
      // Otherwise, move down to the node's child.
      this->node = it->second;
      this->depth++;
      return true;
    }

    bool TraceReplayer::CommitPointer::complete() {
      // By ensuring that we don't insert traces that are superstrings
      // of existing traces in the TraceOccurrenceWatcher, this property
      // should be preserved as traces migrate into the TraceReplayer,
      // which relies on a completed pointer as not having any more
      // pending operations to be waiting for.
      if (this->node->get_end()) {
        assert(this->node->get_children().size() == 0);
      }
      return this->node->get_end() && this->opidx >= this->node->get_value().opidx;
    }

    TraceID TraceReplayer::CommitPointer::replay(OperationExecutor* exec) {
      auto& value = this->node->get_value();
      TraceID tid;
      if (value.replays == 0) {
        // If we haven't replayed this trace before, generate a fresh id.
        tid = exec->get_fresh_trace_id();
        value.tid = tid;
      } else {
        tid = value.tid;
      }
      value.replays++;
      return tid;
    }

    double TraceReplayer::CommitPointer::score(uint64_t opidx) {
      return this->node->get_value().score(opidx);
    }

    void TraceReplayer::flush(uint64_t opidx) {
      // We have to flush all active pointers from the trie, and
      // them attempt to launch traces for any completed pointers.
      // First, clear the vectors of active pointers.
      this->active_watching_pointers.clear();
      this->active_commit_pointers.clear();
      // If we have no completed pointers, flush all pending operations and
      // early exit.
      if (this->completed_commit_pointers.size() == 0) {
        this->flush_buffer();
        return;
      }

#ifdef DEBUG_LEGION
      assert(std::is_sorted(this->completed_commit_pointers.begin(), this->completed_commit_pointers.end()));
#endif
      // Now that we have some (sorted) completed pointers,  issue them.
      for (auto& pointer : this->completed_commit_pointers) {
        // If we're considering a pointer that starts earlier than the
        // pending set of operations, then that trace is behind us. So
        // we just continue onto the next trace.
        if (pointer.get_opidx() < this->operation_start_idx) {
          continue;
        }
        // Now, flush the buffer up until the start of this trace.
        this->flush_buffer(pointer.get_opidx());
        // Finally, we can issue the trace.
        TraceID tid = pointer.replay(this->executor);
        this->replay_trace(pointer.get_opidx() + pointer.get_length(), tid);
      }
      this->completed_commit_pointers.clear();
      // Flush all remaining operations.
      this->flush_buffer();
    }

    void TraceReplayer::process(
      Legion::Internal::Operation *op,
      const std::vector<StaticDependence>* dependence,
      Murmur3Hasher::Hash hash,
      uint64_t opidx
    ) {
      this->operations.emplace(op, dependence);
      // Update all watching pointers. This is very similar to the advancing
      // of pointers in the TraceOccurrenceWatcher.
      this->active_watching_pointers.emplace_back(this->trie.get_root(), opidx);
      // Avoid a reallocation in the same way by copying in place.
      uint64_t copyidx = 0;
      for (uint64_t i = 0; i < this->active_watching_pointers.size(); i++) {
        WatchPointer pointer = this->active_watching_pointers[i];
        if (!pointer.advance(hash)) {
          continue;
        }
        this->active_watching_pointers[copyidx] = pointer;
        copyidx++;
      }
      // Erase the remaining unused elements.
      this->active_watching_pointers.erase(this->active_watching_pointers.begin() + copyidx, this->active_watching_pointers.end());

      // Now update all the commit pointers. This process is more tricky, as
      // we have to actually decide to flush operations through the dependence
      // queue as we match traces. Additionally, we have to manage heuristics
      // around which traces we should take.
      this->active_commit_pointers.emplace_back(this->trie.get_root(), opidx);
      copyidx = 0;
      for (uint64_t i = 0; i < this->active_commit_pointers.size(); i++) {
        CommitPointer pointer = this->active_commit_pointers[i];
        if (!pointer.advance(hash)) {
          continue;
        }
        if (pointer.complete()) {
          // Add the new completed pointer to the vector of
          // completed_commit_pointers. We calculate the score of
          // the pointer at the current opidx and use that score
          // for the rest of the operations on the pointer. We must
          // maintain the sortedness of completed_commit_pointers, so we
          // use upper_bound + insert to insert the pointer into the right
          // place. A future investigation can see if a std::set is a better
          // data structure, but the controlled memory usage + cache behavior
          // of the vector is likely better on the small sizes that
          // completed_commit_pointers should grow to.
#ifdef DEBUG_LEGION
          assert(std::is_sorted(this->completed_commit_pointers.begin(), this->completed_commit_pointers.end()));
#endif
          FrozenCommitPointer frozen(pointer, opidx);
          this->completed_commit_pointers.insert(
            std::upper_bound(
              this->completed_commit_pointers.begin(),
              this->completed_commit_pointers.end(),
              frozen
            ),
            frozen
          );
        } else {
          this->active_commit_pointers[copyidx] = pointer;
          copyidx++;
        }
      }
      // Erase the rest of the active pointers.
      this->active_commit_pointers.erase(this->active_commit_pointers.begin() + copyidx, this->active_commit_pointers.end());

      // Find the minimum opidx of the active and completed pointers.
      uint64_t earliest_active = std::numeric_limits<uint64_t>::max();
      uint64_t earliest_completed = std::numeric_limits<uint64_t>::max();
      for (auto& pointer : this->active_commit_pointers) {
        earliest_active = std::min(earliest_active, pointer.get_opidx());
      }
      for (auto& pointer : this->completed_commit_pointers) {
        earliest_completed = std::min(earliest_completed, pointer.get_opidx());
      }
      uint64_t earliest_opidx = std::min(earliest_active, earliest_completed);

      // First, flush all operations until the earliest_opidx, as there is
      // nothing we are considering before there. If there are no active
      // or completed operations at all, then we just flush the entire buffer.
      if (this->active_commit_pointers.empty() && this->completed_commit_pointers.empty()) {
        this->flush_buffer();
      } else {
        this->flush_buffer(earliest_opidx);
      }

      // Now, we have to case on what combination of pointers are available.
      if (this->active_commit_pointers.empty() && this->completed_commit_pointers.empty()) {
        // There's nothing to do if we don't have any of either pointer left.
        return;
      } else if (this->active_commit_pointers.empty()) {
        // In this case, there are only completed pointers. We'll try to flush
        // through as many operations as we can. The heuristic is to take
        // traces ordered by score. This hueuristic can lead to suboptimal
        // trace replay, for example if the operation stream is AB and we have
        // completed traces [A, B] but B has a higher score, we'll issue A without
        // actually replaying that trace. Doing this seems to require some
        // fancier logic with interval trees or something, so we'll stick to
        // the simpler piece. completed_commit_pointers should already be
        // sorted to have the highest scoring traces at the front.
#ifdef DEBUG_LEGION
        assert(std::is_sorted(this->completed_commit_pointers.begin(), this->completed_commit_pointers.end()));
#endif
        for (auto& pointer : this->completed_commit_pointers) {
          // If we're considering a pointer that starts earlier than the
          // pending set of operations, then that trace is behind us. So
          // we just continue onto the next trace.
          if (pointer.get_opidx() < this->operation_start_idx) {
            continue;
          }
          // Now, flush the buffer up until the start of this trace.
          this->flush_buffer(pointer.get_opidx());
          // Finally, we can issue the trace.
          TraceID tid = pointer.replay(this->executor);
          this->replay_trace(pointer.get_opidx() + pointer.get_length(), tid);
        }
        // The set of completed pointers is now empty.
        this->completed_commit_pointers.clear();
        // At this point, we don't have any completed or active pointers,
        // so flush any remaining operations.
        this->flush_buffer();
      } else if (this->completed_commit_pointers.empty()) {
        // There are no completed pointers, so there's nothing left to do,
        // as we already flushed all possible pending operations.
        return;
      } else {
        // In this case, we have both completed and active pointers. What we actually
        // do will change depending on what the overlaps between our completed and
        // active pointers actually are.
        if (earliest_completed < earliest_active) {
          // In this case, we have some completed pointers that we could potentially
          // replay behind our active pointers. We're going to take a heuristic here
          // where we only flush completed pointers that do not overlap with any
          // active pointers. This biases us towards longer traces when possible,
          // and makes the replay resilient against different kinds of traces
          // being inserted, such as AB, when the trie already contains BC.
#ifdef DEBUG_LEGION
          assert(std::is_sorted(this->completed_commit_pointers.begin(), this->completed_commit_pointers.end()));
#endif
          uint64_t cutoff_opidx = earliest_active;
          uint64_t pending_completion_cutoff = std::numeric_limits<uint64_t>::max();
          uint64_t copyidx = 0;
          for (uint64_t i = 0; i < this->completed_commit_pointers.size(); i++) {
            auto pointer = this->completed_commit_pointers[i];
            // If this completed pointer spans into an active pointer, then we need
            // to save it for later.
            if (pointer.get_opidx() + pointer.get_length() >= cutoff_opidx) {
              this->completed_commit_pointers[copyidx] = pointer;
              copyidx++;
              // If we decide to skip this completed pointer because it overlaps
              // with an active pointer, we shouldn't replay any completed pointers
              // that overlap with this good pointer, as it scored higher.
              pending_completion_cutoff = std::min(pending_completion_cutoff, pointer.get_opidx());
              continue;
            }
            // As before, any pointers that we are already past can be ignored.
            if (pointer.get_opidx() < this->operation_start_idx) {
              continue;
            }
            // Lastly, make sure that this completed pointer doesn't invalidate
            // a completed pointer that was re-queued with a better score.
            if (pointer.get_opidx() + pointer.get_length() >= pending_completion_cutoff) {
              this->completed_commit_pointers[copyidx] = pointer;
              copyidx++;
              continue;
            }
            // Here, we can finally replay the trace.
            this->flush_buffer(pointer.get_opidx());
            TraceID tid = pointer.replay(this->executor);
            this->replay_trace(pointer.get_opidx() + pointer.get_length(), tid);
          }
          // Clear the remaining invalid completions.
          this->completed_commit_pointers.erase(this->completed_commit_pointers.begin() + copyidx, this->completed_commit_pointers.end());

#ifdef DEBUG_LEGION
          // Since we iterated through completed_commit_pointers in sorted order
          // to construct the new vector, it should still be sorted.
          assert(std::is_sorted(this->completed_commit_pointers.begin(), this->completed_commit_pointers.end()));
          // Since we waited to not cut off any active pointers, there should not
          // be any invalid active pointers.
          for (auto& pointer : this->active_commit_pointers) {
            assert(pointer.get_opidx() >= this->operation_start_idx);
          }
#endif
        } else if (earliest_completed > earliest_active) {
          // There are active pointers behind our earliest completed
          // pointer, so there's no point at even looking at the completed
          // pointers.
          return;
        } else {
          // We should never be in the case where an active and completed pointer
          // are starting at the same opidx.
          // TODO (rohany): This can actually happen if we allow for prefixes like
          //  the comment earlier above suggests. We'll deal with that when we
          //  get there.
          assert(false);
        }
      }
    }

    void TraceReplayer::process_trace_noop(Legion::Internal::Operation *op) {
      assert(is_operation_ignorable_in_traces(op));
      // If the operation is a noop during traces, then the replayer
      // takes a much simpler process. In particular, none of the pointers
      // advance or are cancelled, but their depth increases to account
      // for the extra operation. Do a special advance on each active
      // commit pointer.
      this->operations.emplace(op, nullptr);
      for (auto& pointer : this->active_commit_pointers) {
        pointer.advance_for_trace_noop();
      }

      // Because this operation does not invalidate any pointers,
      // we don't always need to compute a minumum and flush the
      // head of the buffer up until the minimum. This is because
      // a previous operation already did that for the active pointers,
      // and this operation does not create any new active or complete
      // pointers. So the addition of this operation cannot require
      // re-flushing the head of the buffer. However, to make the
      // processing of these operations slightly more eager, we'll
      // flush them through if there aren't any active pointers,
      // rather than waiting for the next operation to come along.
      if (this->active_commit_pointers.empty() && this->completed_commit_pointers.empty()) {
        this->flush_buffer();
      }
    }

  };
};
