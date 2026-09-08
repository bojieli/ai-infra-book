#include "pipellm.h"
#include "hack.h"
#include <dlfcn.h>
#include <iostream>
#include <cstdio>
#include <mutex>
#include <algorithm>
#include <thread>
#include <cstring>
#include <chrono>
#include <cassert>
#include <cuda.h>

static bool enable_encrypt = false;
static bool enable_decrypt = false;
size_t encrypt_magic_sz = 0xabcde;
size_t decrypt_magic_sz = 0xabcde;
std::map<EVP_CIPHER_CTX *, std::shared_ptr<encrypt_metadata>> m_ctx_metadata;
std::map<size_t, EVP_CIPHER_CTX *> m_magic_encctx;
std::set<size_t> s_magic;
std::map<EVP_CIPHER_CTX *, std::shared_ptr<decrypt_metadata>> m_ctx_dmetadata;
std::map<size_t, EVP_CIPHER_CTX *> m_magic_decctx;
std::set<size_t> s_magic_dec;
constexpr static int encrypt_workers_num_max = 16;
static int encrypt_workers_num = 1;
static int encrypt_workers_per_commit = 1;
constexpr static int decrypt_workers_num_max = 2;
static int decrypt_workers_num = 1;
int memcpy_thread_num = 1;
int commit_workers_num = encrypt_workers_num / encrypt_workers_per_commit;
encrypt_worker_entry *encrypt_worker_entrys[encrypt_workers_num_max];
std::thread *encrypt_worker_threads[encrypt_workers_num_max];
std::thread *commit_worker_threads[encrypt_workers_num_max];
decrypt_worker_entry *decrypt_worker_entrys[decrypt_workers_num_max];
std::thread *decrypt_worker_threads[decrypt_workers_num_max];
std::thread *decrypt_manager_threads[decrypt_workers_num_max];

Predictor predictor;
void sync_predictor();

HOOK_C_API HOOK_DECL_EXPORT cudaError_t cudaDeviceSynchronize()
{
    predictor.lock();
    sync_predictor();
    predictor.unlock();

    return real_cudaDeviceSynchronize();
}

HOOK_C_API HOOK_DECL_EXPORT cudaError_t cudaStreamSynchronize(cudaStream_t stream)
{
    predictor.lock();
    sync_predictor();
    predictor.unlock();

    return real_cudaStreamSynchronize(stream);
}

HOOK_C_API HOOK_DECL_EXPORT cudaError_t cudaStreamWaitEvent(cudaStream_t stream, cudaEvent_t event, unsigned int flags)
{
    predictor.lock();
    sync_predictor();
    predictor.unlock();

    return real_cudaStreamWaitEvent(stream, event, flags);
}

static bool first = 0;
static inline void init_encrypt_ctx(enum cudaMemcpyKind kind, cudaStream_t stream)
{
    if (!first) {
        first = true;
        // Get envs
        auto enable_encrypt_env = std::getenv("PIPELLM_ENABLE_ENCRYPT");
        if (enable_encrypt_env != nullptr) {
            enable_encrypt = std::atoi(enable_encrypt_env) != 0;
        }
        auto enable_decrypt_env = std::getenv("PIPELLM_ENABLE_DECRYPT");
        if (enable_decrypt_env != nullptr) {
            enable_decrypt = std::atoi(enable_decrypt_env) != 0;
        }
        auto encrypt_workers_num_env = std::getenv("PIPELLM_ENCRYPT_WORKERS");
        if (encrypt_workers_num_env != nullptr) {
            encrypt_workers_num = std::min(encrypt_workers_num_max, std::atoi(encrypt_workers_num_env));
        }
        auto encrypt_workers_per_commit_env = std::getenv("PIPELLM_ENCRYPT_WORKERS_PER_COMMIT");
        if (encrypt_workers_per_commit_env != nullptr) {
            encrypt_workers_per_commit = std::min(encrypt_workers_num, std::atoi(encrypt_workers_per_commit_env));
            commit_workers_num = encrypt_workers_num / encrypt_workers_per_commit;
        }
        auto decrypt_workers_num_env = std::getenv("PIPELLM_DECRYPT_WORKERS");
        if (decrypt_workers_num_env != nullptr) {
            decrypt_workers_num = std::min(decrypt_workers_num_max, std::atoi(decrypt_workers_num_env));
        }
        auto memcpy_thread_num_env = std::getenv("PIPELLM_MEMCPY_THREAD_NUM");
        if (memcpy_thread_num_env != nullptr) {
            memcpy_thread_num = std::min(16, std::atoi(memcpy_thread_num_env));
        }
        auto bind_core_env = std::getenv("PIPELLM_BIND_CORE");
        if (bind_core_env != nullptr) {
            auto core_id = std::atoi(bind_core_env);
            bind_core(core_id);
        }
        if (enable_encrypt) {
            for (int i = 0; i < commit_workers_num; i++) {
                auto worker_entry = new encrypt_worker_entry;
                encrypt_worker_entrys[i] = worker_entry;
                worker_entry->id = i;
                auto magic_sz = encrypt_magic_sz + i;
                worker_entry->magic_sz = magic_sz;
                worker_entry->commit_init_done = false;
                worker_entry->encrypt_workers_per_commit = encrypt_workers_per_commit;
                s_magic.insert(magic_sz);
                commit_worker_threads[i] = new std::thread(commit_worker, worker_entry);
                // Sequential initialization to avoid race condition
                while (!worker_entry->commit_init_done);
                for (int j = 0; j < encrypt_workers_per_commit; j++) {
                    worker_entry->enc_init_done = false;
                    worker_entry->local_id = j;
                    encrypt_worker_threads[i * encrypt_workers_per_commit + j] = new std::thread(encrypt_worker, worker_entry);
                    while (!worker_entry->enc_init_done);
                }
            }
        }
        if (enable_decrypt) {
            for (int i = 0; i < decrypt_workers_num; i++) {
                auto worker_entry = new decrypt_worker_entry;
                decrypt_worker_entrys[i] = worker_entry;
                worker_entry->id = i;
                auto magic_sz = decrypt_magic_sz + i;
                worker_entry->magic_sz = magic_sz;
                worker_entry->enc_worker_entry = encrypt_worker_entrys[i];
                worker_entry->dec_init_done = false;
                worker_entry->commit_init_done = false;
                s_magic_dec.insert(magic_sz);
                decrypt_manager_threads[i] = new std::thread(decrypt_manager, worker_entry);
                while (!worker_entry->commit_init_done);
                decrypt_worker_threads[i] = new std::thread(decrypt_worker, worker_entry);
                while (!worker_entry->dec_init_done);
            }
        }
    }
}

void assign_to_workers(void *dst, const void *src, size_t count, bool decrypt = false, bool predict = true, bool commit = false, bool update_predict_iv = false, bool batch_commit = false)
{
    // auto base = src;
    const char *src_char = (const char *)src;
    char *dst_char = (char *)dst;
    size_t div = (count + commit_workers_num - 1) / commit_workers_num;
    div = (div + block_unit - 1) / block_unit * block_unit;

    for (int i = 0; i < commit_workers_num; i++) {
        auto worker_entry = encrypt_worker_entrys[i];
        auto sz = std::min(count, div);
        if (predict) {
            encryption_task task;
            task.src = src_char;
            task.size = sz;
            task.iv_increment = 32;
            {
                std::lock_guard<std::mutex> lock(worker_entry->lock);
                worker_entry->enc_tasks.push_back(task);
            }
        } else {
            commit_task task;
            worker_entry->commit = true;
            task.enc_task.src = src_char;
            task.enc_task.size = sz;
            task.dst = dst_char;
            task.using_predict = commit;
            task.update_predict_iv = update_predict_iv;
            {
                std::lock_guard<std::mutex> lock(worker_entry->lock);
                worker_entry->commit_tasks.push_back(task);
            }
        }
        src_char += sz;
        dst_char += sz;
        count -= sz;
        if (count == 0) {
            break;
        }
    }
}

void sync_predictor()
{
    // Caller must hold the predictor's lock
    if (!first || !enable_encrypt) return;
    assert(predictor.locking());
    if (!predictor.pending_commit.empty()) {
        assert(encrypt_workers_num == 1);
        {
            std::lock_guard<std::mutex> lock(encrypt_worker_entrys[0]->lock);
            encrypt_worker_entrys[0]->commit = true;
            for (auto &task: predictor.pending_commit) {
                commit_task task0;
                task0.enc_task.src = task.first;
                task0.enc_task.size = task.second.second;
                task0.dst = task.second.first;
                task0.using_predict = true;
                task0.update_predict_iv = false;
                encrypt_worker_entrys[0]->commit_tasks.push_back(task0);
            }
        }
        predictor.pending_commit.clear();
    }

    if (!predictor.pending_decrypt.empty()) {
        assert(decrypt_workers_num == 1);
        {
            std::lock_guard<std::mutex> lock(decrypt_worker_entrys[0]->lock);
            for (auto &task: predictor.pending_decrypt) {
                decrypt_worker_entrys[0]->dec_tasks.push_back(task);
            }
        }
        predictor.pending_decrypt.clear();
    }
    for (int i = 0; i < commit_workers_num; i++) {
        while (1) {
            {
                if (encrypt_worker_entrys[i]->commit == false) {
                    break;
                }
            }
        }
    }
    predictor.pending_commit.clear();
}

HOOK_C_API HOOK_DECL_EXPORT cudaError_t cudaMemcpyAsync(void *dst, const void *src, size_t count,
                                                        enum cudaMemcpyKind kind, cudaStream_t stream)
{
    init_encrypt_ctx(kind, stream);
    if (enable_encrypt && kind == cudaMemcpyHostToDevice && count >= encrypt_threshold_sz) {
        predictor.lock();
        if (predictor.read_only_swap_profiled) {
            auto &record = predictor.read_only_swap_record;
            bool hit = src == record[predictor.read_only_swap_cur_idx].first &&
                       count == record[predictor.read_only_swap_cur_idx].second;
            if (!hit) {
                // Not hit
                printf("Not hit\n");
                assert(0);
                predictor.unlock();
                auto ret = real_cudaMemcpyAsync((char *)dst, (char *)src, count, kind, stream);
                return ret;
            }
            // Hit read-only swap, prepare for next encryption
            predictor.read_only_swap_cur_idx = (predictor.read_only_swap_cur_idx + 1)
                                                % predictor.read_only_swap_record.size();
            predictor.read_only_swap_pred_idx = (predictor.read_only_swap_pred_idx + 1)
                                                % predictor.read_only_swap_record.size();
            auto &entry = record[predictor.read_only_swap_pred_idx];
            assign_to_workers(nullptr, entry.first, entry.second, false, true, false, false);
            assign_to_workers(dst, src, count, false, false, true, false);
            predictor.unlock();
            return cudaSuccess;
        } else if (predictor.other_swap_set.find(std::make_pair(src, count)) != predictor.other_swap_set.end()) {
            // Hit other swaps
            predictor.other_swap_set.erase(std::make_pair(src, count));
            assign_to_workers(dst, src, count, false, false, true, false);
            predictor.unlock();
	        return cudaSuccess;
        } else if (!predictor.read_only_swap_profiled) {
            auto &record = predictor.read_only_swap_record;
            record.push_back(std::make_pair(src, count));
            auto size = record.size();
            // Send this one to encrypt workers
            assign_to_workers(dst, src, count, false, true, false, false);
            assign_to_workers(dst, src, count, false, false, true, false);
            sync_predictor();

            bool found = true;
            const int repeat = 32;
            if (size < repeat * 2 || (size % 2 == 1)) {
                found = false;
            } else {
                auto mid = size / 2;
                for (int i = 0; i < size / 2; i++) {
                    if (record[i] != record[mid + i]) {
                        found = false;
                        break;
                    }
                }
            }

            if (found) {
                // Pattern found
                for (int i = 0; i < size / 2; i++) {
                    record.pop_back();
                }
                predictor.read_only_swap_profiled = true;
                predictor.read_only_swap_cur_idx = (size / 2) % record.size();
                auto &entry = record[predictor.read_only_swap_cur_idx];
                assign_to_workers(nullptr, entry.first, entry.second, false, true, false, false);
                predictor.read_only_swap_pred_idx = predictor.read_only_swap_cur_idx;

                predictor.read_only_swap_pred_idx = (predictor.read_only_swap_cur_idx + 1)
                                                % predictor.read_only_swap_record.size();
                auto &entry1 = record[predictor.read_only_swap_pred_idx];
                assign_to_workers(nullptr, entry1.first, entry1.second, false, true, false, false);
            }
            predictor.unlock();
            return cudaSuccess;
        }
    }
    if (enable_decrypt && kind == cudaMemcpyDeviceToHost && count >= decrypt_threshold_sz && count <= decrypt_threshold_top) {
        predictor.lock();
        predictor.other_swap_set.insert(std::make_pair(dst, count));
        decryption_task task;
        task.src = src;
        task.size = count;
        task.dst = dst;
        predictor.pending_decrypt.push_back(task);
        predictor.unlock();
	    return cudaSuccess;
    }
    auto ret = real_cudaMemcpyAsync(dst, src, count, kind, stream);
    return ret;
}