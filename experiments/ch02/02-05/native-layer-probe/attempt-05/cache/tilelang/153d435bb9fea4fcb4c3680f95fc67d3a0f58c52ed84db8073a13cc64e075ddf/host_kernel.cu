// tilelang target: c -keys=cpu 
#define TVM_EXPORTS
#include "tvm/runtime/base.h"
#include "tvm/runtime/c_backend_api.h"
#include "tvm/ffi/c_api.h"
#include <math.h>
#include <stdio.h>
#include <stdbool.h>
#ifdef __OBJC__
#include "tvm/runtime/device_api.h"
#include "tvm/ffi/function.h"
#include <Metal/Metal.h>
#include <Foundation/Foundation.h>
#include <torch/mps.h>
#endif
void* __tvm_ffi__library_ctx = NULL;
static void* __tvm_error_ndim_mismatch_packed = NULL;
static void* __tvm_error_dtype_mismatch_packed = NULL;
static void* __tvm_error_expect_eq_packed = NULL;
static void* __tvm_error_byte_offset_mismatch_packed = NULL;
static void* __tvm_error_device_type_mismatch_packed = NULL;
static void* __tvm_error_null_ptr_packed = NULL;
static void* __tvm_set_device_packed = NULL;
static void* mhc_post_tilelang_kernel_packed = NULL;
#ifdef __cplusplus
extern "C"
#endif
int32_t mhc_post_tilelang(void* self_handle, void* args, int32_t num_args, void* result);
#ifdef __cplusplus
extern "C"
#endif
int32_t mhc_post_tilelang(void* self_handle, void* args, int32_t num_args, void* result) {
  TVMFFIAny stack[12];
  void* stack_ffi_any = stack;
  if (!((num_args == 5))) {
    char __tvm_assert_msg_buf[512];
    snprintf(__tvm_assert_msg_buf, 512, "%s; expected: %lld, got: %lld", "mhc_post_tilelang: num_args should be 5", (long long)(num_args), (long long)(5));
    TVMFFIErrorSetRaisedFromCStr("RuntimeError", __tvm_assert_msg_buf);
    return -1;
  }
  if (!(!(args == NULL))) {
    TVMFFIErrorSetRaisedFromCStr("RuntimeError", "mhc_post_tilelang: args pointer is NULL");
    return -1;
  }
  int32_t a_type_index = (((TVMFFIAny*)args)[0].type_index);
  if (!(((((a_type_index == 0) || (a_type_index == 4)) || (a_type_index == 7)) || (64 <= a_type_index)))) {
    TVMFFIErrorSetRaisedFromCStr("RuntimeError", "kernel mhc_post_tilelang input a expected pointer or tensor handle");
    return -1;
  }
  int32_t b_type_index = (((TVMFFIAny*)args)[1].type_index);
  if (!(((((b_type_index == 0) || (b_type_index == 4)) || (b_type_index == 7)) || (64 <= b_type_index)))) {
    TVMFFIErrorSetRaisedFromCStr("RuntimeError", "kernel mhc_post_tilelang input b expected pointer or tensor handle");
    return -1;
  }
  int32_t c_type_index = (((TVMFFIAny*)args)[2].type_index);
  if (!(((((c_type_index == 0) || (c_type_index == 4)) || (c_type_index == 7)) || (64 <= c_type_index)))) {
    TVMFFIErrorSetRaisedFromCStr("RuntimeError", "kernel mhc_post_tilelang input c expected pointer or tensor handle");
    return -1;
  }
  int32_t d_type_index = (((TVMFFIAny*)args)[3].type_index);
  if (!(((((d_type_index == 0) || (d_type_index == 4)) || (d_type_index == 7)) || (64 <= d_type_index)))) {
    TVMFFIErrorSetRaisedFromCStr("RuntimeError", "kernel mhc_post_tilelang input d expected pointer or tensor handle");
    return -1;
  }
  int32_t x_type_index = (((TVMFFIAny*)args)[4].type_index);
  if (!(((((x_type_index == 0) || (x_type_index == 4)) || (x_type_index == 7)) || (64 <= x_type_index)))) {
    TVMFFIErrorSetRaisedFromCStr("RuntimeError", "kernel mhc_post_tilelang input x expected pointer or tensor handle");
    return -1;
  }
  void* a = ((a_type_index == 70) ? ((void*)((char*)(((TVMFFIAny*)args)[0].v_ptr) + 24)) : (((TVMFFIAny*)args)[0].v_ptr));
  void* b = ((b_type_index == 70) ? ((void*)((char*)(((TVMFFIAny*)args)[1].v_ptr) + 24)) : (((TVMFFIAny*)args)[1].v_ptr));
  void* c = ((c_type_index == 70) ? ((void*)((char*)(((TVMFFIAny*)args)[2].v_ptr) + 24)) : (((TVMFFIAny*)args)[2].v_ptr));
  void* d = ((d_type_index == 70) ? ((void*)((char*)(((TVMFFIAny*)args)[3].v_ptr) + 24)) : (((TVMFFIAny*)args)[3].v_ptr));
  void* x = ((x_type_index == 70) ? ((void*)((char*)(((TVMFFIAny*)args)[4].v_ptr) + 24)) : (((TVMFFIAny*)args)[4].v_ptr));
  bool mhc_post_tilelang_a_is_null = (a == NULL);
  if (!(!mhc_post_tilelang_a_is_null)) {
    TVMFFIErrorSetRaisedFromCStr("RuntimeError", "mhc_post_tilelang.a is expected to have non-NULL pointer");
    return -1;
  }
  bool mhc_post_tilelang_b_is_null = (b == NULL);
  if (!(!mhc_post_tilelang_b_is_null)) {
    TVMFFIErrorSetRaisedFromCStr("RuntimeError", "mhc_post_tilelang.b is expected to have non-NULL pointer");
    return -1;
  }
  bool mhc_post_tilelang_c_is_null = (c == NULL);
  if (!(!mhc_post_tilelang_c_is_null)) {
    TVMFFIErrorSetRaisedFromCStr("RuntimeError", "mhc_post_tilelang.c is expected to have non-NULL pointer");
    return -1;
  }
  bool mhc_post_tilelang_d_is_null = (d == NULL);
  if (!(!mhc_post_tilelang_d_is_null)) {
    TVMFFIErrorSetRaisedFromCStr("RuntimeError", "mhc_post_tilelang.d is expected to have non-NULL pointer");
    return -1;
  }
  bool mhc_post_tilelang_x_is_null = (x == NULL);
  if (!(!mhc_post_tilelang_x_is_null)) {
    TVMFFIErrorSetRaisedFromCStr("RuntimeError", "mhc_post_tilelang.x is expected to have non-NULL pointer");
    return -1;
  }
  void* mhc_post_tilelang_a_shape = (((DLTensor*)a)[0].shape);
  void* mhc_post_tilelang_b_shape = (((DLTensor*)b)[0].shape);
  void* mhc_post_tilelang_c_shape = (((DLTensor*)c)[0].shape);
  void* mhc_post_tilelang_d_shape = (((DLTensor*)d)[0].shape);
  void* mhc_post_tilelang_x_shape = (((DLTensor*)x)[0].shape);
  if ((((DLTensor*)a)[0].ndim) != 3) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"a";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = (int64_t)3;
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)a)[0].ndim));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = (int64_t)0;
    if (__tvm_error_ndim_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_ndim_mismatch", &__tvm_error_ndim_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_1;
    result_1.type_index = kTVMFFINone;
    result_1.zero_padding = 0;
    result_1.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_ndim_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 4, &result_1) != 0) {
      return -1;
    }
  }
  if (!((bool)1)) {
    TVMFFIErrorSetRaisedFromCStr("RuntimeError", "Symbolic shape variable num_tokens requires at least one non-null buffer among: mhc_post_tilelang.a, mhc_post_tilelang.b, mhc_post_tilelang.c, mhc_post_tilelang.d, mhc_post_tilelang.x");
    return -1;
  }
  int32_t num_tokens = ((int32_t)((int64_t*)mhc_post_tilelang_a_shape)[0]);
  void* mhc_post_tilelang_a_strides = (((DLTensor*)a)[0].strides);
  int32_t dev_id = (((DLTensor*)a)[0].device.device_id);
  void* a_1 = (((DLTensor*)a)[0].data);
  if ((((DLTensor*)b)[0].ndim) != 3) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"b";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = (int64_t)3;
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)b)[0].ndim));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = (int64_t)0;
    if (__tvm_error_ndim_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_ndim_mismatch", &__tvm_error_ndim_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_2;
    result_2.type_index = kTVMFFINone;
    result_2.zero_padding = 0;
    result_2.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_ndim_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 4, &result_2) != 0) {
      return -1;
    }
  }
  void* mhc_post_tilelang_b_strides = (((DLTensor*)b)[0].strides);
  void* b_1 = (((DLTensor*)b)[0].data);
  if ((((DLTensor*)c)[0].ndim) != 2) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"c";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = (int64_t)2;
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)c)[0].ndim));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = (int64_t)0;
    if (__tvm_error_ndim_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_ndim_mismatch", &__tvm_error_ndim_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_3;
    result_3.type_index = kTVMFFINone;
    result_3.zero_padding = 0;
    result_3.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_ndim_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 4, &result_3) != 0) {
      return -1;
    }
  }
  void* mhc_post_tilelang_c_strides = (((DLTensor*)c)[0].strides);
  void* c_1 = (((DLTensor*)c)[0].data);
  if ((((DLTensor*)d)[0].ndim) != 2) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"d";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = (int64_t)2;
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)d)[0].ndim));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = (int64_t)0;
    if (__tvm_error_ndim_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_ndim_mismatch", &__tvm_error_ndim_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_4;
    result_4.type_index = kTVMFFINone;
    result_4.zero_padding = 0;
    result_4.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_ndim_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 4, &result_4) != 0) {
      return -1;
    }
  }
  void* mhc_post_tilelang_d_strides = (((DLTensor*)d)[0].strides);
  void* d_1 = (((DLTensor*)d)[0].data);
  if ((((DLTensor*)x)[0].ndim) != 3) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"x";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = (int64_t)3;
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)x)[0].ndim));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = (int64_t)0;
    if (__tvm_error_ndim_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_ndim_mismatch", &__tvm_error_ndim_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_5;
    result_5.type_index = kTVMFFINone;
    result_5.zero_padding = 0;
    result_5.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_ndim_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 4, &result_5) != 0) {
      return -1;
    }
  }
  void* mhc_post_tilelang_x_strides = (((DLTensor*)x)[0].strides);
  void* x_1 = (((DLTensor*)x)[0].data);
  if ((((((DLTensor*)a)[0].dtype.code) != (uint8_t)2) || ((((DLTensor*)a)[0].dtype.bits) != (uint8_t)32)) || ((((DLTensor*)a)[0].dtype.lanes) != (uint16_t)1)) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"a";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = ((int64_t)(((DLTensor*)a)[0].dtype.code));
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)a)[0].dtype.bits));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)(((DLTensor*)a)[0].dtype.lanes));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)2;
    (((TVMFFIAny*)stack_ffi_any)[6].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[6].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[6].v_int64) = (int64_t)32;
    (((TVMFFIAny*)stack_ffi_any)[7].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[7].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[7].v_int64) = (int64_t)1;
    (((TVMFFIAny*)stack_ffi_any)[8].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[8].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[8].v_int64) = (int64_t)0;
    if (__tvm_error_dtype_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_dtype_mismatch", &__tvm_error_dtype_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_6;
    result_6.type_index = kTVMFFINone;
    result_6.zero_padding = 0;
    result_6.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_dtype_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 8, &result_6) != 0) {
      return -1;
    }
  }
  if (((int32_t)((int64_t*)mhc_post_tilelang_a_shape)[1]) != 4) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"a";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"shape[1]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)4;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)((int32_t)((int64_t*)mhc_post_tilelang_a_shape)[1]));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_7;
    result_7.type_index = kTVMFFINone;
    result_7.zero_padding = 0;
    result_7.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_7) != 0) {
      return -1;
    }
  }
  if (((int32_t)((int64_t*)mhc_post_tilelang_a_shape)[2]) != 4) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"a";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"shape[2]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)4;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)((int32_t)((int64_t*)mhc_post_tilelang_a_shape)[2]));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_8;
    result_8.type_index = kTVMFFINone;
    result_8.zero_padding = 0;
    result_8.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_8) != 0) {
      return -1;
    }
  }
  int32_t condval;
  if ((mhc_post_tilelang_a_strides == NULL)) {
    condval = 1;
  } else {
    condval = ((int32_t)((int64_t*)mhc_post_tilelang_a_strides)[2]);
  }
  if (condval != 1) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"a";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"strides[2]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)1;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    int32_t condval_1;
    if ((mhc_post_tilelang_a_strides == NULL)) {
      condval_1 = 1;
    } else {
      condval_1 = ((int32_t)((int64_t*)mhc_post_tilelang_a_strides)[2]);
    }
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)condval_1);
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_9;
    result_9.type_index = kTVMFFINone;
    result_9.zero_padding = 0;
    result_9.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_9) != 0) {
      return -1;
    }
  }
  int32_t condval_2;
  if ((mhc_post_tilelang_a_strides == NULL)) {
    condval_2 = 1;
  } else {
    condval_2 = ((int32_t)((int64_t*)mhc_post_tilelang_a_strides)[1]);
  }
  if (condval_2 != 4) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"a";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"strides[1]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)4;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    int32_t condval_3;
    if ((mhc_post_tilelang_a_strides == NULL)) {
      condval_3 = 1;
    } else {
      condval_3 = ((int32_t)((int64_t*)mhc_post_tilelang_a_strides)[1]);
    }
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)condval_3);
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_10;
    result_10.type_index = kTVMFFINone;
    result_10.zero_padding = 0;
    result_10.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_10) != 0) {
      return -1;
    }
  }
  int32_t condval_4;
  if ((mhc_post_tilelang_a_strides == NULL)) {
    condval_4 = 1;
  } else {
    condval_4 = ((int32_t)((int64_t*)mhc_post_tilelang_a_strides)[0]);
  }
  if (condval_4 != 16) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"a";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"strides[0]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)16;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    int32_t condval_5;
    if ((mhc_post_tilelang_a_strides == NULL)) {
      condval_5 = 1;
    } else {
      condval_5 = ((int32_t)((int64_t*)mhc_post_tilelang_a_strides)[0]);
    }
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)condval_5);
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_11;
    result_11.type_index = kTVMFFINone;
    result_11.zero_padding = 0;
    result_11.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_11) != 0) {
      return -1;
    }
  }
  if ((uint64_t)0 != (((DLTensor*)a)[0].byte_offset)) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"a";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = (int64_t)0;
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)a)[0].byte_offset));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = (int64_t)0;
    if (__tvm_error_byte_offset_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_byte_offset_mismatch", &__tvm_error_byte_offset_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_12;
    result_12.type_index = kTVMFFINone;
    result_12.zero_padding = 0;
    result_12.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_byte_offset_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 4, &result_12) != 0) {
      return -1;
    }
  }
  if ((((DLTensor*)a)[0].device.device_type) != 2) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"a";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = (int64_t)2;
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)a)[0].device.device_type));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = (int64_t)0;
    if (__tvm_error_device_type_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_device_type_mismatch", &__tvm_error_device_type_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_13;
    result_13.type_index = kTVMFFINone;
    result_13.zero_padding = 0;
    result_13.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_device_type_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 4, &result_13) != 0) {
      return -1;
    }
  }
  if (num_tokens != 0) {
    if (a_1 == NULL) {
      (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
      (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
      (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
      (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
      (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
      (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"a";
      (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
      (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
      (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"data pointer";
      (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 0;
      (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)0;
      if (__tvm_error_null_ptr_packed == NULL) {
        if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_null_ptr", &__tvm_error_null_ptr_packed) != 0) {
          return -1;
        }
      }
      TVMFFIAny result_14;
      result_14.type_index = kTVMFFINone;
      result_14.zero_padding = 0;
      result_14.v_int64 = 0;
      if (TVMFFIFunctionCall(__tvm_error_null_ptr_packed, (TVMFFIAny*) stack_ffi_any, 3, &result_14) != 0) {
        return -1;
      }
    }
  } else {
  }
  if ((((((DLTensor*)b)[0].dtype.code) != (uint8_t)4) || ((((DLTensor*)b)[0].dtype.bits) != (uint8_t)16)) || ((((DLTensor*)b)[0].dtype.lanes) != (uint16_t)1)) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"b";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = ((int64_t)(((DLTensor*)b)[0].dtype.code));
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)b)[0].dtype.bits));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)(((DLTensor*)b)[0].dtype.lanes));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)4;
    (((TVMFFIAny*)stack_ffi_any)[6].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[6].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[6].v_int64) = (int64_t)16;
    (((TVMFFIAny*)stack_ffi_any)[7].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[7].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[7].v_int64) = (int64_t)1;
    (((TVMFFIAny*)stack_ffi_any)[8].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[8].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[8].v_int64) = (int64_t)0;
    if (__tvm_error_dtype_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_dtype_mismatch", &__tvm_error_dtype_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_15;
    result_15.type_index = kTVMFFINone;
    result_15.zero_padding = 0;
    result_15.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_dtype_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 8, &result_15) != 0) {
      return -1;
    }
  }
  if (((int32_t)((int64_t*)mhc_post_tilelang_a_shape)[0]) != ((int32_t)((int64_t*)mhc_post_tilelang_b_shape)[0])) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"b";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"shape[0]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)((int32_t)((int64_t*)mhc_post_tilelang_b_shape)[0]));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)((int32_t)((int64_t*)mhc_post_tilelang_a_shape)[0]));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_16;
    result_16.type_index = kTVMFFINone;
    result_16.zero_padding = 0;
    result_16.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_16) != 0) {
      return -1;
    }
  }
  if (((int32_t)((int64_t*)mhc_post_tilelang_b_shape)[1]) != 4) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"b";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"shape[1]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)4;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)((int32_t)((int64_t*)mhc_post_tilelang_b_shape)[1]));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_17;
    result_17.type_index = kTVMFFINone;
    result_17.zero_padding = 0;
    result_17.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_17) != 0) {
      return -1;
    }
  }
  if (((int32_t)((int64_t*)mhc_post_tilelang_b_shape)[2]) != 4096) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"b";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"shape[2]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)4096;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)((int32_t)((int64_t*)mhc_post_tilelang_b_shape)[2]));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_18;
    result_18.type_index = kTVMFFINone;
    result_18.zero_padding = 0;
    result_18.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_18) != 0) {
      return -1;
    }
  }
  int32_t condval_6;
  if ((mhc_post_tilelang_b_strides == NULL)) {
    condval_6 = 1;
  } else {
    condval_6 = ((int32_t)((int64_t*)mhc_post_tilelang_b_strides)[2]);
  }
  if (condval_6 != 1) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"b";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"strides[2]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)1;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    int32_t condval_7;
    if ((mhc_post_tilelang_b_strides == NULL)) {
      condval_7 = 1;
    } else {
      condval_7 = ((int32_t)((int64_t*)mhc_post_tilelang_b_strides)[2]);
    }
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)condval_7);
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_19;
    result_19.type_index = kTVMFFINone;
    result_19.zero_padding = 0;
    result_19.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_19) != 0) {
      return -1;
    }
  }
  int32_t condval_8;
  if ((mhc_post_tilelang_b_strides == NULL)) {
    condval_8 = 1;
  } else {
    condval_8 = ((int32_t)((int64_t*)mhc_post_tilelang_b_strides)[1]);
  }
  if (condval_8 != 4096) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"b";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"strides[1]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)4096;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    int32_t condval_9;
    if ((mhc_post_tilelang_b_strides == NULL)) {
      condval_9 = 1;
    } else {
      condval_9 = ((int32_t)((int64_t*)mhc_post_tilelang_b_strides)[1]);
    }
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)condval_9);
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_20;
    result_20.type_index = kTVMFFINone;
    result_20.zero_padding = 0;
    result_20.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_20) != 0) {
      return -1;
    }
  }
  int32_t condval_10;
  if ((mhc_post_tilelang_b_strides == NULL)) {
    condval_10 = 1;
  } else {
    condval_10 = ((int32_t)((int64_t*)mhc_post_tilelang_b_strides)[0]);
  }
  if (condval_10 != 16384) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"b";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"strides[0]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)16384;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    int32_t condval_11;
    if ((mhc_post_tilelang_b_strides == NULL)) {
      condval_11 = 1;
    } else {
      condval_11 = ((int32_t)((int64_t*)mhc_post_tilelang_b_strides)[0]);
    }
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)condval_11);
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_21;
    result_21.type_index = kTVMFFINone;
    result_21.zero_padding = 0;
    result_21.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_21) != 0) {
      return -1;
    }
  }
  if ((uint64_t)0 != (((DLTensor*)b)[0].byte_offset)) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"b";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = (int64_t)0;
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)b)[0].byte_offset));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = (int64_t)0;
    if (__tvm_error_byte_offset_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_byte_offset_mismatch", &__tvm_error_byte_offset_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_22;
    result_22.type_index = kTVMFFINone;
    result_22.zero_padding = 0;
    result_22.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_byte_offset_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 4, &result_22) != 0) {
      return -1;
    }
  }
  if ((((DLTensor*)b)[0].device.device_id) != (((DLTensor*)a)[0].device.device_id)) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"b";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"device_id";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)a)[0].device.device_id));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)(((DLTensor*)b)[0].device.device_id));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_23;
    result_23.type_index = kTVMFFINone;
    result_23.zero_padding = 0;
    result_23.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_23) != 0) {
      return -1;
    }
  }
  if ((((DLTensor*)b)[0].device.device_type) != 2) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"b";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = (int64_t)2;
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)b)[0].device.device_type));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = (int64_t)0;
    if (__tvm_error_device_type_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_device_type_mismatch", &__tvm_error_device_type_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_24;
    result_24.type_index = kTVMFFINone;
    result_24.zero_padding = 0;
    result_24.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_device_type_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 4, &result_24) != 0) {
      return -1;
    }
  }
  if (num_tokens != 0) {
    if (b_1 == NULL) {
      (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
      (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
      (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
      (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
      (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
      (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"b";
      (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
      (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
      (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"data pointer";
      (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 0;
      (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)0;
      if (__tvm_error_null_ptr_packed == NULL) {
        if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_null_ptr", &__tvm_error_null_ptr_packed) != 0) {
          return -1;
        }
      }
      TVMFFIAny result_25;
      result_25.type_index = kTVMFFINone;
      result_25.zero_padding = 0;
      result_25.v_int64 = 0;
      if (TVMFFIFunctionCall(__tvm_error_null_ptr_packed, (TVMFFIAny*) stack_ffi_any, 3, &result_25) != 0) {
        return -1;
      }
    }
  } else {
  }
  if ((((((DLTensor*)c)[0].dtype.code) != (uint8_t)2) || ((((DLTensor*)c)[0].dtype.bits) != (uint8_t)32)) || ((((DLTensor*)c)[0].dtype.lanes) != (uint16_t)1)) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"c";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = ((int64_t)(((DLTensor*)c)[0].dtype.code));
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)c)[0].dtype.bits));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)(((DLTensor*)c)[0].dtype.lanes));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)2;
    (((TVMFFIAny*)stack_ffi_any)[6].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[6].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[6].v_int64) = (int64_t)32;
    (((TVMFFIAny*)stack_ffi_any)[7].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[7].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[7].v_int64) = (int64_t)1;
    (((TVMFFIAny*)stack_ffi_any)[8].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[8].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[8].v_int64) = (int64_t)0;
    if (__tvm_error_dtype_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_dtype_mismatch", &__tvm_error_dtype_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_26;
    result_26.type_index = kTVMFFINone;
    result_26.zero_padding = 0;
    result_26.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_dtype_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 8, &result_26) != 0) {
      return -1;
    }
  }
  if (((int32_t)((int64_t*)mhc_post_tilelang_a_shape)[0]) != ((int32_t)((int64_t*)mhc_post_tilelang_c_shape)[0])) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"c";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"shape[0]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)((int32_t)((int64_t*)mhc_post_tilelang_c_shape)[0]));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)((int32_t)((int64_t*)mhc_post_tilelang_a_shape)[0]));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_27;
    result_27.type_index = kTVMFFINone;
    result_27.zero_padding = 0;
    result_27.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_27) != 0) {
      return -1;
    }
  }
  if (((int32_t)((int64_t*)mhc_post_tilelang_c_shape)[1]) != 4) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"c";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"shape[1]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)4;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)((int32_t)((int64_t*)mhc_post_tilelang_c_shape)[1]));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_28;
    result_28.type_index = kTVMFFINone;
    result_28.zero_padding = 0;
    result_28.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_28) != 0) {
      return -1;
    }
  }
  int32_t condval_12;
  if ((mhc_post_tilelang_c_strides == NULL)) {
    condval_12 = 1;
  } else {
    condval_12 = ((int32_t)((int64_t*)mhc_post_tilelang_c_strides)[1]);
  }
  if (condval_12 != 1) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"c";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"strides[1]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)1;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    int32_t condval_13;
    if ((mhc_post_tilelang_c_strides == NULL)) {
      condval_13 = 1;
    } else {
      condval_13 = ((int32_t)((int64_t*)mhc_post_tilelang_c_strides)[1]);
    }
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)condval_13);
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_29;
    result_29.type_index = kTVMFFINone;
    result_29.zero_padding = 0;
    result_29.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_29) != 0) {
      return -1;
    }
  }
  int32_t condval_14;
  if ((mhc_post_tilelang_c_strides == NULL)) {
    condval_14 = 1;
  } else {
    condval_14 = ((int32_t)((int64_t*)mhc_post_tilelang_c_strides)[0]);
  }
  if (condval_14 != 4) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"c";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"strides[0]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)4;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    int32_t condval_15;
    if ((mhc_post_tilelang_c_strides == NULL)) {
      condval_15 = 1;
    } else {
      condval_15 = ((int32_t)((int64_t*)mhc_post_tilelang_c_strides)[0]);
    }
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)condval_15);
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_30;
    result_30.type_index = kTVMFFINone;
    result_30.zero_padding = 0;
    result_30.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_30) != 0) {
      return -1;
    }
  }
  if ((uint64_t)0 != (((DLTensor*)c)[0].byte_offset)) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"c";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = (int64_t)0;
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)c)[0].byte_offset));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = (int64_t)0;
    if (__tvm_error_byte_offset_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_byte_offset_mismatch", &__tvm_error_byte_offset_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_31;
    result_31.type_index = kTVMFFINone;
    result_31.zero_padding = 0;
    result_31.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_byte_offset_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 4, &result_31) != 0) {
      return -1;
    }
  }
  if ((((DLTensor*)c)[0].device.device_id) != (((DLTensor*)a)[0].device.device_id)) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"c";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"device_id";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)a)[0].device.device_id));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)(((DLTensor*)c)[0].device.device_id));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_32;
    result_32.type_index = kTVMFFINone;
    result_32.zero_padding = 0;
    result_32.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_32) != 0) {
      return -1;
    }
  }
  if ((((DLTensor*)c)[0].device.device_type) != 2) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"c";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = (int64_t)2;
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)c)[0].device.device_type));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = (int64_t)0;
    if (__tvm_error_device_type_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_device_type_mismatch", &__tvm_error_device_type_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_33;
    result_33.type_index = kTVMFFINone;
    result_33.zero_padding = 0;
    result_33.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_device_type_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 4, &result_33) != 0) {
      return -1;
    }
  }
  if (num_tokens != 0) {
    if (c_1 == NULL) {
      (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
      (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
      (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
      (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
      (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
      (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"c";
      (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
      (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
      (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"data pointer";
      (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 0;
      (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)0;
      if (__tvm_error_null_ptr_packed == NULL) {
        if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_null_ptr", &__tvm_error_null_ptr_packed) != 0) {
          return -1;
        }
      }
      TVMFFIAny result_34;
      result_34.type_index = kTVMFFINone;
      result_34.zero_padding = 0;
      result_34.v_int64 = 0;
      if (TVMFFIFunctionCall(__tvm_error_null_ptr_packed, (TVMFFIAny*) stack_ffi_any, 3, &result_34) != 0) {
        return -1;
      }
    }
  } else {
  }
  if ((((((DLTensor*)d)[0].dtype.code) != (uint8_t)4) || ((((DLTensor*)d)[0].dtype.bits) != (uint8_t)16)) || ((((DLTensor*)d)[0].dtype.lanes) != (uint16_t)1)) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"d";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = ((int64_t)(((DLTensor*)d)[0].dtype.code));
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)d)[0].dtype.bits));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)(((DLTensor*)d)[0].dtype.lanes));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)4;
    (((TVMFFIAny*)stack_ffi_any)[6].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[6].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[6].v_int64) = (int64_t)16;
    (((TVMFFIAny*)stack_ffi_any)[7].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[7].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[7].v_int64) = (int64_t)1;
    (((TVMFFIAny*)stack_ffi_any)[8].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[8].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[8].v_int64) = (int64_t)0;
    if (__tvm_error_dtype_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_dtype_mismatch", &__tvm_error_dtype_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_35;
    result_35.type_index = kTVMFFINone;
    result_35.zero_padding = 0;
    result_35.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_dtype_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 8, &result_35) != 0) {
      return -1;
    }
  }
  if (((int32_t)((int64_t*)mhc_post_tilelang_a_shape)[0]) != ((int32_t)((int64_t*)mhc_post_tilelang_d_shape)[0])) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"d";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"shape[0]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)((int32_t)((int64_t*)mhc_post_tilelang_d_shape)[0]));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)((int32_t)((int64_t*)mhc_post_tilelang_a_shape)[0]));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_36;
    result_36.type_index = kTVMFFINone;
    result_36.zero_padding = 0;
    result_36.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_36) != 0) {
      return -1;
    }
  }
  if (((int32_t)((int64_t*)mhc_post_tilelang_d_shape)[1]) != 4096) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"d";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"shape[1]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)4096;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)((int32_t)((int64_t*)mhc_post_tilelang_d_shape)[1]));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_37;
    result_37.type_index = kTVMFFINone;
    result_37.zero_padding = 0;
    result_37.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_37) != 0) {
      return -1;
    }
  }
  int32_t condval_16;
  if ((mhc_post_tilelang_d_strides == NULL)) {
    condval_16 = 1;
  } else {
    condval_16 = ((int32_t)((int64_t*)mhc_post_tilelang_d_strides)[1]);
  }
  if (condval_16 != 1) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"d";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"strides[1]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)1;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    int32_t condval_17;
    if ((mhc_post_tilelang_d_strides == NULL)) {
      condval_17 = 1;
    } else {
      condval_17 = ((int32_t)((int64_t*)mhc_post_tilelang_d_strides)[1]);
    }
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)condval_17);
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_38;
    result_38.type_index = kTVMFFINone;
    result_38.zero_padding = 0;
    result_38.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_38) != 0) {
      return -1;
    }
  }
  int32_t condval_18;
  if ((mhc_post_tilelang_d_strides == NULL)) {
    condval_18 = 1;
  } else {
    condval_18 = ((int32_t)((int64_t*)mhc_post_tilelang_d_strides)[0]);
  }
  if (condval_18 != 4096) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"d";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"strides[0]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)4096;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    int32_t condval_19;
    if ((mhc_post_tilelang_d_strides == NULL)) {
      condval_19 = 1;
    } else {
      condval_19 = ((int32_t)((int64_t*)mhc_post_tilelang_d_strides)[0]);
    }
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)condval_19);
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_39;
    result_39.type_index = kTVMFFINone;
    result_39.zero_padding = 0;
    result_39.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_39) != 0) {
      return -1;
    }
  }
  if ((uint64_t)0 != (((DLTensor*)d)[0].byte_offset)) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"d";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = (int64_t)0;
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)d)[0].byte_offset));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = (int64_t)0;
    if (__tvm_error_byte_offset_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_byte_offset_mismatch", &__tvm_error_byte_offset_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_40;
    result_40.type_index = kTVMFFINone;
    result_40.zero_padding = 0;
    result_40.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_byte_offset_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 4, &result_40) != 0) {
      return -1;
    }
  }
  if ((((DLTensor*)d)[0].device.device_id) != (((DLTensor*)a)[0].device.device_id)) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"d";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"device_id";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)a)[0].device.device_id));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)(((DLTensor*)d)[0].device.device_id));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_41;
    result_41.type_index = kTVMFFINone;
    result_41.zero_padding = 0;
    result_41.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_41) != 0) {
      return -1;
    }
  }
  if ((((DLTensor*)d)[0].device.device_type) != 2) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"d";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = (int64_t)2;
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)d)[0].device.device_type));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = (int64_t)0;
    if (__tvm_error_device_type_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_device_type_mismatch", &__tvm_error_device_type_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_42;
    result_42.type_index = kTVMFFINone;
    result_42.zero_padding = 0;
    result_42.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_device_type_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 4, &result_42) != 0) {
      return -1;
    }
  }
  if (num_tokens != 0) {
    if (d_1 == NULL) {
      (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
      (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
      (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
      (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
      (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
      (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"d";
      (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
      (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
      (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"data pointer";
      (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 0;
      (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)0;
      if (__tvm_error_null_ptr_packed == NULL) {
        if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_null_ptr", &__tvm_error_null_ptr_packed) != 0) {
          return -1;
        }
      }
      TVMFFIAny result_43;
      result_43.type_index = kTVMFFINone;
      result_43.zero_padding = 0;
      result_43.v_int64 = 0;
      if (TVMFFIFunctionCall(__tvm_error_null_ptr_packed, (TVMFFIAny*) stack_ffi_any, 3, &result_43) != 0) {
        return -1;
      }
    }
  } else {
  }
  if ((((((DLTensor*)x)[0].dtype.code) != (uint8_t)4) || ((((DLTensor*)x)[0].dtype.bits) != (uint8_t)16)) || ((((DLTensor*)x)[0].dtype.lanes) != (uint16_t)1)) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"x";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = ((int64_t)(((DLTensor*)x)[0].dtype.code));
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)x)[0].dtype.bits));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)(((DLTensor*)x)[0].dtype.lanes));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)4;
    (((TVMFFIAny*)stack_ffi_any)[6].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[6].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[6].v_int64) = (int64_t)16;
    (((TVMFFIAny*)stack_ffi_any)[7].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[7].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[7].v_int64) = (int64_t)1;
    (((TVMFFIAny*)stack_ffi_any)[8].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[8].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[8].v_int64) = (int64_t)0;
    if (__tvm_error_dtype_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_dtype_mismatch", &__tvm_error_dtype_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_44;
    result_44.type_index = kTVMFFINone;
    result_44.zero_padding = 0;
    result_44.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_dtype_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 8, &result_44) != 0) {
      return -1;
    }
  }
  if (((int32_t)((int64_t*)mhc_post_tilelang_a_shape)[0]) != ((int32_t)((int64_t*)mhc_post_tilelang_x_shape)[0])) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"x";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"shape[0]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)((int32_t)((int64_t*)mhc_post_tilelang_x_shape)[0]));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)((int32_t)((int64_t*)mhc_post_tilelang_a_shape)[0]));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_45;
    result_45.type_index = kTVMFFINone;
    result_45.zero_padding = 0;
    result_45.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_45) != 0) {
      return -1;
    }
  }
  if (((int32_t)((int64_t*)mhc_post_tilelang_x_shape)[1]) != 4) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"x";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"shape[1]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)4;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)((int32_t)((int64_t*)mhc_post_tilelang_x_shape)[1]));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_46;
    result_46.type_index = kTVMFFINone;
    result_46.zero_padding = 0;
    result_46.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_46) != 0) {
      return -1;
    }
  }
  if (((int32_t)((int64_t*)mhc_post_tilelang_x_shape)[2]) != 4096) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"x";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"shape[2]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)4096;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)((int32_t)((int64_t*)mhc_post_tilelang_x_shape)[2]));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_47;
    result_47.type_index = kTVMFFINone;
    result_47.zero_padding = 0;
    result_47.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_47) != 0) {
      return -1;
    }
  }
  int32_t condval_20;
  if ((mhc_post_tilelang_x_strides == NULL)) {
    condval_20 = 1;
  } else {
    condval_20 = ((int32_t)((int64_t*)mhc_post_tilelang_x_strides)[2]);
  }
  if (condval_20 != 1) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"x";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"strides[2]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)1;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    int32_t condval_21;
    if ((mhc_post_tilelang_x_strides == NULL)) {
      condval_21 = 1;
    } else {
      condval_21 = ((int32_t)((int64_t*)mhc_post_tilelang_x_strides)[2]);
    }
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)condval_21);
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_48;
    result_48.type_index = kTVMFFINone;
    result_48.zero_padding = 0;
    result_48.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_48) != 0) {
      return -1;
    }
  }
  int32_t condval_22;
  if ((mhc_post_tilelang_x_strides == NULL)) {
    condval_22 = 1;
  } else {
    condval_22 = ((int32_t)((int64_t*)mhc_post_tilelang_x_strides)[1]);
  }
  if (condval_22 != 4096) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"x";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"strides[1]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)4096;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    int32_t condval_23;
    if ((mhc_post_tilelang_x_strides == NULL)) {
      condval_23 = 1;
    } else {
      condval_23 = ((int32_t)((int64_t*)mhc_post_tilelang_x_strides)[1]);
    }
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)condval_23);
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_49;
    result_49.type_index = kTVMFFINone;
    result_49.zero_padding = 0;
    result_49.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_49) != 0) {
      return -1;
    }
  }
  int32_t condval_24;
  if ((mhc_post_tilelang_x_strides == NULL)) {
    condval_24 = 1;
  } else {
    condval_24 = ((int32_t)((int64_t*)mhc_post_tilelang_x_strides)[0]);
  }
  if (condval_24 != 16384) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"x";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"strides[0]";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)16384;
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    int32_t condval_25;
    if ((mhc_post_tilelang_x_strides == NULL)) {
      condval_25 = 1;
    } else {
      condval_25 = ((int32_t)((int64_t*)mhc_post_tilelang_x_strides)[0]);
    }
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)condval_25);
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_50;
    result_50.type_index = kTVMFFINone;
    result_50.zero_padding = 0;
    result_50.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_50) != 0) {
      return -1;
    }
  }
  if ((uint64_t)0 != (((DLTensor*)x)[0].byte_offset)) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"x";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = (int64_t)0;
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)x)[0].byte_offset));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = (int64_t)0;
    if (__tvm_error_byte_offset_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_byte_offset_mismatch", &__tvm_error_byte_offset_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_51;
    result_51.type_index = kTVMFFINone;
    result_51.zero_padding = 0;
    result_51.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_byte_offset_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 4, &result_51) != 0) {
      return -1;
    }
  }
  if ((((DLTensor*)x)[0].device.device_id) != (((DLTensor*)a)[0].device.device_id)) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"x";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"device_id";
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)a)[0].device.device_id));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = ((int64_t)(((DLTensor*)x)[0].device.device_id));
    (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = (int64_t)0;
    if (__tvm_error_expect_eq_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_expect_eq", &__tvm_error_expect_eq_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_52;
    result_52.type_index = kTVMFFINone;
    result_52.zero_padding = 0;
    result_52.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_expect_eq_packed, (TVMFFIAny*) stack_ffi_any, 5, &result_52) != 0) {
      return -1;
    }
  }
  if ((((DLTensor*)x)[0].device.device_type) != 2) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
    (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
    (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"x";
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = (int64_t)2;
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 1;
    (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = ((int64_t)(((DLTensor*)x)[0].device.device_type));
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
    (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = (int64_t)0;
    if (__tvm_error_device_type_mismatch_packed == NULL) {
      if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_device_type_mismatch", &__tvm_error_device_type_mismatch_packed) != 0) {
        return -1;
      }
    }
    TVMFFIAny result_53;
    result_53.type_index = kTVMFFINone;
    result_53.zero_padding = 0;
    result_53.v_int64 = 0;
    if (TVMFFIFunctionCall(__tvm_error_device_type_mismatch_packed, (TVMFFIAny*) stack_ffi_any, 4, &result_53) != 0) {
      return -1;
    }
  }
  if (num_tokens != 0) {
    if (x_1 == NULL) {
      (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 8;
      (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
      (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = (void*)"mhc_post_tilelang";
      (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 8;
      (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
      (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = (void*)"x";
      (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 8;
      (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
      (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = (void*)"data pointer";
      (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 0;
      (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
      (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = (int64_t)0;
      if (__tvm_error_null_ptr_packed == NULL) {
        if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_error_null_ptr", &__tvm_error_null_ptr_packed) != 0) {
          return -1;
        }
      }
      TVMFFIAny result_54;
      result_54.type_index = kTVMFFINone;
      result_54.zero_padding = 0;
      result_54.v_int64 = 0;
      if (TVMFFIFunctionCall(__tvm_error_null_ptr_packed, (TVMFFIAny*) stack_ffi_any, 3, &result_54) != 0) {
        return -1;
      }
    }
  } else {
  }
  (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 1;
  (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
  (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = ((int64_t)2);
  (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 1;
  (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
  (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = ((int64_t)dev_id);
  (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 0;
  (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
  (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = (int64_t)0;
  if (__tvm_set_device_packed == NULL) {
    if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "__tvm_set_device", &__tvm_set_device_packed) != 0) {
      return -1;
    }
  }
  TVMFFIAny result_55;
  result_55.type_index = kTVMFFINone;
  result_55.zero_padding = 0;
  result_55.v_int64 = 0;
  if (TVMFFIFunctionCall(__tvm_set_device_packed, (TVMFFIAny*) stack_ffi_any, 2, &result_55) != 0) {
    return -1;
  }
  if (a_1 == NULL) {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 0;
  } else {
    (((TVMFFIAny*)stack_ffi_any)[0].type_index) = 4;
  }
  (((TVMFFIAny*)stack_ffi_any)[0].zero_padding) = 0;
  (((TVMFFIAny*)stack_ffi_any)[0].v_int64) = 0;
  (((TVMFFIAny*)stack_ffi_any)[0].v_ptr) = a_1;
  if (b_1 == NULL) {
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 0;
  } else {
    (((TVMFFIAny*)stack_ffi_any)[1].type_index) = 4;
  }
  (((TVMFFIAny*)stack_ffi_any)[1].zero_padding) = 0;
  (((TVMFFIAny*)stack_ffi_any)[1].v_int64) = 0;
  (((TVMFFIAny*)stack_ffi_any)[1].v_ptr) = b_1;
  if (c_1 == NULL) {
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 0;
  } else {
    (((TVMFFIAny*)stack_ffi_any)[2].type_index) = 4;
  }
  (((TVMFFIAny*)stack_ffi_any)[2].zero_padding) = 0;
  (((TVMFFIAny*)stack_ffi_any)[2].v_int64) = 0;
  (((TVMFFIAny*)stack_ffi_any)[2].v_ptr) = c_1;
  if (d_1 == NULL) {
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 0;
  } else {
    (((TVMFFIAny*)stack_ffi_any)[3].type_index) = 4;
  }
  (((TVMFFIAny*)stack_ffi_any)[3].zero_padding) = 0;
  (((TVMFFIAny*)stack_ffi_any)[3].v_int64) = 0;
  (((TVMFFIAny*)stack_ffi_any)[3].v_ptr) = d_1;
  if (x_1 == NULL) {
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 0;
  } else {
    (((TVMFFIAny*)stack_ffi_any)[4].type_index) = 4;
  }
  (((TVMFFIAny*)stack_ffi_any)[4].zero_padding) = 0;
  (((TVMFFIAny*)stack_ffi_any)[4].v_int64) = 0;
  (((TVMFFIAny*)stack_ffi_any)[4].v_ptr) = x_1;
  (((TVMFFIAny*)stack_ffi_any)[5].type_index) = 1;
  (((TVMFFIAny*)stack_ffi_any)[5].zero_padding) = 0;
  (((TVMFFIAny*)stack_ffi_any)[5].v_int64) = ((int64_t)num_tokens);
  (((TVMFFIAny*)stack_ffi_any)[6].type_index) = 1;
  (((TVMFFIAny*)stack_ffi_any)[6].zero_padding) = 0;
  (((TVMFFIAny*)stack_ffi_any)[6].v_int64) = ((int64_t)num_tokens);
  (((TVMFFIAny*)stack_ffi_any)[7].type_index) = 1;
  (((TVMFFIAny*)stack_ffi_any)[7].zero_padding) = 0;
  (((TVMFFIAny*)stack_ffi_any)[7].v_int64) = ((int64_t)128);
  (((TVMFFIAny*)stack_ffi_any)[8].type_index) = 1;
  (((TVMFFIAny*)stack_ffi_any)[8].zero_padding) = 0;
  (((TVMFFIAny*)stack_ffi_any)[8].v_int64) = ((int64_t)1);
  (((TVMFFIAny*)stack_ffi_any)[9].type_index) = 1;
  (((TVMFFIAny*)stack_ffi_any)[9].zero_padding) = 0;
  (((TVMFFIAny*)stack_ffi_any)[9].v_int64) = ((int64_t)1);
  (((TVMFFIAny*)stack_ffi_any)[10].type_index) = 1;
  (((TVMFFIAny*)stack_ffi_any)[10].zero_padding) = 0;
  (((TVMFFIAny*)stack_ffi_any)[10].v_int64) = ((int64_t)28672);
  (((TVMFFIAny*)stack_ffi_any)[11].type_index) = 0;
  (((TVMFFIAny*)stack_ffi_any)[11].zero_padding) = 0;
  (((TVMFFIAny*)stack_ffi_any)[11].v_int64) = (int64_t)0;
  if (mhc_post_tilelang_kernel_packed == NULL) {
    if (TVMBackendGetFuncFromEnv(__tvm_ffi__library_ctx, "mhc_post_tilelang_kernel", &mhc_post_tilelang_kernel_packed) != 0) {
      return -1;
    }
  }
  TVMFFIAny result_56;
  result_56.type_index = kTVMFFINone;
  result_56.zero_padding = 0;
  result_56.v_int64 = 0;
  if (TVMFFIFunctionCall(mhc_post_tilelang_kernel_packed, (TVMFFIAny*) stack_ffi_any, 11, &result_56) != 0) {
    return -1;
  }
  return 0;
}

// CodegenC: NOTE: Auto-generated entry function
#ifdef __cplusplus
extern "C"
#endif
int32_t __tvm_ffi_main(void* self, void* args,int num_args, void* result) {
  return mhc_post_tilelang(self, args, num_args, result);
}
