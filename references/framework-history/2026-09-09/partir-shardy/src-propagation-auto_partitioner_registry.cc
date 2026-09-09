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

#include "shardy/dialect/sdy/transforms/propagation/auto_partitioner_registry.h"

#include <cassert>
#include <optional>

#include "llvm/Support/ErrorHandling.h"
#include "llvm/Support/ManagedStatic.h"
#include "llvm/Support/Mutex.h"
#include "mlir/Pass/PassOptions.h"

namespace mlir {
namespace sdy {

namespace {

// The registered callback.
static llvm::ManagedStatic<std::optional<AutoPartitionerCallback>>
    registeredCallback;
static llvm::ManagedStatic<llvm::sys::Mutex> mutex;

}  // namespace

void AutoPartitionerRegistry::setCallback(AutoPartitionerCallback callback) {
  llvm::sys::ScopedLock scopedLock(*mutex);
  // TODO(tomnatan): find a better way to fail in this case, and consider
  // allowing registring multiple callbacks with different keys (that are passed
  // by the user to sdy).

  if (isRegistered()) {
    llvm::report_fatal_error("auto-partitioner callback already registered");
  }
  *registeredCallback = callback;
}

void AutoPartitionerRegistry::addPasses(OpPassManager& pm) {
  // TODO(tomnatan): find a better way to fail in this case.
  if (!isRegistered()) {
    llvm::report_fatal_error("auto-partitioner callback wasn't registered");
  }
  registeredCallback->value()(pm);
}

void AutoPartitionerRegistry::clear() {
  llvm::sys::ScopedLock scopedLock(*mutex);
  registeredCallback->reset();
}

bool AutoPartitionerRegistry::isRegistered() {
  return registeredCallback->has_value();
}

}  // namespace sdy
}  // namespace mlir
