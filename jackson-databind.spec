Name:		jackson-databind
Version:	2.21.8
Release:	1
Summary:	General data-binding package for Jackson
Group:		Development/Java
License:	ASL 2.0
URL:		https://github.com/FasterXML/jackson-databind
Source0:	https://github.com/FasterXML/jackson-databind/archive/refs/tags/jackson-databind-%{version}.tar.gz#/jackson-databind-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	mvn(com.fasterxml.jackson:jackson-base:pom::)
BuildRequires:	mvn(com.fasterxml.jackson:jackson-bom:pom::)
BuildRequires:	mvn(com.fasterxml.jackson:jackson-parent:pom::)
BuildRequires:	mvn(com.fasterxml:oss-parent:pom::)
# oss-parent pins the compiler plugin to this ASM jar.
BuildRequires:	mvn(org.ow2.asm:asm)
BuildRequires:	mvn(com.fasterxml.jackson.core:jackson-annotations)
BuildRequires:	jackson-annotations >= 2.21-2
BuildRequires:	mvn(com.fasterxml.jackson.core:jackson-core)
BuildRequires:	jackson-core >= 2.21.8
# Literal, so the first rpmbuild -bs records them before sysjar is installed.
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildSystem:	maven

Provides:	jackson2-databind = %{version}-%{release}
Obsoletes:	jackson2-databind < %{version}-%{release}
Obsoletes:	%{name}-javadoc < %{version}

%description
Data binding for Jackson on top of the streaming API. 2.21.8 reports
a JsonValue cycle as JsonMappingException, makes BeanDescription
property lookup safe to call concurrently, and validates type
parameters of polymorphic ids (CVE-2026-110879). The Java 9 module
is com.fasterxml.jackson.databind. Tests are skipped.

%prep
%setup -q -n jackson-databind-jackson-databind-%{version}
# JDK 21 activates a profile that passes -source and --release together.
# Jacoco and the enforcer run during package. Replacer, moditect and
# the bundle plugin are not packaged. jackson-base points the jar
# plugin at a manifest those plugins never write.
python - <<'PY'
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "http://maven.apache.org/POM/4.0.0"
ET.register_namespace("", NS)
ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")

def local(tag):
    return tag.rsplit("}", 1)[-1]

def artifact_of(elem):
    for item in elem:
        if local(item.tag) == "artifactId":
            return (item.text or "").strip()
    return ""

def child_text(elem, name):
    for item in elem:
        if local(item.tag) == name:
            return (item.text or "").strip()
    return ""

drop = {
    "jacoco-maven-plugin",
    "maven-enforcer-plugin",
    "maven-surefire-plugin",
    "maven-javadoc-plugin",
    "replacer",
    "cyclonedx-maven-plugin",
    "moditect-maven-plugin",
    "build-helper-maven-plugin",
    "gradle-module-metadata-maven-plugin",
    "animal-sniffer-maven-plugin",
}
drop_profiles = {"java11", "java17", "java21", "errorprone"}
path = Path("pom.xml")
tree = ET.parse(path)
root = tree.getroot()
removed = []
for parent in list(root.iter()):
    for child in list(parent):
        name = local(child.tag)
        if name in ("repositories", "pluginRepositories"):
            parent.remove(child)
            removed.append(name)
            continue
        if name == "profile" and child_text(child, "id") in drop_profiles:
            parent.remove(child)
            removed.append("profile:" + child_text(child, "id"))
            continue
        if name != "plugin":
            continue
        artifact = artifact_of(child)
        if artifact in drop:
            parent.remove(child)
            removed.append(artifact)
for parent in list(root.iter()):
    if local(parent.tag) != "dependencies":
        continue
    for child in list(parent):
        if local(child.tag) != "dependency":
            continue
        if child_text(child, "scope") == "test":
            parent.remove(child)
            removed.append("dep:" + artifact_of(child))
missing = drop - set(removed)
if missing:
    raise SystemExit("not removed " + " ".join(sorted(missing)))
missing_profiles = {"profile:" + name for name in drop_profiles} - set(removed)
if missing_profiles:
    raise SystemExit("profiles not removed " + " ".join(sorted(missing_profiles)))

plugins = None
for child in root:
    if local(child.tag) != "build":
        continue
    for item in child:
        if local(item.tag) == "plugins":
            plugins = item
if plugins is None:
    raise SystemExit("build/plugins missing")
tag = "{" + NS + "}"
jar = ET.Element(tag + "plugin")
group = ET.SubElement(jar, tag + "groupId")
group.text = "org.apache.maven.plugins"
artifact = ET.SubElement(jar, tag + "artifactId")
artifact.text = "maven-jar-plugin"
version = ET.SubElement(jar, tag + "version")
version.text = "3.5.1"
conf = ET.SubElement(jar, tag + "configuration")
conf.set("combine.self", "override")
archive = ET.SubElement(conf, tag + "archive")
entries = ET.SubElement(archive, tag + "manifestEntries")
flag = ET.SubElement(entries, tag + "Multi-Release")
flag.text = "true"
plugins.insert(0, jar)
tree.write(path, encoding="UTF-8", xml_declaration=True)
text = path.read_text(encoding="utf-8")
if "manifestFile" in text or "error_prone_core" in text or "java21" in text:
    raise SystemExit("unwanted pom text survived")
if "jackson-annotations" not in text or "jackson-core" not in text:
    raise SystemExit("jackson dependency missing")

src = Path("src/main/java/com/fasterxml/jackson/databind/cfg/PackageVersion.java.in")
body = src.read_text(encoding="utf-8")
body = body.replace("@package@", "com.fasterxml.jackson.databind.cfg")
body = body.replace("@projectversion@", "%{version}")
body = body.replace("@projectgroupid@", "com.fasterxml.jackson.core")
body = body.replace("@projectartifactid@", "jackson-databind")
for token in ("@package@", "@projectversion@", "@projectgroupid@", "@projectartifactid@"):
    if token in body:
        raise SystemExit("placeholder left")
src.with_suffix("").write_text(body, encoding="utf-8")
src.unlink()
license_file = Path("LICENSE")
if not license_file.is_file():
    raise SystemExit("LICENSE missing")
meta = Path("src/main/resources/META-INF")
meta.mkdir(parents=True, exist_ok=True)
(meta / "LICENSE").write_bytes(license_file.read_bytes())
# jackson-base points jar:jar at this path. The parent pluginManagement
# entry survives a child combine.self override.
(meta / "MANIFEST.MF").write_text(
    "Manifest-Version: 1.0\nMulti-Release: true\n",
    encoding="utf-8",
)
PY

%build -a
mkdir -p target/classes/META-INF/versions/9
javac --release 9 \
	--module-path /usr/share/java/jackson-annotations.jar:/usr/share/java/jackson-core.jar \
	--patch-module com.fasterxml.jackson.databind=target/classes \
	-d target/classes/META-INF/versions/9 \
	src/moditect/module-info.java
test -s target/classes/META-INF/versions/9/module-info.class
jar uf target/jackson-databind-%{version}.jar -C target/classes META-INF/versions/9/module-info.class
java --module-path target/jackson-databind-%{version}.jar:/usr/share/java/jackson-annotations.jar:/usr/share/java/jackson-core.jar --describe-module com.fasterxml.jackson.databind | grep -q '^com.fasterxml.jackson.databind'

%files -f .mfiles
%doc LICENSE README.md SECURITY.md release-notes/VERSION-2.x
