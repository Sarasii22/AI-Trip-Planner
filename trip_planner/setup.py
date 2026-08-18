from setuptools import find_packages, setup
from typing import List

def get_requirements() -> List[str]:
    """This function will return the list of requirements"""
    requirement_list: List[str] = []

    try:
        #open and read the requirements.txt file
        with open("requirements.txt", "r") as file:
            #read lines from the file
            lines = file.readlines()
            #process each line
            for line in lines:
                #strip whitespace and newline characters
                requirement = line.strip()
                #skip empty lines and comments
                if requirement and requirement != '-e .':
                    requirement_list.append(requirement)
    except FileNotFoundError:
        print("requirements.txt file not found. Please ensure it exists in the project directory.")


    return requirement_list

print(get_requirements())
setup(
    name="AI trip_planner",
    version="0.0.1",
    author="Sarasi Madahasi",
    author_email="sarasimadahasi@gmail.com",
    packages=find_packages(),
    install_requires=get_requirements()
)