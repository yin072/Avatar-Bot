from setuptools import setup, find_packages

setup(
    name="avatar_bot",
    version="0.1",
    packages=find_packages(),
    package_dir={"": "."},  # 指定包根目录
    entry_points={
        'console_scripts': [
            'avatar=bot.agent.Api:cli_main',  # 添加这行
        ],
    },
)