Summary:	FedMsg CVS Publisher
Name:		fedmsg-cvs
Version:	%{version}
Release:	%{release}
License:	GPL v2
Group:		Libraries/Python
BuildRequires:	rpm-pythonprov
BuildRequires:	rpmbuild(macros) >= 1.714
Requires:	fedmsg >= 0.17
BuildArch:	noarch
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
FedMsg CVS Publisher.

%prep

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{_sbindir}
install -p fedmsg-cvs-hook.py $RPM_BUILD_ROOT%{_sbindir}/fedmsg-cvs-hook

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%doc README.md fedmsg-cvs-hook.conf
%attr(755,root,root) %{_sbindir}/fedmsg-cvs-hook
