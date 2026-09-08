#pragma once
#include <openssl/ssl.h>
#include <cuda.h>
#include <map>
#include <sys/mman.h>
#include <cassert>
#include <unistd.h>
#include <thread>
#include <deque>
#include <queue>
#include <mutex>
#include <vector>
#include <set>
#include <map>
#include <unordered_map>
#include <algorithm>
#include <immintrin.h>
#include <cstdlib>
#include <memory>
#include <pthread.h>
#include <sys/resource.h>
#include <unistd.h>

extern size_t encrypt_magic_sz;
extern size_t decrypt_magic_sz;
const static size_t encrypt_threshold_sz = 0x4c000;
const static size_t decrypt_threshold_sz = 0x4c000;
const static size_t decrypt_threshold_top = 0x80000;
const static size_t block_unit = 1 << 20;
constexpr static size_t key_length = 32;
constexpr static size_t iv_length = 16;
constexpr static int profile_bytes = 3;
constexpr static uint64_t iv_mod = 1 << (8 * profile_bytes);
const static char iv_profile_path[] = "/tmp/profile_iv.txt";

using iv_t = uint64_t;
struct encryption_entry;
struct buffer_allocator {
    std::vector<unsigned char *> buffers;
    const static size_t buffer_size = block_unit;
    unsigned char *alloc() {
        if (buffers.empty()) {
            return new unsigned char[buffer_size];
        } else {
            auto ptr = buffers.back();
            buffers.pop_back();
            return ptr;
        }
    }
    void free(unsigned char *ptr) {
        buffers.push_back(ptr);
    }
};

extern int memcpy_thread_num;
static constexpr int memcpy_thread_num_max = 5;
struct memcpy_entry {
    volatile bool busy;
    const void *src;
    void *dst;
    size_t size;
    int core;
};
struct encrypt_metadata {
    unsigned char key[key_length];
    unsigned char init_iv[iv_length];
    iv_t cur_iv_offset;
    EVP_CIPHER_CTX *encrypt_ctx;
    bool iv_inited;
    int commit_worker_id;

    // Predictor
    std::map<iv_t, encryption_entry *> m_iv_encentry;

    // For openssl
    int remain;

    // Buffer allocator
    buffer_allocator allocator;

    // For memcpy
    std::thread *memcpy_threads[memcpy_thread_num_max];
    memcpy_entry memcpy_entries[memcpy_thread_num_max];
};

struct decrypt_metadata {
    unsigned char key[key_length];
    unsigned char cur_iv[iv_length];
    unsigned char cur_tag[16];
    unsigned char *cur_buffer;

    // For openssl
    int remain;

    // Buffer allocator
    buffer_allocator allocator;

    // For memcpy
    std::thread *memcpy_threads[memcpy_thread_num_max];
    memcpy_entry memcpy_entries[memcpy_thread_num_max];
};

extern std::map<EVP_CIPHER_CTX *, std::shared_ptr<encrypt_metadata>> m_ctx_metadata;
extern std::map<size_t, EVP_CIPHER_CTX *> m_magic_encctx;
extern std::set<size_t> s_magic;

extern std::map<EVP_CIPHER_CTX *, std::shared_ptr<decrypt_metadata>> m_ctx_dmetadata;
extern std::map<size_t, EVP_CIPHER_CTX *> m_magic_decctx;
extern std::set<size_t> s_magic_dec;

extern void encrypt_worker(void *entry);
extern void commit_worker(void *entry);
extern void decrypt_worker(void *entry);
void decrypt_manager(void *entry);
struct encryption_task {
    const void *src;
    size_t size;
    size_t iv_increment;
};
struct commit_task {
    encryption_task enc_task;
    void *dst;
    bool using_predict;
    bool update_predict_iv;
};
struct encrypt_worker_entry {
    int id;
    int local_id;
    int encrypt_workers_per_commit;
    size_t magic_sz;
    volatile int state;
    std::deque<encryption_task> enc_tasks;
    std::deque<commit_task> commit_tasks;
    std::deque<encryption_entry *> enc_entries[10];
    std::mutex lock;
    std::mutex enc_lock[10];
    volatile bool enc_init_done;
    volatile bool commit_init_done;
    volatile bool commit;
    uint64_t predict_iv_offset;
};

struct encryption_entry {
    volatile bool busy;
    const void *src;
    unsigned char *buffer;
    size_t size;
    unsigned char tag[16];
    uint64_t iv_offset;
};

struct decryption_task {
    const void *src;
    void *dst;
    size_t size;
};

struct decryption_entry {
    volatile bool busy;
    const unsigned char *buffer;
    void *dst;
    size_t size;
    unsigned char tag[16];
    unsigned char iv[iv_length];
};

struct decrypt_worker_entry {
    int id;
    size_t magic_sz;
    std::deque<decryption_task> dec_tasks;
    std::mutex lock;

    std::deque<decryption_entry *> dec_entries;
    std::mutex dec_lock;

    volatile bool dec_init_done;
    volatile bool commit_init_done;
    volatile bool commit;

    struct encrypt_worker_entry *enc_worker_entry;
};

uint64_t next_iv(unsigned char cur_iv[], unsigned char dest_iv[], uint64_t incr = 1);

struct Predictor {
    // For read-only swap
    std::vector<std::pair<const void *, size_t>> read_only_swap_record;
    bool read_only_swap_profiled;
    int read_only_swap_cur_idx;
    int read_only_swap_pred_idx;

    // For other swaps
    std::vector<std::pair<const void *, size_t>> other_swap_record;
    std::set<std::pair<const void *, size_t>> other_swap_set;

    // For commit
    std::deque<std::pair<const void*, std::pair<void *, size_t>>> pending_commit;

    // For decryption
    std::deque<decryption_task> pending_decrypt;

    void lock() {
        while (this->locking()) {
            std::this_thread::yield();
        }
        this->_lock = true;
    }

    void unlock() {
        assert(this->_lock);
        this->_lock = false;
    }

    bool locking() {
        return this->_lock;
    }
private:
    bool _lock;
};

static inline void bind_core(int core) {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(core, &cpuset);

    pthread_t currentThread = pthread_self();
    int rc = pthread_setaffinity_np(currentThread, sizeof(cpu_set_t), &cpuset);
    assert(rc == 0);
}