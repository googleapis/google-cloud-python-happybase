# Changelog

[PyPI History][1]

[1]: https://pypi.org/project/google-cloud-happybase/#history


## 0.32.0

12-17-2018 17:20 PST


### Implementation Changes
- Pool: fix call to `_get_instance`. ([#57](https://github.com/googleapis/google-cloud-python-happybase/pull/57))
- Use `Table.mutate_rows()` rather than `Row.commit()` in `Batch.send()`. ([#54](https://github.com/googleapis/google-cloud-python-happybase/pull/54))
- Remove `instance.copy()` and `timeout` parameter from `Connection` constructor. ([#50](https://github.com/googleapis/google-cloud-python-happybase/pull/50))

### Documentation
- Announce deprecation of Python 2.7 ([#55](https://github.com/googleapis/google-cloud-python-happybase/pull/55))

### Internal / Testing Changes
- Harden system tests. ([#53](https://github.com/googleapis/google-cloud-python-happybase/pull/53))
- Update github issue templates ([#52](https://github.com/googleapis/google-cloud-python-happybase/pull/52))
- Testing cleanups ([#49](https://github.com/googleapis/google-cloud-python-happybase/pull/49))
- Fix version in `setup.py`

## 0.31.0 (2018-10-05)

### Dependencies

- Update to use `google.cloud.bigtable >= 0.31.0`


## 0.30.2 (2018-10-05)

### Dependencies

- Update to use `google.cloud.bigtable 0.30.2`

### Documentation

- Fix incorrect PyPI link in README (#28).

### Implementation changes

- Use Bigtable's `yield_rows` for `Table.rows()` and `Table.scan()`. ([#37](https://github.com/googleapis/google-cloud-python-happybase/pull/37))
- Update scan method to use row set ([#42](https://github.com/googleapis/google-cloud-python-happybase/pull/42))
- Use `row_set` in `rows()` method.  Improves performance for the `rows` method. ([#44](https://github.com/googleapis/google-cloud-python-happybase/pull/44))


## 0.26.0 (2017-08-07)

### Dependencies

- Update to use `google.cloud.bigtable 0.26.0`

### Documentation

- Fix docs URL (#25).


## 0.25.0 (2017-07-19)

### Dependencies

- Update to use `google.cloud.bigtable 0.25.0`


## 0.24.0 (2017-03-31)

### New Features

- Add support for Python 3.6.

### Dependencies

- Update to use `google.cloud.bigtable 0.24.0`


## 0.23.0 (2017-02-24)

### Dependencies

- Update to use `google.cloud.bigtable 0.23.0`


## 0.22.0 (2016-12-10)

### Dependencies

- Update to use `google.cloud.bigtable 0.22.0`


## 0.21.0 (2016-11-22)

### Dependencies

- Update to use `google.cloud.bigtable 0.21.0`


## 0.20.0 (2016-09-29)

### New Features

- Initial release.
