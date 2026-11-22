/* Teaching kernel: signed small integer operands, row-major matrices.
 * All sums in the companion workload fit in int32_t. */
#include <stdint.h>
#include <string.h>

void matmul(int m, int n, int k, int tile, const int32_t *a,
            const int32_t *b, int32_t *c) {
    if (tile == 0) {
        for (int i = 0; i < m; i++)
            for (int j = 0; j < n; j++) {
                int32_t sum = 0;
                for (int p = 0; p < k; p++)
                    sum += a[i*k+p] * b[p*n+j];
                c[i*n+j] = sum;
            }
        return;
    }
    memset(c, 0, (size_t)m*n*sizeof(*c));
    for (int j0 = 0; j0 < n; j0 += tile) {
        int end = j0 + tile < n ? j0 + tile : n;
        for (int i = 0; i < m; i++)
            for (int p = 0; p < k; p++)
                for (int j = j0; j < end; j++)
                    c[i*n+j] += a[i*k+p] * b[p*n+j];
    }
}
