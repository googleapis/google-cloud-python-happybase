import nox


@nox.session(python='2.7')
def cover(session):
    session.install('pytest', 'mock', 'coverage', 'pytest-cov')
    session.install('.')
    session.run('py.test', '--quiet', '--cov=google.cloud.happybase', '--cov=unit_tests', '--cov-config', '.coveragerc', 'unit_tests')

@nox.session(python='2.7')
def docs(session):
    session.install('pytest', 'mock', 'Sphinx', 'sphinx_rtd_theme')
    session.install('.')
    session.run('python', '-c', "import shutil; shutil.rmtree('docs/_build', ignore_errors=True)")
    session.run('sphinx-build', '-W', '-b', 'html', '-d', 'docs/_build/doctrees', 'docs', 'docs/_build/html')
    session.run('python', 'scripts/verify_included_modules.py', '--build-root', '_build')

@nox.session(python="3.7")
def lint(session):
    """Run linters.
    Returns a failure if the linters find linting errors or sufficiently
    serious code quality issues.
    """
    session.install("flake8", "black")
    session.run(
        "black",
        "--check",
        "src",
        "docs",
        "unit_tests",
        "system_tests"
    )
    session.run("flake8", "google", "tests")

@nox.session(python='3.6')
def blacken(session):
    session.install("black")
    session.run(
        "black",
        "noxfile.py"
        "src",
        "docs",
        "unit_tests",
        "system_tests",
    )

@nox.session(python=['2.7', '3.4', '3.5', '3.6', '3.7'])
def tests(session):
    session.install('pytest', 'mock')
    session.install('.')
    session.run('py.test', '--quiet', 'unit_tests')

@nox.session(python=['2.7', '3.7'])
def system_tests(session):
    session.install('pytest', 'mock')
    session.install('.')
    session.run('py.test', '--quiet', 'system_tests/happybase.py')
