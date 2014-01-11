%{?_javapackages_macros:%_javapackages_macros}
Name:          jackson-databind
Version:       2.2.2
Release:       3.1%{?dist}
Summary:       General data-binding package for Jackson (2.x)
License:       ASL 2.0 and LGPLv2+
URL:           http://wiki.fasterxml.com/JacksonHome
Source0:       https://github.com/FasterXML/jackson-databind/archive/%{name}-%{version}.tar.gz
# jackson-databind package don't include the license file
# https://github.com/FasterXML/jackson-databind/issues/264
Source1:       http://www.apache.org/licenses/LICENSE-2.0.txt
Source2:       http://www.gnu.org/licenses/lgpl-2.1.txt

BuildRequires: java-devel
BuildRequires: mvn(com.fasterxml:oss-parent) >= 10
BuildRequires: mvn(com.fasterxml.jackson.core:jackson-annotations) >= %{version}
BuildRequires: mvn(com.fasterxml.jackson.core:jackson-core) >= %{version}

# test deps
BuildRequires: mvn(cglib:cglib)
BuildRequires: mvn(junit:junit)
BuildRequires: mvn(org.codehaus.groovy:groovy)

BuildRequires: maven-local
BuildRequires: maven-enforcer-plugin
BuildRequires: maven-plugin-build-helper
BuildRequires: maven-plugin-bundle
BuildRequires: maven-site-plugin
BuildRequires: maven-surefire-provider-junit4
BuildRequires: replacer
# bundle-plugin Requires
#BuildRequires: mvn(org.sonatype.aether:aether)

Provides:      jackson2-databind = %{version}-%{release}
Obsoletes:     jackson2-databind < %{version}-%{release}

BuildArch:     noarch

%description
General data-binding functionality for Jackson:
works on core streaming API.

%package javadoc
Summary:       Javadoc for %{name}

%description javadoc
This package contains javadoc for %{name}.

%prep
%setup -q -n %{name}-%{name}-%{version}

cp -p %{SOURCE1} .
cp -p %{SOURCE2} .
sed -i 's/\r//' LICENSE-2.0.txt lgpl-2.1.txt

# unavailable test deps
%pom_remove_dep org.hibernate:hibernate-cglib-repack
rm src/test/java/com/fasterxml/jackson/databind/interop/TestHibernate.java
# Off test that require connection with the web
rm src/test/java/com/fasterxml/jackson/databind/ser/TestJdkTypes.java \
 src/test/java/com/fasterxml/jackson/databind/deser/TestJdkTypes.java \
 src/test/java/com/fasterxml/jackson/databind/TestJDKSerialization.java

%build

%mvn_file : %{name}
%mvn_build -- -Dmaven.test.failure.ignore=true

%install
%mvn_install

%files -f .mfiles
%doc LICENSE-2.0.txt lgpl-2.1.txt README.md release-notes/*

%files javadoc -f .mfiles-javadoc
%doc LICENSE-2.0.txt lgpl-2.1.txt

%changelog
* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.2.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Mon Jul 22 2013 gil cattaneo <puntogil@libero.it> 2.2.2-2
- review fixes

* Tue Jul 16 2013 gil cattaneo <puntogil@libero.it> 2.2.2-1
- 2.2.2
- renamed jackson-databind

* Tue May 07 2013 gil cattaneo <puntogil@libero.it> 2.2.1-1
- 2.2.1

* Wed Oct 24 2012 gil cattaneo <puntogil@libero.it> 2.1.0-1
- update to 2.1.0
- renamed jackson2-databind

* Thu Sep 13 2012 gil cattaneo <puntogil@libero.it> 2.0.6-1
- initial rpm