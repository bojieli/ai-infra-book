#include "pipellm.h"
#include "hack.h"
#include <openssl/ssl.h>
#include <dlfcn.h>
#include <iostream>
#include <fstream>
#include <cstdio>
#include <thread>
#include <cassert>
#include <cstring>
#include <sys/mman.h>
#include <vector>
#include <algorithm>
static uint8_t iv_seq[profile_bytes][256] = {};
static uint8_t iv_idx[profile_bytes][256] = {};

static void init_ividx()
{
    for (int i = 0; i < profile_bytes; i++) {
        for (int j = 0; j < 256; j++) {
            iv_idx[i][iv_seq[i][j]] = (uint8_t)j;
        }
    }
}

uint64_t next_iv(uint8_t cur_iv[], uint8_t dest_iv[], uint64_t incr)
{
    uint64_t ret = 0;
    uint64_t idx[profile_bytes + 1];
    for (int i = 0; i < profile_bytes; i++) {
        idx[i] = iv_idx[i][cur_iv[i]];
    }
    idx[0] += incr;
    for (int i = 0; i < profile_bytes; i++) {
        if (i == profile_bytes - 1) {
            ret = idx[i] / 256;
        }
        if (idx[i] >= 256) {
            idx[i + 1] += idx[i] / 256;
            idx[i] %= 256;
        }
    }
    for (int i = 0; i < profile_bytes; i++) {
        dest_iv[i] = iv_seq[i][idx[i]];
    }
    for (int i = profile_bytes; i < iv_length; i++) {
        dest_iv[i] = cur_iv[i];
    }
    return ret;
}

void memcpy_worker(void *entry)
{
    auto x = (memcpy_entry *)entry;
    bind_core(x->core);
    while (true) {
        while (!x->busy);
        memcpy(x->dst, x->src, x->size);
        x->busy = false;
    }
}

static bool encrypt_iv_inited;
static int memcpy_core = 22;
extern "C" int EVP_EncryptUpdate(EVP_CIPHER_CTX *ctx, unsigned char *out, int *outl,
                      const unsigned char *in, int inl)
{
    bool exist0 = m_ctx_metadata.find(ctx) != m_ctx_metadata.end();
    if (!exist0) {
        if (s_magic.find(inl) != s_magic.end()) {
            m_magic_encctx.insert(std::make_pair(inl, ctx));
            auto metadata = std::make_shared<encrypt_metadata>();
            metadata->encrypt_ctx = ctx;
            metadata->remain = 0;
            m_ctx_metadata.insert(std::make_pair(ctx, metadata));

            s_magic.erase(s_magic.find(inl));

            // Memcpy worker
            for (int i = 0; i < memcpy_thread_num - 1; i++) {
                metadata->memcpy_entries[i].busy = false;
                metadata->memcpy_entries[i].core = memcpy_core++;
                metadata->memcpy_threads[i] = new std::thread(memcpy_worker, (void *)&metadata->memcpy_entries[i]);
            }
        }
    } else {
        auto &metadata = *m_ctx_metadata[ctx];
        auto &m_iv_encentry = metadata.m_iv_encentry;
        auto cur_iv_offset = metadata.cur_iv_offset;
        if (m_iv_encentry.find(cur_iv_offset) != m_iv_encentry.end()) {
            auto iter = m_iv_encentry.find(cur_iv_offset);
            auto &encentry = iter->second;
            while (encentry->busy);
            // memcpy(out, encentry->buffer, encentry->size);
            auto src = encentry->buffer;
            auto dst = out;
            auto div = (inl + memcpy_thread_num - 1) / memcpy_thread_num;
            auto size = inl;
            for (int i = 0; i < memcpy_thread_num; i++) {
                if (i == memcpy_thread_num - 1) {
                    memcpy(dst, src, std::min(div, size));
                    break;
                }
                metadata.memcpy_entries[i].src = src;
                metadata.memcpy_entries[i].dst = dst;
                metadata.memcpy_entries[i].size = std::min(div, size);
                std::atomic_thread_fence(std::memory_order_seq_cst);
                metadata.memcpy_entries[i].busy = true;
                src += div;
                dst += div;
                size -= div;
                if (size == 0) break;
            }
            for (int i = 0; i < memcpy_thread_num - 1; i++) {
                while (metadata.memcpy_entries[i].busy);
            }
            assert(inl == encentry->size);
            *outl = inl;

            metadata.remain++;
            return 1;
        }
    }
    auto ret = real_EVP_EncryptUpdate(ctx, out, outl, in, inl);
    return ret;
}

extern "C" int EVP_EncryptInit_ex(EVP_CIPHER_CTX *ctx, const EVP_CIPHER *cipher,
                       ENGINE *impl, const unsigned char *key,
                       const unsigned char *iv)
{
    if (m_ctx_metadata.find(ctx) != m_ctx_metadata.end()) {
        auto &metadata = *m_ctx_metadata[ctx];
        if (!encrypt_iv_inited) {
            std::ifstream iv_profile(iv_profile_path);
            static bool existed = iv_profile.good();
            if (existed) {
                // Profile iv
                for (int i = 0; i < profile_bytes; i++) {
                    for (int j = 0; j < 256; j++) {
                        int x;
                        iv_profile >> x;
                        iv_seq[i][j] = x;
                    }
                }
                init_ividx();
                encrypt_iv_inited = true;
            } else {
                static int sel = 0;
                static uint8_t cur = 0;
                static uint8_t carry = 0;
                static bool record = false;
                static int record_idx = 0;
                if (cur != iv[sel]) {
                    cur = iv[sel];
                    if (carry != 0 && carry != iv[sel + 1]) {
                        if (!record) {
                            // Record from Carry
                            record = true;
                        } else {
                            // Record next
                            record = false;

                            // Save already recorded in file
                            std::ofstream iv_profile_write(iv_profile_path, std::ios::app);
                            for (int i = 0; i < 256; i++) {
                                iv_profile_write << (int)iv_seq[sel][i] << (i == 255 ? '\n' : ' ');
                            }
                            record_idx = 0;
                            iv_profile_write.close();
                            std::cerr << "Profiled sel " << sel << std::endl;
                            sel++;
                            if (sel == profile_bytes) {
                                exit(0);
                            }
                        }
                    }
                    carry = iv[sel + 1];
                    if (record) {
                        iv_seq[sel][record_idx++] = iv[sel];
                    }
                }
            }
        }
        if (!metadata.iv_inited) {
            memcpy(metadata.init_iv, iv, iv_length);
            memcpy(metadata.key, key, key_length);
            metadata.cur_iv_offset = 0;
            metadata.iv_inited = true;
        } else {
            metadata.cur_iv_offset++;
        }
    }
    return real_EVP_EncryptInit_ex(ctx, cipher, impl, key, iv);
}

extern "C" int EVP_EncryptFinal_ex(EVP_CIPHER_CTX *ctx, unsigned char *out, int *outl)
{
    bool exist0 = m_ctx_metadata.find(ctx) != m_ctx_metadata.end();
    if (exist0) {
        auto &metadata = *m_ctx_metadata[ctx];
        if (metadata.remain > 0) {
            *outl = 0;
            return 1;
        }
    }
    auto ret = real_EVP_EncryptFinal_ex(ctx, out, outl);
    return ret;
}

extern "C" int EVP_CIPHER_CTX_ctrl(EVP_CIPHER_CTX *ctx, int type, int arg, void *ptr)
{
    bool exist0 = m_ctx_metadata.find(ctx) != m_ctx_metadata.end();
    if (exist0) {
        auto &metadata = *m_ctx_metadata[ctx];
        if (metadata.remain > 0 && type == EVP_CTRL_GCM_GET_TAG) {
            memcpy(ptr, metadata.m_iv_encentry.at(metadata.cur_iv_offset)->tag, 16);
            metadata.remain--;
            // Must execute in the end
            metadata.allocator.free(metadata.m_iv_encentry.at(metadata.cur_iv_offset)->buffer);
            delete metadata.m_iv_encentry.at(metadata.cur_iv_offset);
            metadata.m_iv_encentry.erase(metadata.cur_iv_offset);
            return 1;
        }
    }
    bool exist1 = m_ctx_dmetadata.find(ctx) != m_ctx_dmetadata.end();
    if (exist1) {
        auto &metadata = *m_ctx_dmetadata[ctx];
        if (metadata.remain == 2 && type == EVP_CTRL_GCM_SET_TAG) {
            memcpy(metadata.cur_tag, ptr, 16);
            return 1;
        }
    }

    auto ret = real_EVP_CIPHER_CTX_ctrl(ctx, type, arg, ptr);
    return ret;
}

extern "C" int EVP_DecryptUpdate(EVP_CIPHER_CTX *ctx, unsigned char *out, int *outl,
                      const unsigned char *in, int inl)
{
    bool exist0 = m_ctx_dmetadata.find(ctx) != m_ctx_dmetadata.end();
    if (!exist0) {
        if (s_magic_dec.find(inl) != s_magic_dec.end()) {
            m_magic_decctx.insert(std::make_pair(inl, ctx));
            auto metadata = std::make_shared<decrypt_metadata>();
            metadata->remain = 0;
            m_ctx_dmetadata.insert(std::make_pair(ctx, metadata));

            s_magic_dec.erase(s_magic_dec.find(inl));

            // Memcpy worker
            for (int i = 0; i < memcpy_thread_num - 1; i++) {
                metadata->memcpy_entries[i].busy = false;
                metadata->memcpy_entries[i].core = memcpy_core++;
                metadata->memcpy_threads[i] = new std::thread(memcpy_worker, (void *)&metadata->memcpy_entries[i]);
            }
        }
    } else {
        // Allocate memory
        auto &metadata = *m_ctx_dmetadata[ctx];
        if (metadata.remain != 2) {
            auto ret = real_EVP_DecryptUpdate(ctx, out, outl, in, inl);
            return ret;
        }
        auto buffer = metadata.allocator.alloc();
        
        // Memcpy into buffer
        {
            auto src = in;
            auto dst = buffer;
            auto div = (inl + memcpy_thread_num - 1) / memcpy_thread_num;
            auto size = inl;
            for (int i = 0; i < memcpy_thread_num; i++) {
                if (i == memcpy_thread_num - 1) {
                    memcpy(dst, src, std::min(div, size));
                    break;
                }
                metadata.memcpy_entries[i].src = src;
                metadata.memcpy_entries[i].dst = dst;
                metadata.memcpy_entries[i].size = std::min(div, size);
                std::atomic_thread_fence(std::memory_order_seq_cst);
                metadata.memcpy_entries[i].busy = true;
                src += div;
                dst += div;
                size -= div;
                if (size == 0) break;
            }
            for (int i = 0; i < memcpy_thread_num - 1; i++) {
                while (metadata.memcpy_entries[i].busy);
            }
        }
        *outl = inl;
        metadata.cur_buffer = buffer;

        return 1;
    }
    auto ret = real_EVP_DecryptUpdate(ctx, out, outl, in, inl);
    return ret;
}

extern "C" int EVP_DecryptInit_ex(EVP_CIPHER_CTX *ctx, const EVP_CIPHER *cipher,
                       ENGINE *impl, const unsigned char *key,
                       const unsigned char *iv)
{
    bool exist0 = m_ctx_dmetadata.find(ctx) != m_ctx_dmetadata.end();
    if (exist0) {
        auto &metadata = *m_ctx_dmetadata[ctx];
        metadata.remain++;
        if (metadata.remain == 2) {
            memcpy(metadata.key, key, key_length);
            memcpy(metadata.cur_iv, iv, iv_length);
            return 1;
        }
    }
    return real_EVP_DecryptInit_ex(ctx, cipher, impl, key, iv);
}

extern "C" int EVP_DecryptFinal_ex(EVP_CIPHER_CTX *ctx, unsigned char *out, int *outl)
{
    bool exist0 = m_ctx_dmetadata.find(ctx) != m_ctx_dmetadata.end();
    if (exist0) {
        auto &metadata = *m_ctx_dmetadata[ctx];
        if (metadata.remain == 2) {
            *outl = 0;
            metadata.remain--;
            return 1;
        }
    }
    return real_EVP_DecryptFinal_ex(ctx, out, outl);
}