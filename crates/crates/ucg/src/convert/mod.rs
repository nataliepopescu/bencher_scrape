// Copyright 2017 Jeremy Wall <jeremy@marzhillstudios.com>
//
//  Licensed under the Apache License, Version 2.0 (the "License");
//  you may not use this file except in compliance with the License.
//  You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.

//! The conversion stage of the ucg compiler.
pub mod b64;
pub mod env;
pub mod exec;
pub mod flags;
pub mod json;
pub mod toml;
pub mod traits;
pub mod xml;
pub mod yaml;
pub mod yamlmulti;

use std::collections::HashMap;

/// ConverterRunner knows how to run a given converter on a Val.
pub struct ConverterRegistry {
    converters: HashMap<String, Box<dyn traits::Converter>>,
}

impl ConverterRegistry {
    /// Creates a new ConverterRegistry.
    ///
    /// * flags
    /// * json
    /// * env
    /// * exec
    fn new() -> Self {
        ConverterRegistry {
            converters: HashMap::new(),
        }
    }

    pub fn make_registry() -> Self {
        let mut registry = Self::new();
        registry.register("json", Box::new(json::JsonConverter::new()));
        registry.register("env", Box::new(env::EnvConverter::new()));
        registry.register("flags", Box::new(flags::FlagConverter::new()));
        registry.register("exec", Box::new(exec::ExecConverter::new()));
        registry.register("yaml", Box::new(yaml::YamlConverter::new()));
        registry.register("yamlmulti", Box::new(yamlmulti::MultiYamlConverter::new()));
        registry.register("toml", Box::new(toml::TomlConverter::new()));
        registry.register("xml", Box::new(xml::XmlConverter {}));
        registry
    }

    pub fn register<S: Into<String>>(&mut self, typ: S, converter: Box<dyn traits::Converter>) {
        self.converters.insert(typ.into(), converter);
    }

    pub fn get_converter(&self, typ: &str) -> Option<&dyn traits::Converter> {
        self.converters.get(typ).map(|c| c.as_ref())
    }

    pub fn get_converter_list(&self) -> Vec<(&String, &Box<dyn traits::Converter>)> {
        self.converters.iter().collect()
    }
}

pub struct ImporterRegistry {
    importers: HashMap<String, Box<dyn traits::Importer>>,
}

impl ImporterRegistry {
    /// Creates a new ImporterRegistry.
    ///
    /// * b64
    /// * b64urlsafe
    fn new() -> Self {
        ImporterRegistry {
            importers: HashMap::new(),
        }
    }

    pub fn make_registry() -> Self {
        let mut registry = Self::new();
        registry.register("b64", Box::new(b64::Base64Importer { url_safe: false }));
        registry.register(
            "b64urlsafe",
            Box::new(b64::Base64Importer { url_safe: true }),
        );
        registry.register("json", Box::new(json::JsonConverter {}));
        registry.register("yaml", Box::new(yaml::YamlConverter {}));
        registry.register("toml", Box::new(toml::TomlConverter {}));
        registry
    }

    pub fn register<S: Into<String>>(&mut self, typ: S, importer: Box<dyn traits::Importer>) {
        self.importers.insert(typ.into(), importer);
    }

    pub fn get_importer(&self, typ: &str) -> Option<&dyn traits::Importer> {
        self.importers.get(typ).map(|c| c.as_ref())
    }

    pub fn get_importer_list(&self) -> Vec<(&String, &Box<dyn traits::Importer>)> {
        self.importers.iter().collect()
    }
}
