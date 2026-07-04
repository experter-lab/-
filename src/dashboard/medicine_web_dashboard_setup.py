from setuptools import setup

package_name = "medicine_web_dashboard"

setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="cgz",
    maintainer_email="user@example.com",
    description="Web dashboard prototype for the medicine delivery robot.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "web_dashboard_node = medicine_web_dashboard.web_dashboard_node:main",
        ],
    },
)
