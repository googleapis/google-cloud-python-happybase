# Changelog

[PyPI History][1]

[1]: https://pypi.org/project/google-cloud-happybase/#history


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
