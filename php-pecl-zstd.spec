#
# Conditional build:
%bcond_without	tests		# build without tests
%bcond_without	tests_online	# build without online tests

%if 0%{?_pld_builder:1}
%undefine	with_tests_online
%endif

%define		php_name	php%{?php_suffix}
%define		modname	zstd
Summary:	%{modname} - Zstandard extension
Name:		%{php_name}-pecl-%{modname}
Version:	0.13.3
Release:	1
License:	PHP 3.01
Group:		Development/Languages/PHP
Source0:	https://pecl.php.net/get/%{modname}-%{version}.tgz
# Source0-md5:	a1064d2232126c45ca29b454f9e583bf
URL:		https://pecl.php.net/package/zstd/
BuildRequires:	%{php_name}-cli
BuildRequires:	%{php_name}-devel
BuildRequires:	rpmbuild(macros) >= 1.666
BuildRequires:	zstd-devel
%if %{with tests}
BuildRequires:	%{php_name}-openssl
BuildRequires:	%{php_name}-pcre
%endif
%{?requires_php_extension}
Provides:	php(%{modname}) = %{version}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
PHP extension for compression and decompression with Zstandard
library.

%prep
%setup -qc
mv %{modname}-%{version}/* .
rm -r zstd

cat <<'EOF' > run-tests.sh
#!/bin/sh
export NO_INTERACTION=1 REPORT_EXIT_STATUS=1 MALLOC_CHECK_=2
exec %{__make} test \
	PHP_EXECUTABLE=%{__php} \
	PHP_TEST_SHARED_SYSTEM_EXTENSIONS="openssl" \
	RUN_TESTS_SETTINGS="-q $*"
EOF
chmod +x run-tests.sh

xfail() {
	local t=$1
	test -f $t
	cat >> $t <<-EOF

	--XFAIL--
	Skip
	EOF
}

while read line; do
	t=${line##*\[}; t=${t%\]}
	xfail $t
done << 'EOF'
zstd_compress(): compress level [tests/008.phpt]
%ifarch x32
zstd_compress(): basic functionality [tests/001.phpt]
zstd_compress(): variation [tests/003.phpt]
namespace: Zstd\compress()/uncompress() [tests/007.phpt]
zstd_compress(): compress level [tests/009.phpt]
%endif
EOF

%build
phpize
%configure \
	--with-libzstd
%{__make}

# simple module load test
%{__php} -n -q \
	-d extension_dir=modules \
	-d extension=%{modname}.so \
	-m > modules.log
grep %{modname} modules.log

%if %{with tests}
%{!?tests_online:SKIP_ONLINE_TESTS=1} \
./run-tests.sh --show-diff
%endif

%install
rm -rf $RPM_BUILD_ROOT
%{__make} install \
	EXTENSION_DIR=%{php_extensiondir} \
	INSTALL_ROOT=$RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d
cat <<'EOF' > $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d/%{modname}.ini
; Enable %{modname} extension module
extension=%{modname}.so
EOF

# no -devel yet
%{__rm} $RPM_BUILD_ROOT%{php_includedir}/ext/zstd/php_zstd.h

%clean
rm -rf $RPM_BUILD_ROOT

%post
%php_webserver_restart

%postun
if [ "$1" = 0 ]; then
	%php_webserver_restart
fi

%files
%defattr(644,root,root,755)
%doc README.md
%config(noreplace) %verify(not md5 mtime size) %{php_sysconfdir}/conf.d/%{modname}.ini
%attr(755,root,root) %{php_extensiondir}/%{modname}.so
