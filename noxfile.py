import nox

BLACK_VERSION = "black==19.10b0"

@nox.session(python="3.6")
def cover(session):
    session.install("pytest", "mock", "coverage", "pytest-cov")
    session.install(".")
    session.run(
        "py.test",
        "--quiet",
        "--cov=google.cloud.happybase",
        "--cov=unit_tests",
        "--cov-config",
        ".coveragerc",
        "unit_tests",
    )


@nox.session(python="3.6")
def docs(session):
    session.install("pytest", "mock", "Sphinx", "sphinx_rtd_theme")
    session.install(".")
    session.run(
        "python",
        "-c",
        "import shutil; shutil.rmtree('docs/_build', ignore_errors=True)",
    )
    session.run(
        "sphinx-build",
        "-W",
        "-b",
        "html",
        "-d",
        "docs/_build/doctrees",
        "docs",
        "docs/_build/html",
    )
    session.run(
        "python", "scripts/verify_included_modules.py", "--build-root", "_build"
    )


# Linting with flake8.
#
# We ignore the following rules:
#   E203: whitespace before ‘:’
#   E266: too many leading ‘#’ for block comment
#   E501: line too long
#   I202: Additional newline in a section of imports
#
# We also need to specify the rules which are ignored by default:
# ['E226', 'W504', 'E126', 'E123', 'W503', 'E24', 'E704', 'E121']
FLAKE8_COMMON_ARGS = [
    "--show-source",
    "--builtin=gettext",
    "--max-complexity=20",
    "--exclude=.nox,.cache,env,lib,generated_pb2,*_pb2.py,*_pb2_grpc.py",
    "--ignore=E121,E123,E126,E203,E226,E24,E266,E501,E704,F401,W503,W504,I202",
    "--max-line-length=88",
]


@nox.session(python="3.7")
def lint(session):
    """Run linters.
    Returns a failure if the linters find linting errors or sufficiently
    serious code quality issues.
    """
    session.install("flake8", BLACK_VERSION)
    session.run("black", "--check", "src", "docs", "unit_tests", "system_tests")
    session.run(
        "flake8", *FLAKE8_COMMON_ARGS, "src/google", "unit_tests", "system_tests"
    )


@nox.session(python="3.6")
def blacken(session):
    session.install(BLACK_VERSION)
    session.run("black", "noxfile.py", "src", "docs", "unit_tests", "system_tests")


@nox.session(python=["3.6", "3.7", "3.8", "3.9"])
def unit(session):
    session.install("pytest", "mock")
    session.install(".")
    session.run("py.test", "--quiet", "unit_tests")


@nox.session(python=["3.7"])
def system(session):
    session.install("pytest", "mock")
    session.install("-e", ".")
    session.run("py.test", "--quiet", "system_tests/test_happybase.py")
