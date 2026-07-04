from setuptools import setup

package_name = "medicine_vision_detector"

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
    description="Vision detector prototype for medicine information acquisition.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "drug_info_detector_node = medicine_vision_detector.drug_info_detector_node:main",
            "yolo_rknn_detector_node = medicine_vision_detector.yolo_rknn_detector_node:main",
        ],
    },
)
