# setup.py defines this project as a Python package.
# It helps Python recognize the project structure and makes it
# easier to install, import, and use the modules across the project.
# This is useful for maintaining a clean, production-oriented ML project structure.


from setuptools import find_packages,setup

def get_requirements() -> list[str]:
    """ This will return list of requirements   """

    requirement_lst:list[str]=[]

    try:
        with open ("requirements.txt","r") as file:
            lines=file.readlines()
            for line in lines:
                requirement=line.strip()
                if requirement and requirement!="-e .":  #check if requirements is not empty and not equal to -e.
                    requirement_lst.append(requirement)
    except FileNotFoundError:
        print("requirements.txt file not found")

    return requirement_lst



setup   (
    name="networkSecurity",
    version = "0.0.1",
    author = "Sidd",
    author_email = "ksiddartha16@gmail.com",
    packages = find_packages(),
    install_requires = get_requirements()
)
