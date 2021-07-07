mod dvec2_impl_scalar;
mod dvec3_impl_scalar;
mod dvec4_impl_scalar;

mod ivec2_impl_scalar;
mod ivec3_impl_scalar;
mod ivec4_impl_scalar;

mod uvec2_impl_scalar;
mod uvec3_impl_scalar;
mod uvec4_impl_scalar;

mod vec2_impl_scalar;
mod vec3_impl_scalar;
#[cfg(any(not(target_feature = "sse2"), feature = "scalar-math"))]
mod vec3a_impl_scalar;
#[cfg(all(target_feature = "sse2", not(feature = "scalar-math")))]
mod vec3a_impl_sse2;
#[cfg(any(not(target_feature = "sse2"), feature = "scalar-math"))]
mod vec4_impl_scalar;
#[cfg(all(target_feature = "sse2", not(feature = "scalar-math")))]
mod vec4_impl_sse2;
mod vec_traits;

pub use vec_traits::*;
