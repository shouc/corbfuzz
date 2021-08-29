
dnl $Id$
dnl config.m4 for extension hsfuzz
m4_include(ax_cxx_compile_stdcxx_11.m4)
AX_CXX_COMPILE_STDCXX_11

PHP_ARG_ENABLE(hsfuzz, whether to enable hsfuzz, [ --enable-hsfuzz   Enable hsfuzz])

if test "$PHP_hsfuzz" != "no"; then
  AC_DEFINE(HAVE_HSFUZZ, 1, [whether hsfuzz is enabled])
  PHP_REQUIRE_CXX()
  PHP_ADD_LIBRARY(stdc++, 1, HSFUZZ_SHARED_LIBADD)
  PHP_SUBST(HSFUZZ_SHARED_LIBADD)
  PHP_SUBST(Z3_SHARED_LIBADD)

  PHP_NEW_EXTENSION(hsfuzz, hsfuzz.cc, $ext_shared)
  PHP_ADD_MAKEFILE_FRAGMENT
  PHP_INSTALL_HEADERS([ext/hsfuzz], [php_hsfuzz.h])
fi
