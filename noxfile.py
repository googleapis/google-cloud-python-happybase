import nox


@nox.session(python='2.7')
def cover(session):
    session.install('pytest', 'mock', 'coverage', 'pytest-cov')
    session.install('.')
    session.run('py.test', '--quiet', '--cov=google.cloud.happybase', '--cov=unit_tests', '--cov-config', '.coveragerc', 'unit_tests')

@nox.session(python='2.7')
def coveralls(session):
    session.install('pytest', 'mock', 'coverage', 'pytest-cov', 'coveralls')
    session.install('.')
    session.run('py.test', '--quiet', '--cov=google.cloud.happybase', '--cov=unit_tests', '--cov-config', '.coveragerc', 'unit_tests')
    session.run('coveralls')

@nox.session(python='2.7')
def docs(session):
    session.install('pytest', 'mock', 'Sphinx', 'sphinx_rtd_theme')
    session.install('.')
    session.run('python', '-c', "import shutil; shutil.rmtree('docs/_build', ignore_errors=True)")
    session.run('sphinx-build', '-W', '-b', 'html', '-d', 'docs/_build/doctrees', 'docs', 'docs/_build/html')
    session.run('python', 'scripts/verify_included_modules.py', '--build-root', '_build')

@nox.session(python='2.7')
def lint(session):
    session.install('pytest', 'mock', 'pycodestyle', 'pylint >= 1.6.4')
    session.install('.')
    session.run('python', 'scripts/pycodestyle_on_repo.py')
    session.run('python', 'scripts/run_pylint.py')

@nox.session(python='2.7')
def py27(session):
    session.install('pytest', 'mock')
    session.install('.')
    session.run('py.test', '--quiet', 'unit_tests')

@nox.session(python='3.4')
def py34(session):
    session.install('pytest', 'mock')
    session.install('.')
    session.run('py.test', '--quiet', 'unit_tests')

@nox.session(python='3.5')
def py35(session):
    session.install('pytest', 'mock')
    session.install('.')
    session.run('py.test', '--quiet', 'unit_tests')

@nox.session(python='2.7')
def system_tests(session):
    session.install('pytest', 'mock')
    session.install('.')
    session.run('python', 'system_tests/attempt_system_tests.py')

@nox.session(python='3.4')
def system_tests3(session):
    session.install('pytest', 'mock')
    session.install('.')
    session.run('python', 'system_tests/attempt_system_tests.py')
