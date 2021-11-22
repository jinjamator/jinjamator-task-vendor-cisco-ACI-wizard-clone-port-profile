# Copyright 2021 Wilhelm Putz

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import setuptools
from subprocess import check_output

command = "git describe --tags --long --dirty"
version_format = ("{tag}.dev{commitcount}+{gitsha}",)


def format_version(version, fmt):
    parts = version.split("-")
    assert len(parts) in (3, 4)
    dirty = len(parts) == 4
    tag, count, sha = parts[:3]
    if count == "0" and not dirty:
        return tag
    return fmt.format(tag=tag, commitcount=count, gitsha=sha.lstrip("g"))


version = check_output(command.split()).decode("utf-8").strip()



with open("README.rst", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    install_requires = fh.read().split("\n")




setuptools.setup(
    name="jinjamator-task-vendor-cisco-ACI-wizard-clone-port-profile",
    version=f"{version}",
    author="Wilhelm Putz",
    author_email="wilhelm.putz@kapsch.net",
    description="Cisco ACI Port-Profile Clone Task",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/jinjamator/jinjamator-task-vendor-cisco-ACI-wizard-clone-port-profile",
    packages=['jinjamator'],
    include_package_data=True,
    package_data={"": ["*"]},
    install_requires=install_requires,
    license="ASL V2",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: System :: Installation/Setup",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    zip_safe=False,
)
