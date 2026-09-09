#define _POSIX_C_SOURCE 200809L
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static uint32_t state = 501;
static uint32_t random_u32(void) {
    state ^= state << 13; state ^= state >> 17; state ^= state << 5;
    return state;
}
static double seconds(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}
static int minimum(int a, int b) { return a < b ? a : b; }

/* Row-major arrays, no BLAS, no threads, identical increasing-k reductions. */
static void ijk(const float *restrict a, const float *restrict b,
                float *restrict c, int m, int kdim, int n, int tile) {
    (void)tile;
    for (int i = 0; i < m; ++i)
        for (int j = 0; j < n; ++j) {
            float sum = 0;
            for (int k = 0; k < kdim; ++k) sum += a[i*kdim+k] * b[k*n+j];
            c[i*n+j] = sum;
        }
}
static void ikj(const float *restrict a, const float *restrict b,
                float *restrict c, int m, int kdim, int n, int tile) {
    (void)tile;
    memset(c, 0, sizeof(float)*m*n);
    for (int i = 0; i < m; ++i)
        for (int k = 0; k < kdim; ++k) {
            float v = a[i*kdim+k];
            for (int j = 0; j < n; ++j) c[i*n+j] += v * b[k*n+j];
        }
}
static void blocked(const float *restrict a, const float *restrict b,
                    float *restrict c, int m, int kdim, int n, int tile) {
    memset(c, 0, sizeof(float)*m*n);
    for (int ii = 0; ii < m; ii += tile)
        for (int jj = 0; jj < n; jj += tile)
            for (int kk = 0; kk < kdim; kk += tile)
                for (int i = ii; i < minimum(ii+tile,m); ++i)
                    for (int k = kk; k < minimum(kk+tile,kdim); ++k) {
                        float v = a[i*kdim+k];
                        for (int j = jj; j < minimum(jj+tile,n); ++j)
                            c[i*n+j] += v * b[k*n+j];
                    }
}
typedef void (*multiply)(const float *, const float *, float *, int, int, int, int);
struct candidate { const char *name; multiply fn; int tile; };
static volatile double sink;

int main(void) {
    const int shapes[][3] = {{64,64,64},{128,512,64},{256,128,256},{127,257,65}};
    const struct candidate methods[] = {{"ijk",ijk,0},{"ikj",ikj,0},
        {"blocked",blocked,8},{"blocked",blocked,16},{"blocked",blocked,32},{"blocked",blocked,64},
        {"blocked",blocked,128},{"blocked",blocked,256}};
    enum { trials=9, count=8 };
    printf("{\"trials\":%d,\"seed\":501,\"rows\":[\n",trials);
    int first = 1;
    for (int shape=0; shape<4; ++shape) {
        int m=shapes[shape][0],kd=shapes[shape][1],n=shapes[shape][2];
        float *a=malloc(sizeof(float)*m*kd), *b=malloc(sizeof(float)*kd*n);
        float *c=malloc(sizeof(float)*m*n);
        double *ref=malloc(sizeof(double)*m*n);
        if (!a || !b || !c || !ref) return 2;
        for (int i=0;i<m*kd;++i) a[i]=((int)(random_u32()%2049)-1024)/1024.0f;
        for (int i=0;i<kd*n;++i) b[i]=((int)(random_u32()%2049)-1024)/1024.0f;
        for (int i=0;i<m;++i) for (int j=0;j<n;++j) {
            double s=0;
            for (int k=0;k<kd;++k) s+=(double)a[i*kd+k]*b[k*n+j];
            ref[i*n+j]=s;
        }
        double errors[count],samples[count][trials];
        int reps[count];
        for (int q=0;q<count;++q) {
            methods[q].fn(a,b,c,m,kd,n,methods[q].tile);
            errors[q]=0;
            for (int i=0;i<m*n;++i) {
                double error=fabs(c[i]-ref[i]);
                if (!isfinite(c[i]) || error>1e-4+1e-5*fabs(ref[i])) {
                    fprintf(stderr,"validation failure shape=%d candidate=%d index=%d\n",shape,q,i);
                    return 3;
                }
                if (error>errors[q]) errors[q]=error;
            }
            for (int w=0;w<5;++w) methods[q].fn(a,b,c,m,kd,n,methods[q].tile);
            double start=seconds();
            for (int w=0;w<10;++w) methods[q].fn(a,b,c,m,kd,n,methods[q].tile);
            double per=(seconds()-start)/10;
            reps[q]=(int)(0.015/per);
            if (reps[q]<1) reps[q]=1;
            if (reps[q]>10000) reps[q]=10000;
        }
        for (int t=0;t<trials;++t) {
            int order[count];
            for (int q=0;q<count;++q) order[q]=q;
            for(int q=count-1;q>0;--q) { int j=random_u32()%(q+1),tmp=order[q];order[q]=order[j];order[j]=tmp; }
            for (int pos=0;pos<count;++pos) {
                int q=order[pos];
                double start=seconds();
                for (int r=0;r<reps[q];++r) methods[q].fn(a,b,c,m,kd,n,methods[q].tile);
                samples[q][t]=(seconds()-start)*1e6/reps[q];
                sink+=c[(t*107)%(m*n)];
            }
        }
        for (int q=0;q<count;++q) {
            printf("%s{\"m\":%d,\"k\":%d,\"n\":%d,\"method\":\"%s\",\"tile\":%d,\"repeats\":%d,\"max_abs_error\":%.9g,\"samples_us\":[",
                   first?"":",\n",m,kd,n,methods[q].name,methods[q].tile,reps[q],errors[q]);
            first=0;
            for(int t=0;t<trials;++t) printf("%s%.9g",t?",":"",samples[q][t]);
            printf("]}");
        }
        free(a);free(b);free(c);free(ref);
    }
    printf("\n],\"checksum\":%.9g}\n",sink);
    return 0;
}
