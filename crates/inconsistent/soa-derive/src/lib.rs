//! This crate provides a custom derive (`#[derive(StructOfArray)]`) to
//! automatically generate code from a given struct `T` that allow to replace
//! `Vec<T>` with a struct of arrays. For example, the following code
//!
//! ```
//! # #[macro_use] extern crate soa_derive;
//! # fn main() {
//! #[derive(StructOfArray)]
//! pub struct Cheese {
//!     pub smell: f64,
//!     pub color: (f64, f64, f64),
//!     pub with_mushrooms: bool,
//!     pub name: String,
//! }
//! # }
//! ```
//!
//! will generate a `CheeseVec` struct that looks like this:
//!
//! ```
//! pub struct CheeseVec {
//!     pub smell: Vec<f64>,
//!     pub color: Vec<(f64, f64, f64)>,
//!     pub with_mushrooms: Vec<bool>,
//!     pub name: Vec<String>,
//! }
//! ```
//!
//! It will also generate the same functions that a `Vec<Chees>` would have, and
//! a few helper structs: `CheeseSlice`, `CheeseSliceMut`, `CheeseRef` and
//! `CheeseRefMut` corresponding respectivly to `&[Cheese]`, `&mut [Cheese]`,
//! `&Cheese` and `&mut Cheese`.
//!
//! # How to use it
//!
//! Add `#[derive(StructOfArray)]` to each struct you want to derive a struct of
//! array version. If you need the helper structs to derive additional traits
//! (such as `Debug` or `PartialEq`), you can add an attribute `#[soa_derive =
//! "Debug, PartialEq"]` to the struct declaration.
//!
//! ```
//! # #[macro_use] extern crate soa_derive;
//! # fn main() {
//! #[derive(Debug, PartialEq, StructOfArray)]
//! #[soa_derive = "Debug, PartialEq"]
//! pub struct Cheese {
//!     pub smell: f64,
//!     pub color: (f64, f64, f64),
//!     pub with_mushrooms: bool,
//!     pub name: String,
//! }
//! # }
//! ```
//!
//! # Usage and API
//!
//! All the generated code have some generated documentation with it, so you
//! should be able to use `cargo doc` on your crate and see the documentation
//! for all the generated structs and functions.
//!
//! Most of the time, you should be able to replace `Vec<Cheese>` by
//! `CheeseVec`, with exception of code using direct indexing in the vector and
//! a few other caveats listed below.
//!
//! ## Caveats and limitations
//!
//! `Vec<T>` functionalities rely a lot on references and automatic *deref*
//! feature, for getting function from `[T]` and indexing. But the SoA vector
//! (let's call it `CheeseVec`, generated from the `Cheese` struct) generated by
//! this crate can not implement `Deref<Target=CheeseSlice>`, because `Deref` is
//! required to return a reference, and `CheeseSlice` is not a reference. The
//! same applies to `Index` and `IndexMut` trait, that can not return
//! `CheeseRef/CheeseRefMut`.
//!
//! This means that the we can not index into a `CheeseVec`, and that a few
//! functions are duplicated, or require a call to `as_ref()/as_mut()` to change
//! the type used.
//!
//! # Iteration
//!
//! It is possible to iterate over the values in a `CheeseVec`
//!
//! ```no_run
//! # #[macro_use] extern crate soa_derive;
//! # fn main() {
//! # #[derive(Debug, PartialEq, StructOfArray)]
//! # pub struct Cheese {
//! #     pub smell: f64,
//! #     pub color: (f64, f64, f64),
//! #     pub with_mushrooms: bool,
//! #     pub name: String,
//! # }
//! # impl Cheese { fn new(name: &str) -> Cheese { unimplemented!() } }
//! let mut vec = CheeseVec::new();
//! vec.push(Cheese::new("stilton"));
//! vec.push(Cheese::new("brie"));
//!
//! for cheese in vec.iter() {
//!     // when iterating over a CheeseVec, we load all members from memory
//!     // in a CheeseRef
//!     let typeof_cheese: CheeseRef = cheese;
//!     println!("this is {}, with a smell power of {}", cheese.name, cheese.smell);
//! }
//! # }
//! ```
//!
//! One of the main advantage of the SoA layout is to be able to only load some
//! fields from memory when iterating over the vector. In order to do so, one
//! can manually pick the needed fields:
//!
//! ```no_run
//! # #[macro_use] extern crate soa_derive;
//! # fn main() {
//! # #[derive(Debug, PartialEq, StructOfArray)]
//! # pub struct Cheese {
//! #     pub smell: f64,
//! #     pub color: (f64, f64, f64),
//! #     pub with_mushrooms: bool,
//! #     pub name: String,
//! # }
//! # impl Cheese { fn new(name: &str) -> Cheese { unimplemented!() } }
//! # let mut vec = CheeseVec::new();
//! # vec.push(Cheese::new("stilton"));
//! # vec.push(Cheese::new("brie"));
//! for name in &vec.name {
//!     // We get referenes to the names
//!     let typeof_name: &String = name;
//!     println!("got cheese {}", name);
//! }
//! # }
//! ```
//!
//! In order to iterate over multiple fields at the same time, one can use the
//! [soa_zip!](macro.soa_zip.html) macro.
//!
//! ```no_run
//! # #[macro_use] extern crate soa_derive;
//! # fn main() {
//! # #[derive(Debug, PartialEq, StructOfArray)]
//! # pub struct Cheese {
//! #     pub smell: f64,
//! #     pub color: (f64, f64, f64),
//! #     pub with_mushrooms: bool,
//! #     pub name: String,
//! # }
//! # impl Cheese { fn new(name: &str) -> Cheese { unimplemented!() } }
//! # let mut vec = CheeseVec::new();
//! # vec.push(Cheese::new("stilton"));
//! # vec.push(Cheese::new("brie"));
//! for (name, smell, color) in soa_zip!(&mut vec, [name, mut smell, color]) {
//!     println!("this is {}, with color {:#?}", name, color);
//!     // smell is a mutable reference
//!     *smell += 1.0;
//! }
//! # }
//! ```

// The proc macro is implemented in soa_derive_internal, and re-exported by this
// crate. This is because a single crate can not define both a proc macro and a
// macro_rules macro.
pub use soa_derive_internal::StructOfArray;

/// Create an iterator over multiple fields in a Struct of array style vector.
///
/// This macro takes two main arguments: the array/slice container, and a list
/// of fields to use, inside square brackets. The iterator will give references
/// to the fields, which can be mutable references if the field name is prefixed
/// with `mut`.
///
/// ```
/// # #[macro_use] extern crate soa_derive;
/// # fn main() {
/// #[derive(StructOfArray)]
/// struct Cheese {
///     size: f64,
///     mass: f64,
///     smell: f64,
///     name: String,
/// }
///
/// let mut vec = CheeseVec::new();
/// // fill the vector
///
/// // Iterate over immutable references
/// for (mass, size, name) in soa_zip!(&vec, [mass, size, name]) {
///     println!("got {} kg and {} cm of {}", mass, size, name);
/// }
///
/// // Iterate over mutable references
/// for (mass, name) in soa_zip!(&mut vec, [mut mass, name]) {
///     println!("got {} kg of {}, eating 1 kg", mass, name);
///     *mass -= 1.0;
/// }
/// # }
/// ```
///
/// The iterator can also work with external iterators. In this case, the
/// iterator will yields elements until any of the fields or one external
/// iterator returns None.
///
/// ```
/// # #[macro_use] extern crate soa_derive;
/// # fn main() {
/// # #[derive(StructOfArray)]
/// # struct Cheese {
/// #     size: f64,
/// #     mass: f64,
/// #     smell: f64,
/// #     name: String,
/// # }
/// # #[derive(Debug)] struct Cellar;
/// let mut vec = CheeseVec::new();
/// let mut cellars = Vec::<Cellar>::new();
///
/// for (name, mass, cellar) in soa_zip!(&vec, [name, mass], &cellars) {
///     println!("we have {} kg of {} in {:#?}", mass, name, cellar);
/// }
/// # }
/// ```
#[macro_export]
macro_rules! soa_zip {
    ($self: expr, [$($fields: tt)*] $(, $external: expr)* $(,)*) => {{
        let this = $self;
        $crate::soa_zip_impl!(@munch this, {$($fields)*} -> [] $($external ,)*)
    }};
}

#[macro_export]
#[doc(hidden)]
macro_rules! soa_zip_impl {
    // @flatten creates a tuple-flattening closure for .map() call
    // Finish recursion
    (@flatten $p:pat => $tup:expr ) => {
        |$p| $tup
    };
    // Eat an element ($_iter) and add it to the current closure. Then recurse
    (@flatten $p:pat => ( $($tup:tt)* ) , $_iter:expr $( , $tail:expr )* ) => {
        $crate::soa_zip_impl!(@flatten ($p, a) => ( $($tup)*, a ) $( , $tail )*)
    };

    // The main code is emmited here: we create an iterator, zip it and then
    // map the zipped iterator to flatten it
    (@last , $first: expr, $($tail: expr,)*) => {
        ::std::iter::IntoIterator::into_iter($first)
            $(
                .zip($tail)
            )*
            .map(
                $crate::soa_zip_impl!(@flatten a => (a) $( , $tail )*)
            )
    };

    // Eat the last `mut $field` and then emit code
    (@munch $self: expr, {mut $field: ident} -> [$($output: tt)*] $($ext: expr ,)*) => {
        $crate::soa_zip_impl!(@last $($output)*, $self.$field.iter_mut(), $($ext, )*)
    };
    // Eat the last `$field` and then emit code
    (@munch $self: expr, {$field: ident} -> [$($output: tt)*] $($ext: expr ,)*) => {
        $crate::soa_zip_impl!(@last $($output)*, $self.$field.iter(), $($ext, )*)
    };

    // Eat the next `mut $field` and then recurse
    (@munch $self: expr, {mut $field: ident, $($tail: tt)*} -> [$($output: tt)*] $($ext: expr ,)*) => {
        $crate::soa_zip_impl!(@munch $self, {$($tail)*} -> [$($output)*, $self.$field.iter_mut()] $($ext, )*)
    };
    // Eat the next `$field` and then recurse
    (@munch $self: expr, {$field: ident, $($tail: tt)*} -> [$($output: tt)*] $($ext: expr ,)*) => {
        $crate::soa_zip_impl!(@munch $self, {$($tail)*} -> [$($output)*, $self.$field.iter()] $($ext, )*)
    };
}
