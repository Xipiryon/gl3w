#!/usr/bin/env python

#   This file is part of gl3es, hosted at https://github.com/skaslev/gl3es
#
#   This is free and unencumbered software released into the public domain.
#
#   Anyone is free to copy, modify, publish, use, compile, sell, or
#   distribute this software, either in source code form or as a compiled
#   binary, for any purpose, commercial or non-commercial, and by any
#   means.
#
#   In jurisdictions that recognize copyright laws, the author or authors
#   of this software dedicate any and all copyright interest in the
#   software to the public domain. We make this dedication for the benefit
#   of the public at large and to the detriment of our heirs and
#   successors. We intend this dedication to be an overt act of
#   relinquishment in perpetuity of all present and future rights to this
#   software under copyright law.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#   MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#   IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
#   OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#   ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#   OTHER DEALINGS IN THE SOFTWARE.

# Allow Python 2.6+ to use the print() function
from __future__ import print_function

import argparse
import os
import re

# Try to import Python 3 library urllib.request
# and if it fails, fall back to Python 2 urllib2
try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

# UNLICENSE copyright header
UNLICENSE = r'''/*

    This file was generated with gl3es_gen.py, part of gl3es
    (hosted at https://github.com/skaslev/gl3es)

    This is free and unencumbered software released into the public domain.

    Anyone is free to copy, modify, publish, use, compile, sell, or
    distribute this software, either in source code form or as a compiled
    binary, for any purpose, commercial or non-commercial, and by any
    means.

    In jurisdictions that recognize copyright laws, the author or authors
    of this software dedicate any and all copyright interest in the
    software to the public domain. We make this dedication for the benefit
    of the public at large and to the detriment of our heirs and
    successors. We intend this dedication to be an overt act of
    relinquishment in perpetuity of all present and future rights to this
    software under copyright law.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
    OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

*/

'''

EXT_SUFFIX = ['ARB', 'EXT', 'KHR', 'OVR', 'NV', 'AMD', 'INTEL']

def is_ext(proc):
    return any(proc.endswith(suffix) for suffix in EXT_SUFFIX)

def proc_t(proc):
    return {
        'p': proc,
        'p_s': proc[2:],
        'p_t': 'PFN{0}PROC'.format(proc.upper())
    }

def write(f, s):
    f.write(s.encode('utf-8'))

parser = argparse.ArgumentParser(description='gl3es generator script')
parser.add_argument('--ext', action='store_true', help='Load extensions')
parser.add_argument('--root', type=str, default='', help='Root directory')
args = parser.parse_args()

# Create directories
if not os.path.exists(os.path.join(args.root, 'include/GLES3')):
    os.makedirs(os.path.join(args.root, 'include/GLES3'))
if not os.path.exists(os.path.join(args.root, 'src')):
    os.makedirs(os.path.join(args.root, 'src'))

# Download gl3.h
if not os.path.exists(os.path.join(args.root, 'include/GLES3/gl3.h')):
    print('Downloading gl3.h to {0}...'.format(os.path.join(args.root, 'include/GLES3/gl3.h')))
    web = urllib2.urlopen('http://www.opengl.org/registry/api/GLES3/gl3.h')
    with open(os.path.join(args.root, 'include/GLES3/gl3.h'), 'wb') as f:
        f.writelines(web.readlines())
else:
    print('Reusing gl3.h from {0}...'.format(os.path.join(args.root, 'include/GLES3')))

# Parse function names from gl3.h
print('Parsing gl3.h header...')
procs = []
p = re.compile(r'GL_APICALL.*APIENTRY\s+(\w+)')
with open(os.path.join(args.root, 'include/GLES3/gl3.h'), 'r') as f:
    for line in f:
        m = p.match(line)
        if not m:
            continue
        proc = m.group(1)
        if args.ext or not is_ext(proc):
            procs.append(proc)
procs.sort()

# Generate gl3es.h
print('Generating gl3es.h in {0}...'.format(os.path.join(args.root, 'include/GLES3')))
with open(os.path.join(args.root, 'include/GLES3/gl3es.h'), 'wb') as f:
    write(f, UNLICENSE)
    write(f, r'''#ifndef __gl3es_h_
#define __gl3es_h_

#include <GLES3/gl3.h>

#ifndef __gl_h_
#define __gl_h_
#endif

#ifdef __cplusplus
extern "C" {
#endif

#define GL3ES_OK 0
#define GL3ES_ERROR_INIT -1
#define GL3ES_ERROR_LIBRARY_OPEN -2
#define GL3ES_ERROR_OPENGL_VERSION -3

typedef void (*GL3ESglProc)(void);
typedef GL3ESglProc (*GL3ESGetProcAddressProc)(const char *proc);

/* gl3es api */
int gl3esInit(void);
int gl3esInit2(GL3ESGetProcAddressProc proc);
int gl3esIsSupported(int major, int minor);
GL3ESglProc gl3esGetProcAddress(const char *proc);

/* gl3es internal state */
''')
    write(f, 'union GL3ESProcs {\n')
    write(f, '    GL3ESglProc ptr[{0}];\n'.format(len(procs)))
    write(f, '    struct {\n')
    for proc in procs:
        write(f, '        {0[p_t]: <55} {0[p_s]};\n'.format(proc_t(proc)))
    write(f, r'''    } gl;
};

extern union GL3ESProcs gl3esProcs;

/* OpenGL functions */
''')
    for proc in procs:
        write(f, '#define {0[p]: <48} gl3esProcs.gl.{0[p_s]}\n'.format(proc_t(proc)))
    write(f, r'''
#ifdef __cplusplus
}
#endif

#endif
''')

# Generate gl3es.c
print('Generating gl3es.c in {0}...'.format(os.path.join(args.root, 'src')))
with open(os.path.join(args.root, 'src/gl3es.c'), 'wb') as f:
    write(f, UNLICENSE)
    write(f, r'''#include <GLES3/gl3.h>
#include <stdlib.h>

#define ARRAY_SIZE(x)  (sizeof(x) / sizeof((x)[0]))

#if defined(_WIN32)
#define WIN32_LEAN_AND_MEAN 1
#include <windows.h>

static HMODULE libgl;
static PROC (__stdcall *wgl_get_proc_address)(LPCSTR);

static int open_libgl(void)
{
    libgl = LoadLibraryA("libEGL.dll");
    if (!libgl)
        return GL3ES_ERROR_LIBRARY_OPEN;

    *(void **)(&wgl_get_proc_address) = GetProcAddress(libgl, "wglGetProcAddress");
    return GL3ES_OK;
}

static void close_libgl(void)
{
    FreeLibrary(libgl);
}

static GL3ESglProc get_proc(const char *proc)
{
    GL3ESglProc res;

    res = (GL3ESglProc)wgl_get_proc_address(proc);
    if (!res)
        res = (GL3ESglProc)GetProcAddress(libgl, proc);
    return res;
}
#elif defined(__APPLE__)
#include <dlfcn.h>

static void *libgl;

static int open_libgl(void)
{
    libgl = dlopen("/System/Library/Frameworks/OpenGLES.framework/OpenGL", RTLD_LAZY | RTLD_LOCAL);
    if (!libgl)
        return GL3ES_ERROR_LIBRARY_OPEN;

    return GL3ES_OK;
}

static void close_libgl(void)
{
    dlclose(libgl);
}

static GL3ESglProc get_proc(const char *proc)
{
    GL3ESglProc res;

    *(void **)(&res) = dlsym(libgl, proc);
    return res;
}
#else
#include <dlfcn.h>

static void *libgl;
static GL3ESglProc (*glx_get_proc_address)(const GLubyte *);

static int open_libgl(void)
{
    libgl = dlopen("libGL.so.1", RTLD_LAZY | RTLD_LOCAL);
    if (!libgl)
        return GL3ES_ERROR_LIBRARY_OPEN;

    *(void **)(&glx_get_proc_address) = dlsym(libgl, "glXGetProcAddressARB");
    return GL3ES_OK;
}

static void close_libgl(void)
{
    dlclose(libgl);
}

static GL3ESglProc get_proc(const char *proc)
{
    GL3ESglProc res;

    res = glx_get_proc_address((const GLubyte *)proc);
    if (!res)
        *(void **)(&res) = dlsym(libgl, proc);
    return res;
}
#endif

static struct {
    int major, minor;
} version;

static int parse_version(void)
{
    if (!glGetIntegerv)
        return GL3ES_ERROR_INIT;

    glGetIntegerv(GL_MAJOR_VERSION, &version.major);
    glGetIntegerv(GL_MINOR_VERSION, &version.minor);

    if (version.major < 3)
        return GL3ES_ERROR_OPENGL_VERSION;
    return GL3ES_OK;
}

static void load_procs(GL3ESGetProcAddressProc proc);

int gl3esInit(void)
{
    return gl3esInit2(get_proc);
}

int gl3esInit2(GL3ESGetProcAddressProc proc)
{
    int res = open_libgl();
    if (res)
        return res;

    atexit(close_libgl);
    load_procs(proc);
    return parse_version();
}

int gl3esIsSupported(int major, int minor)
{
    if (major < 3)
        return 0;
    if (version.major == major)
        return version.minor >= minor;
    return version.major >= major;
}

GL3ESglProc gl3esGetProcAddress(const char *proc)
{
    return get_proc(proc);
}

static const char *proc_names[] = {
''')
    for proc in procs:
        write(f, '    "{0}",\n'.format(proc))
    write(f, r'''};

union GL3ESProcs gl3esProcs;

static void load_procs(GL3ESGetProcAddressProc proc)
{
    size_t i;
    for (i = 0; i < ARRAY_SIZE(proc_names); i++)
        gl3esProcs.ptr[i] = proc(proc_names[i]);
}
''')

