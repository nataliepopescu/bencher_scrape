# String Interner

| Continuous Integration |     Test Coverage    |  Documentation   |       Crates.io      |
|:----------------------:|:--------------------:|:----------------:|:--------------------:|
| [![travisCI][1]][2]    | [![codecov][5]][6]   | [![docs][9]][10] | [![crates][11]][12]  |

A data structure to cache strings efficiently, with minimal memory footprint and the ability to assicate
the interned strings with unique symbols.
These symbols allow for constant time comparisons and look-ups to the underlying interned string contents.
Also, iterating through the interned strings is cache efficient.

## License

Licensed under either of

 * Apache license, Version 2.0, ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)
 * MIT license ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)

at your option.

### Dual licence: [![badge][license-mit-badge]](LICENSE-MIT) [![badge][license-apache-badge]](LICENSE-APACHE)

### Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the Apache-2.0 license, shall be dual licensed as above, without any
additional terms or conditions.

[1]: https://github.com/Robbepop/string-interner/workflows/Rust%20-%20Continuous%20Integration/badge.svg?branch=master
[2]: https://github.com/Robbepop/string-interner/actions?query=workflow%3A%22Rust+-+Continuous+Integration%22+branch%3Amaster
[5]:  https://codecov.io/gh/robbepop/string-interner/branch/master/graph/badge.svg
[6]:  https://codecov.io/gh/Robbepop/string-interner/branch/master
[9]:  https://docs.rs/string-interner/badge.svg
[10]: https://docs.rs/string-interner
[11]: https://img.shields.io/crates/v/string-interner.svg
[12]: https://crates.io/crates/string-interner

[license-mit-badge]: https://img.shields.io/badge/license-MIT-blue.svg
[license-apache-badge]: https://img.shields.io/badge/license-APACHE-orange.svg
