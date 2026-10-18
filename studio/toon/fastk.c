// Fast kernels for the shaded-2D renderer. Built with: gcc -O3 -march=native -shared -fPIC fastk.c -o libfastk.so -lm
#include <math.h>
#include <stddef.h>

static inline float clampf(float x, float a, float b) { return x < a ? a : (x > b ? b : x); }
static inline float sstep(float e0, float e1, float x) {
    float t = clampf((x - e0) / (e1 - e0), 0.f, 1.f);
    return t * t * (3.f - 2.f * t);
}

// ---------------------------------------------------------------- SDF primitives on a grid
void sdf_circle(float *out, int h, int w, const float *xs, const float *ys, float cx, float cy, float r) {
    for (int j = 0; j < h; j++) {
        float dy = ys[j] - cy, dy2 = dy * dy;
        float *o = out + (size_t)j * w;
        for (int i = 0; i < w; i++) { float dx = xs[i] - cx; o[i] = sqrtf(dx * dx + dy2) - r; }
    }
}

void sdf_capsule(float *out, int h, int w, const float *xs, const float *ys,
                 float ax, float ay, float bx, float by, float r1, float r2) {
    float bax = bx - ax, bay = by - ay, bb = bax * bax + bay * bay + 1e-9f, dr = r2 - r1;
    for (int j = 0; j < h; j++) {
        float pay = ys[j] - ay;
        float *o = out + (size_t)j * w;
        for (int i = 0; i < w; i++) {
            float pax = xs[i] - ax;
            float t = clampf((pax * bax + pay * bay) / bb, 0.f, 1.f);
            float qx = pax - bax * t, qy = pay - bay * t;
            o[i] = sqrtf(qx * qx + qy * qy) - (r1 + dr * t);
        }
    }
}

void sdf_polyline(float *out, int h, int w, const float *xs, const float *ys, const float *pts, int n, float r) {
    for (int j = 0; j < h; j++) {
        float y = ys[j];
        float *o = out + (size_t)j * w;
        for (int i = 0; i < w; i++) {
            float x = xs[i], best = 1e30f;
            for (int k = 0; k < n - 1; k++) {
                float ax = pts[2 * k], ay = pts[2 * k + 1];
                float bax = pts[2 * k + 2] - ax, bay = pts[2 * k + 3] - ay;
                float pax = x - ax, pay = y - ay;
                float bb = bax * bax + bay * bay + 1e-9f;
                float t = clampf((pax * bax + pay * bay) / bb, 0.f, 1.f);
                float qx = pax - bax * t, qy = pay - bay * t;
                float d2 = qx * qx + qy * qy;
                if (d2 < best) best = d2;
            }
            o[i] = sqrtf(best) - r;
        }
    }
}

// shared shading of one pixel's colour from distance + gradient
// ---------------------------------------------------------------- "soft 3D" look (style 1)
// Smooth wrap-around light instead of hard cel bands, a soft gloss highlight, warm bounce light from
// below, a darker turn at the edges (the shape reads round, like clay), and a soft spread-out shadow.
static int STYLE = 0;
static float SHW = 14.f;
void set_style(int s, float shadow_soft) { STYLE = s; SHW = shadow_soft; }

static inline void shade_soft(float dv, float gx, float gy, float bevel, float rim, float spec,
                              const float *dark, const float *mid, const float *light,
                              const float *L, float lxy, float *col) {
    float s = fmaxf(-dv, 0.f) / (bevel * 1.6f);
    float u = clampf(1.f - s, 0.f, 1.f);
    float slope = s < 1.f ? u / sqrtf(fmaxf(1.f - u * u, 0.02f)) : 0.f;
    if (slope > 6.f) slope = 6.f;
    float gl = sqrtf(gx * gx + gy * gy) + 1e-6f;
    float fade = clampf(gl * 1.15f, 0.f, 1.f); fade *= fade;   // where the smoothed field flattens (the middle), so does the slope
    float nx = gx / gl * slope * fade, ny = gy / gl * slope * fade;
    float nl = sqrtf(nx * nx + ny * ny + 1.f);
    nx /= nl; ny /= nl; float nz = 1.f / nl;
    float lam = nx * L[0] + ny * L[1] + nz * L[2];
    float d = clampf((lam + 0.25f) / 1.25f, 0.f, 1.f);
    float soft = d * d * (3.f - 2.f * d);
    float cel = sstep(0.42f, 0.50f, d) * 0.5f + sstep(0.80f, 0.86f, d) * 0.5f;  // a hint of toon bands
    float k = 0.7f * soft + 0.3f * cel;
    for (int c = 0; c < 3; c++) {
        float a = k < 0.5f ? dark[c] + (mid[c] - dark[c]) * (k * 2.f) : mid[c] + (light[c] - mid[c]) * (k * 2.f - 1.f);
        col[c] = a;
    }
    float edge = sstep(0.35f, 0.95f, 1.f - nz);                  // turning away from us: a little darker
    for (int c = 0; c < 3; c++) col[c] *= 1.f - 0.22f * edge;
    float bounce = fmaxf(ny, 0.f) * edge;                         // warm light bouncing up off the floor
    col[0] += 0.10f * bounce; col[1] += 0.06f * bounce; col[2] += 0.02f * bounce;
    if (spec > 0.f) {
        float hx = L[0], hy = L[1], hz = L[2] + 1.f; float hl = sqrtf(hx * hx + hy * hy + hz * hz);
        float nh = fmaxf((nx * hx + ny * hy + nz * hz) / hl, 0.f);
        float g = powf(nh, 60.f);
        float sp = (0.55f * sstep(0.5f, 0.8f, g) + 0.45f * g) * spec * 1.4f;
        for (int c = 0; c < 3; c++) col[c] += (1.f - col[c]) * sp;
    }
    if (rim > 0.f) {
        float back = -(nx * L[0] + ny * L[1]) / lxy;
        float r = sstep(0.45f, 0.75f, 1.f - nz) * sstep(0.1f, 0.6f, back) * rim * 0.8f;
        col[0] += r * 0.65f; col[1] += r * 0.80f; col[2] += r * 1.0f;
    }
}

static inline void shade_col(float dv, float gx, float gy, float bevel, float rim, float spec,
                             const float *dark, const float *mid, const float *light,
                             const float *L, float lxy, float *col) {
    float s = fmaxf(-dv, 0.f) / bevel;
    float u = clampf(1.f - s, 0.f, 1.f);
    float slope = s < 1.f ? u / sqrtf(fmaxf(1.f - u * u, 0.02f)) : 0.f;
    if (slope > 5.f) slope = 5.f;
    float gl = sqrtf(gx * gx + gy * gy) + 1e-6f;
    float nx = gx / gl * slope, ny = gy / gl * slope;
    float nl = sqrtf(nx * nx + ny * ny + 1.f);
    nx /= nl; ny /= nl; float nz = 1.f / nl;
    float lam = nx * L[0] + ny * L[1] + nz * L[2];
    if (STYLE == 1) { shade_soft(dv, gx, gy, bevel, rim, spec, dark, mid, light, L, lxy, col); return; }
    float t1 = sstep(0.30f, 0.34f, lam), t2 = sstep(0.86f, 0.90f, lam);
    for (int c = 0; c < 3; c++) {
        float a = dark[c] + (mid[c] - dark[c]) * t1;
        col[c] = a + (light[c] - a) * t2;
    }
    if (spec > 0.f) {
        float sp = sstep(0.975f, 0.985f, lam) * spec;
        for (int c = 0; c < 3; c++) col[c] += (1.f - col[c]) * sp;
    }
    if (rim > 0.f) {
        float back = -(nx * L[0] + ny * L[1]) / lxy;
        float r = sstep(0.55f, 0.62f, 1.f - nz) * sstep(0.2f, 0.5f, back) * rim;
        col[0] += r * 0.55f; col[1] += r * 0.75f; col[2] += r * 1.0f;
    }
}

// ---------------------------------------------------------------- shaded fill (v1)
void shade(float *img, int W, int y0, int x0, int h, int w,
           const float *d, const float *dsh, const float *mask,
           float ow, float bevel, float shadow, float alpha, float rim, float spec, int flat,
           const float *dark, const float *mid, const float *light,
           const float *tint, float tint_amt, const float *L, const float *ink) {
    float lxy = sqrtf(L[0] * L[0] + L[1] * L[1]);
    for (int j = 0; j < h; j++) {
        float *row = img + ((size_t)(y0 + j) * W + x0) * 3;
        const float *dr = d + (size_t)j * w;
        for (int i = 0; i < w; i++) {
            float *p = row + 3 * i;
            float m = 1.f, msh = 1.f;
            if (mask) {
                float md = mask[(size_t)j * w + i];
                m = clampf(0.5f - md, 0.f, 1.f);
                msh = sstep(1.f, -1.f, md);
            }
            if (dsh && shadow > 0.f) {
                float a = sstep(14.f, -14.f, dsh[(size_t)j * w + i]) * shadow * alpha * msh;
                if (a > 0.f) { p[0] *= 1.f - a; p[1] *= 1.f - a; p[2] *= 1.f - a; }
            }
            float dv = dr[i];
            if (ow > 0.f) {
                float a = clampf(0.5f - (dv - ow), 0.f, 1.f) * alpha * m;
                if (a > 0.f) for (int c = 0; c < 3; c++) p[c] += (ink[c] - p[c]) * a;
            }
            float af = clampf(0.5f - dv, 0.f, 1.f) * alpha * m;
            if (af <= 0.f) continue;
            float col[3];
            if (flat) { col[0] = mid[0]; col[1] = mid[1]; col[2] = mid[2]; }
            else {
                float gx, gy;
                if (w == 1) gx = 0.f;
                else if (i == 0) gx = dr[1] - dr[0];
                else if (i == w - 1) gx = dr[i] - dr[i - 1];
                else gx = 0.5f * (dr[i + 1] - dr[i - 1]);
                if (h == 1) gy = 0.f;
                else if (j == 0) gy = d[(size_t)w + i] - dv;
                else if (j == h - 1) gy = dv - d[(size_t)(j - 1) * w + i];
                else gy = 0.5f * (d[(size_t)(j + 1) * w + i] - d[(size_t)(j - 1) * w + i]);
                shade_col(dv, gx, gy, bevel, rim, spec, dark, mid, light, L, lxy, col);
            }
            if (tint && tint_amt > 0.f) for (int c = 0; c < 3; c++) col[c] += (tint[c] - col[c]) * tint_amt;
            for (int c = 0; c < 3; c++) p[c] += (col[c] - p[c]) * af;
        }
    }
}

// ---------------------------------------------------------------- additive glow with a bright core
void glow(float *img, int W, int y0, int x0, int h, int w, const float *d,
          const float *color, float radius, float intensity, const float *core, float core_w) {
    float ci = intensity < 1.f ? intensity : 1.f;
    float inv = 1.f / radius;
    for (int j = 0; j < h; j++) {
        float *row = img + ((size_t)(y0 + j) * W + x0) * 3;
        const float *dr = d + (size_t)j * w;
        for (int i = 0; i < w; i++) {
            float dv = dr[i];
            float g = expf(-fmaxf(dv, 0.f) * inv) * intensity;
            float *p = row + 3 * i;
            if (g > 1e-4f) { p[0] += g * color[0]; p[1] += g * color[1]; p[2] += g * color[2]; }
            float a = clampf(0.5f - (dv - core_w), 0.f, 1.f) * ci;
            if (a > 0.f) for (int c = 0; c < 3; c++) p[c] += (core[c] - p[c]) * a;
        }
    }
}

// ---------------------------------------------------------------- RGBA overlay (straight alpha, uint8)
void overlay(float *img, int W, int y0, int x0, int h, int w, const unsigned char *rgba, int stride) {
    const float k = 1.f / 255.f;
    for (int j = 0; j < h; j++) {
        float *row = img + ((size_t)(y0 + j) * W + x0) * 3;
        const unsigned char *s = rgba + (size_t)j * stride;
        for (int i = 0; i < w; i++) {
            unsigned char a8 = s[4 * i + 3];
            if (!a8) continue;
            float a = a8 * k, *p = row + 3 * i;
            p[0] += (s[4 * i] * k - p[0]) * a;
            p[1] += (s[4 * i + 1] * k - p[1]) * a;
            p[2] += (s[4 * i + 2] * k - p[2]) * a;
        }
    }
}

// ================================================================ v2 kernels
void sdf_rbox(float *out, int h, int w, const float *xs, const float *ys,
              float cx, float cy, float hw, float hh, float r) {
    for (int j = 0; j < h; j++) {
        float qy = fabsf(ys[j] - cy) - hh + r;
        float *o = out + (size_t)j * w;
        for (int i = 0; i < w; i++) {
            float qx = fabsf(xs[i] - cx) - hw + r;
            float mx = fmaxf(qx, 0.f), my = fmaxf(qy, 0.f);
            o[i] = sqrtf(mx * mx + my * my) + fminf(fmaxf(qx, qy), 0.f) - r;
        }
    }
}

void sdf_ellipse(float *out, int h, int w, const float *xs, const float *ys,
                 float cx, float cy, float rx, float ry, float c, float s) {
    float m = rx < ry ? rx : ry;
    for (int j = 0; j < h; j++) {
        float y = ys[j] - cy;
        float *o = out + (size_t)j * w;
        for (int i = 0; i < w; i++) {
            float x = xs[i] - cx;
            float u = (x * c + y * s) / rx, v = (-x * s + y * c) / ry;
            o[i] = (sqrtf(u * u + v * v) - 1.f) * m;
        }
    }
}

// Shaded fill where the drop shadow reuses the same distance field shifted by whole pixels.
void shade2(float *img, int W, int y0, int x0, int h, int w,
            const float *df, int fw, int fh, int fox, int foy, int sox, int soy, const float *mask,
            float ow, float bevel, float shadow, float alpha, float rim, float spec, int flat,
            const float *dark, const float *mid, const float *light,
            const float *tint, float tint_amt, const float *L, const float *ink) {
    float lxy = sqrtf(L[0] * L[0] + L[1] * L[1]);
    float top[3];
    {
        float lam = L[2];
        float t1 = sstep(0.30f, 0.34f, lam), t2 = sstep(0.86f, 0.90f, lam);
        for (int c = 0; c < 3; c++) { float a = dark[c] + (mid[c] - dark[c]) * t1; top[c] = a + (light[c] - a) * t2; }
        if (spec > 0.f) { float sp = sstep(0.975f, 0.985f, lam) * spec; for (int c = 0; c < 3; c++) top[c] += (1.f - top[c]) * sp; }
    }
    for (int j = 0; j < h; j++) {
        int fj = j + foy;
        float *row = img + ((size_t)(y0 + j) * W + x0) * 3;
        const float *dr = df + (size_t)fj * fw + fox;
        int sj = fj - soy;
        for (int i = 0; i < w; i++) {
            float *p = row + 3 * i;
            float m = 1.f, msh = 1.f;
            if (mask) {
                float md = mask[(size_t)j * w + i];
                m = clampf(0.5f - md, 0.f, 1.f);
                msh = sstep(1.f, -1.f, md);
            }
            if (shadow > 0.f) {
                int si = i + fox - sox;
                if (sj >= 0 && sj < fh && si >= 0 && si < fw) {
                    float a = sstep(SHW, -SHW, df[(size_t)sj * fw + si]) * shadow * alpha * msh;
                    if (a > 0.f) { p[0] *= 1.f - a; p[1] *= 1.f - a; p[2] *= 1.f - a; }
                }
            }
            float dv = dr[i];
            if (ow > 0.f) {
                float a = clampf(0.5f - (dv - ow), 0.f, 1.f) * alpha * m;
                if (a > 0.f) for (int c = 0; c < 3; c++) p[c] += (ink[c] - p[c]) * a;
            }
            float af = clampf(0.5f - dv, 0.f, 1.f) * alpha * m;
            if (af <= 0.f) continue;
            float col[3];
            if (flat) { col[0] = mid[0]; col[1] = mid[1]; col[2] = mid[2]; }
            else if (STYLE == 0 && -dv >= bevel) { col[0] = top[0]; col[1] = top[1]; col[2] = top[2]; }
            else {
                int fi = i + fox;
                float gx, gy;
                if (fi <= 0) gx = df[(size_t)fj * fw + 1] - df[(size_t)fj * fw];
                else if (fi >= fw - 1) gx = df[(size_t)fj * fw + fi] - df[(size_t)fj * fw + fi - 1];
                else gx = 0.5f * (df[(size_t)fj * fw + fi + 1] - df[(size_t)fj * fw + fi - 1]);
                if (fj <= 0) gy = df[(size_t)fw + fi] - df[fi];
                else if (fj >= fh - 1) gy = df[(size_t)fj * fw + fi] - df[(size_t)(fj - 1) * fw + fi];
                else gy = 0.5f * (df[(size_t)(fj + 1) * fw + fi] - df[(size_t)(fj - 1) * fw + fi]);
                shade_col(dv, gx, gy, bevel, rim, spec, dark, mid, light, L, lxy, col);
            }
            if (tint && tint_amt > 0.f) for (int c = 0; c < 3; c++) col[c] += (tint[c] - col[c]) * tint_amt;
            for (int c = 0; c < 3; c++) p[c] += (col[c] - p[c]) * af;
        }
    }
}

void to_u8(const float *img, unsigned char *out, size_t n) {
    for (size_t k = 0; k < n; k++) {
        float v = img[k];
        v = v < 0.f ? 0.f : (v > 1.f ? 1.f : v);
        out[k] = (unsigned char)(v * 255.f + 0.5f);
    }
}

void add_light(float *img, int W, int y0, int x0, int h, int w, const unsigned char *src, int stride, int ch, float k) {
    k /= 255.f;
    for (int j = 0; j < h; j++) {
        float *row = img + ((size_t)(y0 + j) * W + x0) * 3;
        const unsigned char *s = src + (size_t)j * stride;
        for (int i = 0; i < w; i++) {
            row[3 * i] += s[ch * i] * k; row[3 * i + 1] += s[ch * i + 1] * k; row[3 * i + 2] += s[ch * i + 2] * k;
        }
    }
}

void flash(float *img, size_t npix, float r, float g, float b, float a) {
    for (size_t k = 0; k < npix; k++) {
        img[3 * k] += (r - img[3 * k]) * a; img[3 * k + 1] += (g - img[3 * k + 1]) * a; img[3 * k + 2] += (b - img[3 * k + 2]) * a;
    }
}

void sdf_heart(float *out, int h, int w, const float *xs, const float *ys, float cx, float cy, float s) {
    const float r2 = 0.35355339f;
    for (int j = 0; j < h; j++) {
        float py = -(ys[j] - cy) / s + 0.62f;
        float *o = out + (size_t)j * w;
        for (int i = 0; i < w; i++) {
            float px = fabsf(xs[i] - cx) / s, d;
            if (py + px > 1.f) {
                float ax = px - 0.25f, ay = py - 0.75f;
                d = sqrtf(ax * ax + ay * ay) - r2;
            } else {
                float m = 0.5f * fmaxf(px + py, 0.f);
                float d1 = px * px + (py - 1.f) * (py - 1.f);
                float d2 = (px - m) * (px - m) + (py - m) * (py - m);
                float sg = (px - py) > 0.f ? 1.f : ((px - py) < 0.f ? -1.f : 0.f);
                d = sqrtf(fminf(d1, d2)) * sg;
            }
            o[i] = d * s;
        }
    }
}

void smin(float *d, const float *e, size_t n, float k) {
    float ik = 0.5f / k;
    for (size_t i = 0; i < n; i++) {
        float a = d[i], b = e[i];
        float h = clampf(0.5f + (b - a) * ik, 0.f, 1.f);
        d[i] = b + (a - b) * h - k * h * (1.f - h);
    }
}
