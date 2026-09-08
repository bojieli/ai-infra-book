#include "pipellm.h"
#include "hack.h"
#include <unistd.h>
#include <cstring>
#include <cassert>

void encrypt_worker(void *entry)
{
    auto x = (struct encrypt_worker_entry *)entry;
    auto worker_id = x->id;
    auto local_id = x->local_id;
    bind_core((x->encrypt_workers_per_commit + 1) * worker_id + local_id + 1);

    std::deque<encryption_entry *> enc_entries;

    unsigned char encrypt_key[key_length];
    unsigned char encrypt_init_iv[iv_length];
    unsigned char iv[iv_length];
    auto enc_ctx = m_magic_encctx[x->magic_sz];
    auto &enc_metadata = *m_ctx_metadata.at(enc_ctx);
    memcpy(encrypt_key, enc_metadata.key, key_length);
    memcpy(encrypt_init_iv, enc_metadata.init_iv, iv_length);
    auto fake_src = new unsigned char [1 << 20];

    x->enc_init_done = true;
    auto local_ctx = real_EVP_CIPHER_CTX_new();
    while (1) {
        while (x->enc_entries[local_id].empty()) {
            // Polling 1 us
            constexpr int polling_us = 1;
            auto start = std::chrono::system_clock::now();
            while (1) {
                auto end = std::chrono::system_clock::now();
                if (std::chrono::duration_cast<std::chrono::microseconds>(end - start).count() >= polling_us) {
                    break;
                }
            }
        }

        if (!x->enc_entries[local_id].empty()){
            std::lock_guard<std::mutex> lock(x->enc_lock[local_id]);
            enc_entries = x->enc_entries[local_id];
            x->enc_entries[local_id].clear();
        }

        for (auto &entry : enc_entries) {
            int updated_len;
            next_iv(encrypt_init_iv, iv, entry->iv_offset);
            real_EVP_EncryptInit_ex(local_ctx, EVP_aes_256_gcm(), 0, encrypt_key, iv);
            assert(real_EVP_EncryptUpdate(local_ctx, entry->buffer, &updated_len, (unsigned char*)entry->src, entry->size) == 1);
            real_EVP_EncryptFinal_ex(local_ctx, entry->buffer + updated_len, &updated_len);
            real_EVP_CIPHER_CTX_ctrl(local_ctx, EVP_CTRL_GCM_GET_TAG, 16, entry->tag);
            entry->busy = false;
        }
        enc_entries.clear();
    }
}

void commit_worker(void *entry)
{
    auto x = (struct encrypt_worker_entry *)entry;
    auto worker_id = x->id;
    auto encrypt_workers_per_commit = x->encrypt_workers_per_commit;
    bind_core((encrypt_workers_per_commit + 1) * worker_id);
    CUcontext cuda_ctx;
    CUdevice dev;
    cudaStream_t stream;
    void *fake_src, *fake_dst;
    assert(cuInit(0) == CUDA_SUCCESS);
    assert(cuDeviceGet(&dev, 0) == CUDA_SUCCESS);
    assert(cuCtxCreate(&cuda_ctx, CU_CTX_SCHED_SPIN, dev) == CUDA_SUCCESS);
    assert(cuCtxPushCurrent(cuda_ctx) == CUDA_SUCCESS);
    assert(real_cudaStreamCreateWithFlags(&stream, cudaStreamNonBlocking) == cudaSuccess);
    assert(real_cudaMallocHost(&fake_src, 1ul << 30) == cudaSuccess);
    sleep(1);
    void *dev_buffer;
    real_cudaMalloc(&dev_buffer, x->magic_sz);
    real_cudaMemcpyAsync(dev_buffer, fake_src, x->magic_sz, cudaMemcpyHostToDevice, stream);
    real_cudaMemcpyAsync(dev_buffer, fake_src, x->magic_sz, cudaMemcpyHostToDevice, stream);
    real_cudaDeviceSynchronize();
    real_cudaFree(dev_buffer);
    x->commit_init_done = true;

    auto enc_ctx = m_magic_encctx[x->magic_sz];
    auto &enc_metadata = *m_ctx_metadata.at(enc_ctx);
    enc_metadata.commit_worker_id = worker_id;
    x->predict_iv_offset = enc_metadata.cur_iv_offset + 1;

    std::deque<encryption_task> enc_tasks;
    std::deque<commit_task> commit_tasks;
    std::deque<commit_task> remain_commit_tasks;
    std::vector<std::pair<const void *, size_t>> predict_vec;

    while (1) {
        while (x->commit_tasks.empty() && x->enc_tasks.empty() && commit_tasks.empty()) {
            // Polling 1 us
            constexpr int polling_us = 1;
            auto start = std::chrono::system_clock::now();
            while (1) {
                auto end = std::chrono::system_clock::now();
                if (std::chrono::duration_cast<std::chrono::microseconds>(end - start).count() >= polling_us) {
                    break;
                }
            }
        }

        if (!x->commit_tasks.empty() || !x->enc_tasks.empty()){
            std::lock_guard<std::mutex> lock(x->lock);
            for (auto &task : x->commit_tasks) {
                commit_tasks.push_back(task);
            }
            x->commit_tasks.clear();
            enc_tasks = x->enc_tasks;
            x->enc_tasks.clear();
        }

        for (auto &task : enc_tasks) {
            {
                auto count = task.size;
                auto base = task.src;
                x->predict_iv_offset += task.iv_increment;

                size_t div = (count + encrypt_workers_per_commit - 1) / encrypt_workers_per_commit;
                div = (div + block_unit - 1) / block_unit * block_unit;
                auto blocks = (div + block_unit - 1) / block_unit;
                predict_vec.push_back(std::make_pair(task.src, task.size));
                for (int i = 0; i < encrypt_workers_per_commit; i++) {
                    for (int j = 0; j < blocks; j++) {
                        int updated_len;
                        auto size = std::min(count, block_unit);
                        auto enc_entry = new encryption_entry;
                        enc_entry->src = base;
                        enc_entry->buffer = enc_metadata.allocator.alloc();
                        enc_entry->size = size;
                        enc_entry->busy = true;
                        enc_entry->iv_offset = x->predict_iv_offset;
                        enc_metadata.m_iv_encentry.insert(std::make_pair(x->predict_iv_offset, enc_entry));
                        {
                            // TODO: batch insert into enc_entries
                            std::lock_guard<std::mutex> lock(x->enc_lock[i]);
                            x->enc_entries[i].push_back(enc_entry);
                        }
                        x->predict_iv_offset++;
                        base += size;
                        count -= size;
                        if (count == 0) break;
                    }
                    if (count == 0) break;
                }

            }
        }
        enc_tasks.clear();

        for (auto &task : commit_tasks) {
            if (task.using_predict) {
                // Wait until in set
                {
                    bool found = false;
                    for (auto x = predict_vec.begin(); x != predict_vec.end(); ++x) {
                        if (*x == std::make_pair(task.enc_task.src, task.enc_task.size)) {
                            found = true;
                            predict_vec.erase(x);
                            break;
                        }
                    }
                    if (!found) {
                        remain_commit_tasks.push_back(task);
                        continue;
                    }
                }

                // Sending NOPs
                size_t cur_predict_iv_offset = enc_metadata.m_iv_encentry.begin()->first;
                assert(cur_predict_iv_offset >= enc_metadata.cur_iv_offset);
                while (cur_predict_iv_offset > enc_metadata.cur_iv_offset + 1) {
                    auto ret = real_cudaMemcpyAsync(task.dst, fake_src, 1, cudaMemcpyHostToDevice, stream);
                    if (ret != cudaSuccess) {
                        printf("cudaMemcpyAsync failed with %d\n", ret);
                        assert(0);
                    }
                }
                auto ret = real_cudaMemcpyAsync(task.dst, fake_src, task.enc_task.size, cudaMemcpyHostToDevice, stream);
                if (ret != cudaSuccess) {
                    printf("cudaMemcpyAsync failed with %d\n", ret);
                    assert(0);
                }
            } else {
                assert(real_cudaMemcpyAsync(task.dst, task.enc_task.src, task.enc_task.size, cudaMemcpyHostToDevice, stream) == cudaSuccess);
            }
        }

        commit_tasks = remain_commit_tasks;
        remain_commit_tasks.clear();
        x->commit = false;
    }
}

void decrypt_worker(void *entry)
{
    auto x = (struct decrypt_worker_entry *)entry;
    auto worker_id = x->id;
    bind_core(2 * worker_id + 4 + 1);
    
    std::deque<decryption_entry *> dec_entries;
    unsigned char decrypt_key[key_length];

    auto dec_ctx = m_magic_decctx[x->magic_sz];
    auto &dec_metadata = *m_ctx_dmetadata.at(dec_ctx);

    memcpy(decrypt_key, dec_metadata.key, key_length);

    x->dec_init_done = true;
    auto local_ctx = real_EVP_CIPHER_CTX_new();
    while (1) {
        while (x->dec_entries.empty()) {
            // Polling 1 us
            constexpr int polling_us = 1;
            auto start = std::chrono::system_clock::now();
            while (1) {
                auto end = std::chrono::system_clock::now();
                if (std::chrono::duration_cast<std::chrono::microseconds>(end - start).count() >= polling_us) {
                    break;
                }
            }
        }

        if (!x->dec_entries.empty()){
            std::lock_guard<std::mutex> lock(x->dec_lock);
            dec_entries = x->dec_entries;
            x->dec_entries.clear();
        }

        for (auto &entry : dec_entries) {
            int updated_len;
            real_EVP_DecryptInit_ex(local_ctx, EVP_aes_256_gcm(), 0, decrypt_key, entry->iv);
            real_EVP_CIPHER_CTX_ctrl(local_ctx, EVP_CTRL_GCM_SET_TAG, 16, entry->tag);
            assert(real_EVP_DecryptUpdate(local_ctx, (unsigned char *)entry->dst, &updated_len, entry->buffer, entry->size) == 1);
            real_EVP_DecryptFinal_ex(local_ctx, (unsigned char *)entry->dst + updated_len, &updated_len);
            assert(updated_len == 0);
            entry->busy = false;
        }
        dec_entries.clear();
    }
}


void decrypt_manager(void *entry)
{
    auto x = (struct decrypt_worker_entry *)entry;
    auto worker_id = x->id;
    bind_core(2 * worker_id + 4);
    CUcontext cuda_ctx;
    CUdevice dev;
    cudaStream_t stream;
    void *fake_src, *fake_dst;
    assert(cuInit(0) == CUDA_SUCCESS);
    assert(cuDeviceGet(&dev, 0) == CUDA_SUCCESS);
    assert(cuCtxCreate(&cuda_ctx, CU_CTX_SCHED_SPIN, dev) == CUDA_SUCCESS);
    assert(cuCtxPushCurrent(cuda_ctx) == CUDA_SUCCESS);
    assert(real_cudaStreamCreateWithFlags(&stream, cudaStreamNonBlocking) == cudaSuccess);
    assert(real_cudaMallocHost(&fake_dst, 1ul << 20) == cudaSuccess);
    sleep(1);
    void *dev_buffer;
    real_cudaMalloc(&dev_buffer, 1ul << 20);
    real_cudaMemcpyAsync(fake_dst, dev_buffer, x->magic_sz, cudaMemcpyDeviceToHost, stream);
    real_cudaMemcpyAsync(fake_dst, dev_buffer, x->magic_sz, cudaMemcpyDeviceToHost, stream);
    real_cudaDeviceSynchronize();
    x->commit_init_done = true;

    std::deque<decryption_task> dec_tasks;
    std::deque<decryption_entry *> dec_entries;
    std::deque<encryption_task> enc_tasks;
    auto dec_ctx = m_magic_decctx[x->magic_sz];
    auto &dec_metadata = *m_ctx_dmetadata.at(dec_ctx);
    dec_metadata.remain = 0;

    while (1) {
        while (x->dec_tasks.empty() && dec_entries.empty()) {
            // Polling 1 us
            constexpr int polling_us = 1;
            auto start = std::chrono::system_clock::now();
            while (1) {
                auto end = std::chrono::system_clock::now();
                if (std::chrono::duration_cast<std::chrono::microseconds>(end - start).count() >= polling_us) {
                    break;
                }
            }
        }

        if (!x->dec_tasks.empty()){
            std::lock_guard<std::mutex> lock(x->lock);
            dec_tasks = x->dec_tasks;
            x->dec_tasks.clear();
        }

        for (auto &task : dec_tasks) {
            dec_metadata.remain = 0;
            assert(real_cudaMemcpyAsync(dev_buffer, task.src, task.size, cudaMemcpyDeviceToDevice, stream) == cudaSuccess);
            assert(real_cudaMemcpyAsync(fake_dst, dev_buffer, task.size, cudaMemcpyDeviceToHost, stream) == cudaSuccess);

            auto entry = new decryption_entry;
            entry->buffer = dec_metadata.cur_buffer;
            memcpy(entry->tag, dec_metadata.cur_tag, 16);
            memcpy(entry->iv, dec_metadata.cur_iv, iv_length);
            entry->size = task.size;
            entry->busy = true;
            entry->dst = task.dst;
            entry->busy = true;
            {
                std::lock_guard<std::mutex> lock(x->dec_lock);
                x->dec_entries.push_back(entry);
                dec_entries.push_back(entry);
            }
        }


        // Send to encryption
        bool batch_first = true;
        for (auto iter = dec_entries.begin(); iter != dec_entries.end();) {
            auto &entry = *iter;
            if (entry->busy) {
                ++iter;
                continue;
            }
            encryption_task task;
            task.src = entry->dst;
            task.size = entry->size;
            task.iv_increment = batch_first ? dec_entries.size() : 0;
            batch_first = false;
            enc_tasks.push_back(task);

            // Remove buffer
            dec_metadata.allocator.free((unsigned char *)entry->buffer);
            delete entry;
            iter = dec_entries.erase(iter);
        }

        if (!enc_tasks.empty()) {
            auto worker_entry = x->enc_worker_entry;
            std::lock_guard<std::mutex> lock(worker_entry->lock);
            for (auto &task : enc_tasks) {
                worker_entry->enc_tasks.push_back(task);
            }
        }

        dec_tasks.clear();
        enc_tasks.clear();
    }
}