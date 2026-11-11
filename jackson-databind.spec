Name:		jackson-databind
Version:	2.23.0
Release:	2
Summary:	General data-binding package for Jackson
Group:		Development/Java
License:	ASL 2.0
URL:		https://github.com/FasterXML/jackson-databind
Source0:	https://github.com/FasterXML/jackson-databind/archive/refs/tags/jackson-databind-%{version}.tar.gz#/jackson-databind-%{version}.tar.gz
# Gradle 9.9.1 strictly pins 2.22.3. No prebuilt jars.
Source1:	https://github.com/FasterXML/jackson-databind/archive/refs/tags/jackson-databind-2.22.3.tar.gz#/jackson-databind-2.22.3.tar.gz

BuildArch:	noarch
BuildRequires:	mvn(com.fasterxml.jackson:jackson-base:pom::)
BuildRequires:	mvn(com.fasterxml.jackson:jackson-bom:pom::)
BuildRequires:	mvn(com.fasterxml.jackson:jackson-parent:pom::)
BuildRequires:	mvn(com.fasterxml:oss-parent:pom::)
# oss-parent pins the compiler plugin to this ASM jar.
BuildRequires:	mvn(org.ow2.asm:asm)
BuildRequires:	mvn(com.fasterxml.jackson.core:jackson-annotations)
BuildRequires:	jackson-annotations >= 2.23
BuildRequires:	mvn(com.fasterxml.jackson.core:jackson-core)
BuildRequires:	jackson-core >= 2.23.0
BuildRequires:	jackson-bom >= 2.23.0
BuildRequires:	jackson-parent >= 2.23
BuildRequires:	fasterxml-oss-parent >= 81
# Literal, so the first rpmbuild -bs records them before sysjar is installed.
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildSystem:	maven

Provides:	jackson2-databind = %{version}-%{release}
Obsoletes:	jackson2-databind < %{version}-%{release}
Obsoletes:	%{name}-javadoc < %{version}

%description
Data binding for Jackson on top of the streaming API. 2.23.0
honors FAIL_ON_UNEXPECTED_VIEW_PROPERTIES for constructors,
builders, unwrapped values, and array shapes. It adds the JDK
RowSet implementations to the polymorphic deny-list, checks map
keys the same way as bean types, and fixes null handling for
primitive problem handlers, identity references, and
readerForUpdating. The Java 9 module is
com.fasterxml.jackson.databind. Tests are skipped.
2.23.0 stays the default jar. Gradle 9.9.1 strictly pins 2.22.3,
so that jar is installed beside it.

%prep
%setup -q -n jackson-databind-jackson-databind-%{version}
%setup -q -T -D -a 1 -n jackson-databind-jackson-databind-%{version}
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete
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

# 2.22.3 side jar. It compiles against the default jackson-core 2.23.0
# and the strict jackson-annotations 2.22 jar.
mkdir -p jdb222/gen/com/fasterxml/jackson/databind/cfg jdb222/classes
sed -e 's/@package@/com.fasterxml.jackson.databind.cfg/' \
	-e 's/@projectversion@/2.22.3/' \
	-e 's/@projectgroupid@/com.fasterxml.jackson.core/' \
	-e 's/@projectartifactid@/jackson-databind/' \
	jackson-databind-jackson-databind-2.22.3/src/main/java/com/fasterxml/jackson/databind/cfg/PackageVersion.java.in \
	> jdb222/gen/com/fasterxml/jackson/databind/cfg/PackageVersion.java
grep -F -q '"2.22.3"' jdb222/gen/com/fasterxml/jackson/databind/cfg/PackageVersion.java
find jackson-databind-jackson-databind-2.22.3/src/main/java -name '*.java' ! -name 'module-info.java' > jdb222/sources.list
test "$(wc -l < jdb222/sources.list)" -eq 482
echo jdb222/gen/com/fasterxml/jackson/databind/cfg/PackageVersion.java >> jdb222/sources.list
javac --release 8 -encoding UTF-8 -Xlint:-options \
	-cp %{_javadir}/jackson-core.jar:%{_javadir}/jackson-annotations-2.22.jar \
	-d jdb222/classes @jdb222/sources.list
/bin/cp -a jackson-databind-jackson-databind-2.22.3/src/main/resources/META-INF jdb222/classes/
cat > jdb222/manifest.mf << 'EOF'
Manifest-Version: 1.0
Automatic-Module-Name: com.fasterxml.jackson.databind

EOF
jar cfm jdb222/jackson-databind.jar jdb222/manifest.mf -C jdb222/classes .
jar i jdb222/jackson-databind.jar
javap -verbose -cp jdb222/jackson-databind.jar com.fasterxml.jackson.databind.ObjectMapper | grep -F 'major version: 52'
jar --describe-module -f jdb222/jackson-databind.jar > jdb222/describe.txt
cat jdb222/describe.txt
if grep -F -q 'Unable to derive' jdb222/describe.txt; then
	exit 1
fi
grep -F -q 'com.fasterxml.jackson.databind' jdb222/describe.txt
cat > jdb222/jackson-databind.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.fasterxml.jackson.core</groupId>
  <artifactId>jackson-databind</artifactId>
  <version>2.22.3</version>
  <name>jackson-databind</name>
  <description>General data-binding functionality for Jackson</description>
  <licenses>
    <license>
      <name>Apache License, Version 2.0</name>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>com.fasterxml.jackson.core</groupId>
      <artifactId>jackson-core</artifactId>
      <version>2.22.3</version>
    </dependency>
    <dependency>
      <groupId>com.fasterxml.jackson.core</groupId>
      <artifactId>jackson-annotations</artifactId>
      <version>2.22</version>
    </dependency>
  </dependencies>
</project>
EOF

%install -p
sysjar install --buildroot %{buildroot} \
	--artifact jdb222/jackson-databind.pom:jdb222/jackson-databind.jar \
	--file-name jackson-databind-2.22.3 \
	--filelist .mfiles222
# 2.23 owns jackson-databind.sysjar. 2.22.3 keeps a second index.
/bin/mv %{buildroot}/usr/share/sysjar/index/com.fasterxml.jackson.core/jackson-databind.sysjar \
	%{buildroot}/usr/share/sysjar/index/com.fasterxml.jackson.core/jackson-databind-2.22.3.sysjar
sed -i 's|/usr/share/sysjar/index/com.fasterxml.jackson.core/jackson-databind\.sysjar|/usr/share/sysjar/index/com.fasterxml.jackson.core/jackson-databind-2.22.3.sysjar|' .mfiles222

%install -a
while IFS= read -r line; do
	grep -qxF -- "$line" .mfiles || printf '%s\n' "$line" >> .mfiles
done < .mfiles222

%check -a
cat > JdbSmoke.java << 'EOF'
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
public class JdbSmoke {
	public static void main(String[] args) throws Exception {
		ObjectMapper mapper = new ObjectMapper();
		JsonNode node = mapper.readTree("{\"k\":\"gradle\"}");
		if (!"gradle".equals(node.get("k").asText())) {
			throw new RuntimeException(node.toString());
		}
		System.out.println(args[0] + " " + mapper.version() + " " + node.get("k").asText());
	}
}
EOF
CP223=%{buildroot}%{_javadir}/jackson-databind.jar:%{_javadir}/jackson-core.jar:%{_javadir}/jackson-annotations.jar:%{_javadir}/fastdoubleparser.jar
javac --release 8 -encoding UTF-8 -Xlint:-options -cp "$CP223" JdbSmoke.java
java -cp "$CP223:." JdbSmoke jdb223_ok > check223.log
cat check223.log
grep -F -q 'jdb223_ok 2.23.0 gradle' check223.log
CP222=%{buildroot}%{_javadir}/jackson-databind-2.22.3.jar:%{_javadir}/jackson-core.jar:%{_javadir}/jackson-annotations-2.22.jar:%{_javadir}/fastdoubleparser.jar
javac --release 8 -encoding UTF-8 -Xlint:-options -cp "$CP222" JdbSmoke.java
java -cp "$CP222:." JdbSmoke jdb222_ok > check222.log
cat check222.log
grep -F -q 'jdb222_ok 2.22.3 gradle' check222.log

%files -f .mfiles
%doc LICENSE README.md SECURITY.md release-notes/VERSION-2.x
