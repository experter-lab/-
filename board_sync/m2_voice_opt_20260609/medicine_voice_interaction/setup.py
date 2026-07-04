from setuptools import find_packages, setup


package_name = "medicine_voice_interaction"


setup(
    name=package_name,
    version="0.0.1",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="cgz",
    maintainer_email="user@example.com",
    description="Voice command and TTS bridge nodes for the medicine delivery robot.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "voice_console_node = medicine_voice_interaction.voice_console_node:main",
            "voice_command_dispatcher_node = medicine_voice_interaction.voice_command_dispatcher_node:main",
            "m2_voice_bridge_node = medicine_voice_interaction.m2_voice_bridge_node:main",
            "ai_voice_chat_bridge_node = medicine_voice_interaction.ai_voice_chat_bridge_node:main",
            "dashscope_asr_bridge_node = medicine_voice_interaction.dashscope_asr_bridge_node:main",
            "vision_drug_voice_bridge_node = medicine_voice_interaction.vision_drug_voice_bridge_node:main",
        ],
    },
)
