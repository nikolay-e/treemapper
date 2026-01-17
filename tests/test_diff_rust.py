import pytest

from tests.utils import DiffTestCase, DiffTestRunner


@pytest.fixture
def diff_test_runner(tmp_path):
    return DiffTestRunner(tmp_path)


BASIC_RUST_CASES = [
    DiffTestCase(
        name="rust_001_basic_function",
        initial_files={
            "src/lib.rs": """pub fn greet(name: &str) -> String {
    format!("Hello, {}!", name)
}
""",
        },
        changed_files={
            "src/lib.rs": """pub fn greet(name: &str) -> String {
    format!("Hello, {}!", name)
}

pub fn farewell(name: &str) -> String {
    format!("Goodbye, {}!", name)
}
""",
        },
        must_include=["farewell", "Goodbye"],
        must_not_include=["garbage_marker_12345"],
        commit_message="Add farewell function",
    ),
    DiffTestCase(
        name="rust_002_function_signature_change",
        initial_files={
            "src/math.rs": """pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
""",
            "src/main.rs": """mod math;

fn main() {
    let result = math::add(2, 3);
    println!("Result: {}", result);
}
""",
        },
        changed_files={
            "src/math.rs": """pub fn add(a: i64, b: i64) -> i64 {
    a + b
}

pub fn subtract(a: i64, b: i64) -> i64 {
    a - b
}
""",
        },
        must_include=["add", "i64", "subtract"],
        must_not_include=["garbage_unused_symbol"],
        commit_message="Change add signature and add subtract",
    ),
    DiffTestCase(
        name="rust_003_basic_struct",
        initial_files={
            "src/models.rs": """pub struct Point {
    pub x: f64,
    pub y: f64,
}
""",
        },
        changed_files={
            "src/models.rs": """pub struct Point {
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

pub struct Rectangle {
    pub width: f64,
    pub height: f64,
}
""",
        },
        must_include=["Point", "z", "Rectangle"],
        must_not_include=["garbage_struct_field"],
        commit_message="Add z coordinate and Rectangle struct",
    ),
    DiffTestCase(
        name="rust_004_struct_with_methods",
        initial_files={
            "src/counter.rs": """pub struct Counter {
    value: i32,
}

impl Counter {
    pub fn new() -> Self {
        Self { value: 0 }
    }
}
""",
        },
        changed_files={
            "src/counter.rs": """pub struct Counter {
    value: i32,
}

impl Counter {
    pub fn new() -> Self {
        Self { value: 0 }
    }

    pub fn increment(&mut self) {
        self.value += 1;
    }

    pub fn get(&self) -> i32 {
        self.value
    }
}
""",
        },
        must_include=["Counter", "increment", "get"],
        must_not_include=["garbage_method_name"],
        commit_message="Add increment and get methods",
    ),
    DiffTestCase(
        name="rust_005_impl_block",
        initial_files={
            "src/circle.rs": """pub struct Circle {
    pub radius: f64,
}
""",
        },
        changed_files={
            "src/circle.rs": """pub struct Circle {
    pub radius: f64,
}

impl Circle {
    pub fn new(radius: f64) -> Self {
        Self { radius }
    }

    pub fn area(&self) -> f64 {
        std::f64::consts::PI * self.radius * self.radius
    }

    pub fn circumference(&self) -> f64 {
        2.0 * std::f64::consts::PI * self.radius
    }
}
""",
        },
        must_include=["Circle", "area", "circumference", "PI"],
        must_not_include=["garbage_circle_method"],
        commit_message="Add Circle impl block",
    ),
    DiffTestCase(
        name="rust_006_basic_use_statement",
        initial_files={
            "src/main.rs": """fn main() {
    let map = std::collections::HashMap::new();
    println!("{:?}", map);
}
""",
        },
        changed_files={
            "src/main.rs": """use std::collections::HashMap;
use std::collections::HashSet;

fn main() {
    let map: HashMap<String, i32> = HashMap::new();
    let set: HashSet<i32> = HashSet::new();
    println!("{:?} {:?}", map, set);
}
""",
        },
        must_include=["HashMap", "HashSet", "use std::collections"],
        must_not_include=["garbage_import_12345"],
        commit_message="Add explicit use statements",
    ),
    DiffTestCase(
        name="rust_007_module_use",
        initial_files={
            "src/lib.rs": """pub mod utils;
""",
            "src/utils.rs": """pub fn helper() -> String {
    "helper".to_string()
}
""",
        },
        changed_files={
            "src/lib.rs": """pub mod utils;

pub use utils::helper;
pub use utils::processor;
""",
            "src/utils.rs": """pub fn helper() -> String {
    "helper".to_string()
}

pub fn processor(data: &str) -> String {
    data.to_uppercase()
}
""",
        },
        must_include=["processor", "pub use utils"],
        must_not_include=["garbage_module_item"],
        commit_message="Add processor and re-exports",
    ),
    DiffTestCase(
        name="rust_008_basic_trait_definition",
        initial_files={
            "src/traits.rs": """pub trait Named {
    fn name(&self) -> &str;
}
""",
        },
        changed_files={
            "src/traits.rs": """pub trait Named {
    fn name(&self) -> &str;
}

pub trait Describable {
    fn describe(&self) -> String;

    fn short_description(&self) -> String {
        self.describe().chars().take(50).collect()
    }
}
""",
        },
        must_include=["Describable", "describe", "short_description"],
        must_not_include=["garbage_trait_method"],
        commit_message="Add Describable trait",
    ),
    DiffTestCase(
        name="rust_009_trait_impl",
        initial_files={
            "src/animal.rs": """pub trait Animal {
    fn speak(&self) -> String;
}

pub struct Dog {
    pub name: String,
}
""",
        },
        changed_files={
            "src/animal.rs": """pub trait Animal {
    fn speak(&self) -> String;
}

pub struct Dog {
    pub name: String,
}

impl Animal for Dog {
    fn speak(&self) -> String {
        format!("{} says woof!", self.name)
    }
}

pub struct Cat {
    pub name: String,
}

impl Animal for Cat {
    fn speak(&self) -> String {
        format!("{} says meow!", self.name)
    }
}
""",
        },
        must_include=["impl Animal for Dog", "Cat", "meow"],
        must_not_include=["garbage_animal_type"],
        commit_message="Add Animal impls for Dog and Cat",
    ),
    DiffTestCase(
        name="rust_010_enum_definition",
        initial_files={
            "src/status.rs": """pub enum Status {
    Active,
    Inactive,
}
""",
        },
        changed_files={
            "src/status.rs": """pub enum Status {
    Active,
    Inactive,
    Pending,
    Error(String),
}

impl Status {
    pub fn is_active(&self) -> bool {
        matches!(self, Status::Active)
    }
}
""",
        },
        must_include=["Pending", "Error", "is_active"],
        must_not_include=["garbage_enum_variant"],
        commit_message="Add Pending and Error variants",
    ),
    DiffTestCase(
        name="rust_011_generic_struct",
        initial_files={
            "src/container.rs": """pub struct Box<T> {
    value: T,
}
""",
        },
        changed_files={
            "src/container.rs": """pub struct Box<T> {
    value: T,
}

impl<T> Box<T> {
    pub fn new(value: T) -> Self {
        Self { value }
    }

    pub fn get(&self) -> &T {
        &self.value
    }

    pub fn into_inner(self) -> T {
        self.value
    }
}
""",
        },
        must_include=["Box<T>", "into_inner", "get"],
        must_not_include=["garbage_generic_method"],
        commit_message="Add Box impl block",
    ),
    DiffTestCase(
        name="rust_012_generic_function",
        initial_files={
            "src/utils.rs": """pub fn identity(x: i32) -> i32 {
    x
}
""",
        },
        changed_files={
            "src/utils.rs": """pub fn identity<T>(x: T) -> T {
    x
}

pub fn swap<T>(a: T, b: T) -> (T, T) {
    (b, a)
}

pub fn compare<T: PartialOrd>(a: &T, b: &T) -> std::cmp::Ordering {
    a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal)
}
""",
        },
        must_include=["identity<T>", "swap", "compare", "PartialOrd"],
        must_not_include=["garbage_generic_fn"],
        commit_message="Make functions generic",
    ),
    DiffTestCase(
        name="rust_013_result_error_handling",
        initial_files={
            "src/parser.rs": """pub fn parse(s: &str) -> i32 {
    s.parse().unwrap()
}
""",
        },
        changed_files={
            "src/parser.rs": """use std::num::ParseIntError;

pub fn parse(s: &str) -> Result<i32, ParseIntError> {
    s.parse()
}

pub fn parse_or_default(s: &str, default: i32) -> i32 {
    parse(s).unwrap_or(default)
}
""",
        },
        must_include=["Result", "ParseIntError", "parse_or_default"],
        must_not_include=["garbage_error_handler"],
        commit_message="Add proper error handling",
    ),
    DiffTestCase(
        name="rust_014_option_handling",
        initial_files={
            "src/finder.rs": """pub fn find_first(items: &[i32], target: i32) -> i32 {
    for item in items {
        if *item == target {
            return *item;
        }
    }
    -1
}
""",
        },
        changed_files={
            "src/finder.rs": """pub fn find_first(items: &[i32], target: i32) -> Option<i32> {
    items.iter().find(|&&x| x == target).copied()
}

pub fn find_index(items: &[i32], target: i32) -> Option<usize> {
    items.iter().position(|&x| x == target)
}

pub fn find_or_default(items: &[i32], target: i32, default: i32) -> i32 {
    find_first(items, target).unwrap_or(default)
}
""",
        },
        must_include=["Option<i32>", "find_index", "find_or_default"],
        must_not_include=["garbage_option_fn"],
        commit_message="Return Option instead of sentinel values",
    ),
    DiffTestCase(
        name="rust_015_const_and_static",
        initial_files={
            "src/config.rs": """pub const MAX_SIZE: usize = 100;
""",
        },
        changed_files={
            "src/config.rs": """pub const MAX_SIZE: usize = 100;
pub const MIN_SIZE: usize = 10;
pub const DEFAULT_NAME: &str = "unnamed";

pub static mut COUNTER: i32 = 0;

pub fn get_default_config() -> Config {
    Config {
        name: DEFAULT_NAME.to_string(),
        size: MAX_SIZE,
    }
}

pub struct Config {
    pub name: String,
    pub size: usize,
}
""",
        },
        must_include=["MIN_SIZE", "DEFAULT_NAME", "COUNTER", "Config"],
        must_not_include=["garbage_const_name"],
        commit_message="Add constants and Config struct",
    ),
]


ADVANCED_RUST_CASES = [
    DiffTestCase(
        name="rust_016_use_crate_module",
        initial_files={
            "src/utils.rs": """pub fn format_string(s: &str) -> String {
    format!("[{}]", s)
}
""",
            "src/main.rs": """mod utils;

use crate::utils::format_string;

fn main() {
    let result = format_string("hello");
    println!("{}", result);
}
""",
        },
        changed_files={
            "src/utils.rs": """pub fn format_string(s: &str) -> String {
    format!("[[{}]]", s)
}

pub fn trim_string(s: &str) -> &str {
    s.trim()
}
""",
        },
        must_include=["format_string", "trim_string"],
        must_not_include=["garbage_unused_symbol"],
        commit_message="Update format_string and add trim_string",
    ),
    DiffTestCase(
        name="rust_017_impl_trait_for_type",
        initial_files={
            "src/traits.rs": """pub trait Drawable {
    fn draw(&self);
}
""",
            "src/shapes.rs": """use crate::traits::Drawable;

pub struct Circle {
    pub radius: f64,
}

impl Drawable for Circle {
    fn draw(&self) {
        println!("Drawing circle with radius {}", self.radius);
    }
}
""",
        },
        changed_files={
            "src/traits.rs": """pub trait Drawable {
    fn draw(&self);
    fn area(&self) -> f64;
}
""",
        },
        must_include=["Drawable", "area"],
        must_not_include=["garbage_trait_method"],
        commit_message="Add area method to Drawable trait",
    ),
    DiffTestCase(
        name="rust_018_derive_macro",
        initial_files={
            "src/models.rs": """#[derive(Debug, Clone)]
pub struct User {
    pub id: u64,
    pub name: String,
}

impl User {
    pub fn new(id: u64, name: String) -> Self {
        Self { id, name }
    }
}
""",
        },
        changed_files={
            "src/models.rs": """#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct User {
    pub id: u64,
    pub name: String,
    pub email: String,
}

impl User {
    pub fn new(id: u64, name: String, email: String) -> Self {
        Self { id, name, email }
    }
}
""",
        },
        must_include=["User", "email", "PartialEq"],
        must_not_include=["garbage_field_name"],
        commit_message="Add email field and more derives",
    ),
    DiffTestCase(
        name="rust_019_mod_rs_reexports",
        initial_files={
            "src/lib/mod.rs": """mod utils;
mod helpers;

pub use utils::format;
pub use helpers::process;
""",
            "src/lib/utils.rs": """pub fn format(s: &str) -> String {
    s.to_uppercase()
}
""",
            "src/lib/helpers.rs": """pub fn process(data: &[u8]) -> Vec<u8> {
    data.to_vec()
}
""",
        },
        changed_files={
            "src/lib/utils.rs": """pub fn format(s: &str) -> String {
    s.to_uppercase()
}

pub fn format_lower(s: &str) -> String {
    s.to_lowercase()
}
""",
        },
        must_include=["format_lower", "to_lowercase"],
        must_not_include=["garbage_format_function"],
        commit_message="Add format_lower function",
    ),
    DiffTestCase(
        name="rust_020_cargo_features",
        initial_files={
            "Cargo.toml": """[package]
name = "myapp"
version = "0.1.0"
edition = "2021"

[features]
default = []
async = ["tokio"]

[dependencies]
tokio = { version = "1", optional = true }
""",
            "src/lib.rs": """#[cfg(feature = "async")]
pub mod async_utils {
    pub async fn fetch() -> String {
        "data".to_string()
    }
}

pub fn sync_fetch() -> String {
    "sync data".to_string()
}
""",
        },
        changed_files={
            "Cargo.toml": """[package]
name = "myapp"
version = "0.1.0"
edition = "2021"

[features]
default = []
async = ["tokio"]
serde = ["dep:serde"]

[dependencies]
tokio = { version = "1", optional = true }
serde = { version = "1", optional = true, features = ["derive"] }
""",
        },
        must_include=["serde", "features"],
        must_not_include=["garbage_dependency"],
        commit_message="Add serde feature",
    ),
    DiffTestCase(
        name="rust_021_cfg_feature",
        initial_files={
            "src/config.rs": """#[cfg(feature = "json")]
use serde_json;

pub struct Config {
    pub name: String,
}

#[cfg(feature = "json")]
impl Config {
    pub fn from_json(s: &str) -> Self {
        serde_json::from_str(s).unwrap()
    }
}
""",
        },
        changed_files={
            "src/config.rs": """#[cfg(feature = "json")]
use serde_json;

#[cfg(feature = "yaml")]
use serde_yaml;

pub struct Config {
    pub name: String,
    pub version: String,
}

#[cfg(feature = "json")]
impl Config {
    pub fn from_json(s: &str) -> Self {
        serde_json::from_str(s).unwrap()
    }
}

#[cfg(feature = "yaml")]
impl Config {
    pub fn from_yaml(s: &str) -> Self {
        serde_yaml::from_str(s).unwrap()
    }
}
""",
        },
        must_include=["from_yaml", "serde_yaml", "version"],
        must_not_include=["garbage_config_method"],
        commit_message="Add yaml feature support",
    ),
    DiffTestCase(
        name="rust_022_unsafe_ffi",
        initial_files={
            "src/ffi.rs": """extern "C" {
    fn external_function(x: i32) -> i32;
}

pub fn safe_wrapper(x: i32) -> i32 {
    unsafe { external_function(x) }
}
""",
        },
        changed_files={
            "src/ffi.rs": """extern "C" {
    fn external_function(x: i32) -> i32;
    fn another_external(s: *const u8, len: usize) -> i32;
}

pub fn safe_wrapper(x: i32) -> i32 {
    unsafe { external_function(x) }
}

pub fn safe_string_wrapper(s: &str) -> i32 {
    unsafe { another_external(s.as_ptr(), s.len()) }
}
""",
        },
        must_include=["another_external", "safe_string_wrapper"],
        must_not_include=["garbage_ffi_function"],
        commit_message="Add another FFI function",
    ),
    DiffTestCase(
        name="rust_023_macro_rules",
        initial_files={
            "src/macros.rs": """#[macro_export]
macro_rules! vec_of_strings {
    ($($x:expr),*) => {
        vec![$($x.to_string()),*]
    };
}
""",
            "src/main.rs": """mod macros;

fn main() {
    let v = vec_of_strings!["a", "b", "c"];
    println!("{:?}", v);
}
""",
        },
        changed_files={
            "src/macros.rs": """#[macro_export]
macro_rules! vec_of_strings {
    ($($x:expr),*) => {
        vec![$($x.to_string()),*]
    };
}

#[macro_export]
macro_rules! hashmap {
    ($($key:expr => $value:expr),*) => {{
        let mut map = std::collections::HashMap::new();
        $(map.insert($key, $value);)*
        map
    }};
}
""",
        },
        must_include=["hashmap", "HashMap"],
        must_not_include=["garbage_macro_name"],
        commit_message="Add hashmap macro",
    ),
    DiffTestCase(
        name="rust_024_async_await",
        initial_files={
            "src/async_service.rs": """pub async fn fetch_data(url: &str) -> Result<String, Error> {
    let response = reqwest::get(url).await?;
    response.text().await
}

pub struct Error;
""",
            "src/main.rs": """mod async_service;

#[tokio::main]
async fn main() {
    let data = async_service::fetch_data("http://example.com").await;
    println!("{:?}", data);
}
""",
        },
        changed_files={
            "src/async_service.rs": """use std::time::Duration;

pub async fn fetch_data(url: &str) -> Result<String, Error> {
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(30))
        .build()?;
    let response = client.get(url).send().await?;
    response.text().await
}

pub async fn fetch_with_retry(url: &str, retries: u32) -> Result<String, Error> {
    for _ in 0..retries {
        if let Ok(data) = fetch_data(url).await {
            return Ok(data);
        }
    }
    Err(Error)
}

pub struct Error;
""",
        },
        must_include=["fetch_with_retry", "timeout", "Duration"],
        must_not_include=["garbage_async_function"],
        commit_message="Add fetch_with_retry and timeout",
    ),
    DiffTestCase(
        name="rust_025_question_mark_operator",
        initial_files={
            "src/errors.rs": """use std::fmt;

#[derive(Debug)]
pub enum AppError {
    IoError(std::io::Error),
    ParseError(String),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            AppError::IoError(e) => write!(f, "IO error: {}", e),
            AppError::ParseError(s) => write!(f, "Parse error: {}", s),
        }
    }
}

impl std::error::Error for AppError {}
""",
            "src/parser.rs": """use crate::errors::AppError;
use std::fs;

pub fn parse_file(path: &str) -> Result<String, AppError> {
    let content = fs::read_to_string(path).map_err(AppError::IoError)?;
    Ok(content)
}
""",
        },
        changed_files={
            "src/errors.rs": """use std::fmt;

#[derive(Debug)]
pub enum AppError {
    IoError(std::io::Error),
    ParseError(String),
    NetworkError(String),
    ValidationError { field: String, message: String },
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            AppError::IoError(e) => write!(f, "IO error: {}", e),
            AppError::ParseError(s) => write!(f, "Parse error: {}", s),
            AppError::NetworkError(s) => write!(f, "Network error: {}", s),
            AppError::ValidationError { field, message } => {
                write!(f, "Validation error in {}: {}", field, message)
            }
        }
    }
}

impl std::error::Error for AppError {}
""",
        },
        must_include=["NetworkError", "ValidationError"],
        must_not_include=["garbage_error_variant"],
        commit_message="Add NetworkError and ValidationError variants",
    ),
    DiffTestCase(
        name="rust_026_box_dyn_trait",
        initial_files={
            "src/plugin.rs": """pub trait Plugin {
    fn name(&self) -> &str;
    fn execute(&self);
}

pub struct PluginManager {
    plugins: Vec<Box<dyn Plugin>>,
}

impl PluginManager {
    pub fn new() -> Self {
        Self { plugins: vec![] }
    }

    pub fn register(&mut self, plugin: Box<dyn Plugin>) {
        self.plugins.push(plugin);
    }
}
""",
        },
        changed_files={
            "src/plugin.rs": """pub trait Plugin: Send + Sync {
    fn name(&self) -> &str;
    fn execute(&self);
    fn priority(&self) -> i32 { 0 }
}

pub struct PluginManager {
    plugins: Vec<Box<dyn Plugin>>,
}

impl PluginManager {
    pub fn new() -> Self {
        Self { plugins: vec![] }
    }

    pub fn register(&mut self, plugin: Box<dyn Plugin>) {
        self.plugins.push(plugin);
        self.plugins.sort_by_key(|p| -p.priority());
    }

    pub fn execute_all(&self) {
        for plugin in &self.plugins {
            plugin.execute();
        }
    }
}
""",
        },
        must_include=["priority", "execute_all", "Send + Sync"],
        must_not_include=["garbage_plugin_method"],
        commit_message="Add priority and execute_all",
    ),
    DiffTestCase(
        name="rust_027_arc_mutex",
        initial_files={
            "src/shared_state.rs": """use std::sync::{Arc, Mutex};

pub struct Counter {
    value: Arc<Mutex<i32>>,
}

impl Counter {
    pub fn new() -> Self {
        Self {
            value: Arc::new(Mutex::new(0)),
        }
    }

    pub fn increment(&self) {
        let mut val = self.value.lock().unwrap();
        *val += 1;
    }
}
""",
        },
        changed_files={
            "src/shared_state.rs": """use std::sync::{Arc, Mutex, RwLock};

pub struct Counter {
    value: Arc<Mutex<i32>>,
    history: Arc<RwLock<Vec<i32>>>,
}

impl Counter {
    pub fn new() -> Self {
        Self {
            value: Arc::new(Mutex::new(0)),
            history: Arc::new(RwLock::new(vec![])),
        }
    }

    pub fn increment(&self) {
        let mut val = self.value.lock().unwrap();
        *val += 1;
        let mut history = self.history.write().unwrap();
        history.push(*val);
    }

    pub fn get_history(&self) -> Vec<i32> {
        self.history.read().unwrap().clone()
    }
}
""",
        },
        must_include=["RwLock", "history", "get_history"],
        must_not_include=["garbage_concurrency_field"],
        commit_message="Add history tracking with RwLock",
    ),
    DiffTestCase(
        name="rust_028_build_rs",
        initial_files={
            "build.rs": """fn main() {
    println!("cargo:rerun-if-changed=proto/");
    tonic_build::compile_protos("proto/service.proto").unwrap();
}
""",
            "src/service.rs": """pub mod proto {
    tonic::include_proto!("service");
}

pub use proto::service_server::Service;
""",
        },
        changed_files={
            "build.rs": """fn main() {
    println!("cargo:rerun-if-changed=proto/");

    tonic_build::configure()
        .build_server(true)
        .build_client(true)
        .compile(&["proto/service.proto", "proto/types.proto"], &["proto/"])
        .unwrap();
}
""",
        },
        must_include=["build_client", "types.proto", "configure"],
        must_not_include=["garbage_build_option"],
        commit_message="Add types.proto and client generation",
    ),
    DiffTestCase(
        name="rust_029_proc_macro",
        initial_files={
            "derive_macro/src/lib.rs": """use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

#[proc_macro_derive(MyTrait)]
pub fn my_trait_derive(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = input.ident;

    let expanded = quote! {
        impl MyTrait for #name {
            fn name(&self) -> &str {
                stringify!(#name)
            }
        }
    };

    TokenStream::from(expanded)
}
""",
            "src/main.rs": """use derive_macro::MyTrait;

#[derive(MyTrait)]
struct MyStruct {
    value: i32,
}

fn main() {
    let s = MyStruct { value: 42 };
    println!("{}", s.name());
}
""",
        },
        changed_files={
            "derive_macro/src/lib.rs": """use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput, Data, Fields};

#[proc_macro_derive(MyTrait, attributes(my_attr))]
pub fn my_trait_derive(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = input.ident;

    let field_count = match input.data {
        Data::Struct(ref data) => match data.fields {
            Fields::Named(ref fields) => fields.named.len(),
            Fields::Unnamed(ref fields) => fields.unnamed.len(),
            Fields::Unit => 0,
        },
        _ => 0,
    };

    let expanded = quote! {
        impl MyTrait for #name {
            fn name(&self) -> &str {
                stringify!(#name)
            }

            fn field_count(&self) -> usize {
                #field_count
            }
        }
    };

    TokenStream::from(expanded)
}
""",
        },
        must_include=["field_count", "Fields", "Data::Struct"],
        must_not_include=["garbage_proc_macro_fn"],
        commit_message="Add field_count method to derive macro",
    ),
    DiffTestCase(
        name="rust_030_include_str",
        initial_files={
            "data/config.json": """{"name": "app", "version": "1.0"}
""",
            "src/config.rs": """const CONFIG_JSON: &str = include_str!("../data/config.json");

pub fn get_config() -> serde_json::Value {
    serde_json::from_str(CONFIG_JSON).unwrap()
}
""",
        },
        changed_files={
            "data/config.json": """{"name": "app", "version": "2.0", "features": ["auth", "api"]}
""",
        },
        must_include=["features", "auth", "api"],
        must_not_include=["garbage_config_key"],
        commit_message="Update config with features",
    ),
]


OWNERSHIP_RUST_CASES = [
    DiffTestCase(
        name="rust_031_mutable_borrow",
        initial_files={
            "src/data.rs": """pub struct Data {
    values: Vec<i32>,
}

impl Data {
    pub fn new() -> Self {
        Self { values: Vec::new() }
    }

    pub fn add(&mut self, value: i32) {
        self.values.push(value);
    }

    pub fn get(&self, index: usize) -> Option<&i32> {
        self.values.get(index)
    }
}
""",
            "src/processor.rs": """use crate::data::Data;

pub fn process(data: &Data) {
    if let Some(val) = data.get(0) {
        println!("First value: {}", val);
    }
}
""",
        },
        changed_files={
            "src/processor.rs": """use crate::data::Data;

pub fn process(data: &mut Data) {
    data.add(42);
    if let Some(val) = data.get(0) {
        println!("First value: {}", val);
    }
}

pub fn process_multiple(data: &mut Data, count: usize) {
    for i in 0..count {
        data.add(i as i32);
    }
}
""",
        },
        must_include=["process_multiple", "&mut Data"],
        must_not_include=["garbage_processor_fn"],
        commit_message="Change to mutable borrow",
    ),
    DiffTestCase(
        name="rust_032_move_semantics",
        initial_files={
            "src/resource.rs": """pub struct Resource {
    data: String,
}

impl Resource {
    pub fn new(data: String) -> Self {
        Self { data }
    }

    pub fn consume(self) -> String {
        self.data
    }
}
""",
            "src/handler.rs": """use crate::resource::Resource;

pub fn handle(resource: Resource) {
    let data = resource.consume();
    println!("Handled: {}", data);
}
""",
        },
        changed_files={
            "src/handler.rs": """use crate::resource::Resource;

pub fn handle(resource: Resource) {
    let data = resource.consume();
    println!("Handled: {}", data);
}

pub fn transfer_ownership(resource: Resource) -> Resource {
    println!("Transferring: {}", resource.data);
    resource
}

pub fn take_and_return(mut resource: Resource) -> Resource {
    resource.data.push_str("_processed");
    resource
}
""",
        },
        must_include=["transfer_ownership", "take_and_return", "_processed"],
        must_not_include=["garbage_ownership_fn"],
        commit_message="Add ownership transfer functions",
    ),
    DiffTestCase(
        name="rust_033_clone_trait",
        initial_files={
            "src/entity.rs": """#[derive(Debug)]
pub struct Entity {
    id: u64,
    name: String,
}

impl Entity {
    pub fn new(id: u64, name: String) -> Self {
        Self { id, name }
    }
}
""",
        },
        changed_files={
            "src/entity.rs": """#[derive(Debug, Clone)]
pub struct Entity {
    id: u64,
    name: String,
}

impl Entity {
    pub fn new(id: u64, name: String) -> Self {
        Self { id, name }
    }

    pub fn duplicate(&self) -> Self {
        self.clone()
    }
}
""",
            "src/service.rs": """use crate::entity::Entity;

pub fn clone_entities(entities: &[Entity]) -> Vec<Entity> {
    entities.iter().cloned().collect()
}

pub fn process_with_backup(entity: &Entity) -> Entity {
    let backup = entity.clone();
    println!("Processing: {:?}", entity);
    backup
}
""",
        },
        must_include=["Clone", "duplicate", "clone_entities"],
        must_not_include=["garbage_clone_fn"],
        commit_message="Add Clone derive and cloning functions",
    ),
    DiffTestCase(
        name="rust_034_copy_trait",
        initial_files={
            "src/point.rs": """#[derive(Debug)]
pub struct Point {
    x: f64,
    y: f64,
}

impl Point {
    pub fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }

    pub fn distance(&self, other: &Point) -> f64 {
        ((self.x - other.x).powi(2) + (self.y - other.y).powi(2)).sqrt()
    }
}
""",
        },
        changed_files={
            "src/point.rs": """#[derive(Debug, Clone, Copy)]
pub struct Point {
    x: f64,
    y: f64,
}

impl Point {
    pub fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }

    pub fn distance(self, other: Point) -> f64 {
        ((self.x - other.x).powi(2) + (self.y - other.y).powi(2)).sqrt()
    }

    pub fn midpoint(self, other: Point) -> Point {
        Point::new((self.x + other.x) / 2.0, (self.y + other.y) / 2.0)
    }
}
""",
            "src/geometry.rs": """use crate::point::Point;

pub fn calculate_area(p1: Point, p2: Point, p3: Point) -> f64 {
    let a = p1.distance(p2);
    let b = p2.distance(p3);
    let c = p3.distance(p1);
    let s = (a + b + c) / 2.0;
    (s * (s - a) * (s - b) * (s - c)).sqrt()
}
""",
        },
        must_include=["Copy", "midpoint", "calculate_area"],
        must_not_include=["garbage_geometry_fn"],
        commit_message="Add Copy trait and geometry functions",
    ),
]


LIFETIME_RUST_CASES = [
    DiffTestCase(
        name="rust_035_lifetime_annotations",
        initial_files={
            "src/parser.rs": """pub struct Parser {
    input: String,
}

impl Parser {
    pub fn new(input: String) -> Self {
        Self { input }
    }

    pub fn parse(&self) -> Vec<String> {
        self.input.split_whitespace().map(String::from).collect()
    }
}
""",
        },
        changed_files={
            "src/parser.rs": """pub struct Parser<'a> {
    input: &'a str,
}

impl<'a> Parser<'a> {
    pub fn new(input: &'a str) -> Self {
        Self { input }
    }

    pub fn parse(&self) -> Vec<&'a str> {
        self.input.split_whitespace().collect()
    }

    pub fn first_word(&self) -> Option<&'a str> {
        self.input.split_whitespace().next()
    }
}

pub fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
""",
        },
        must_include=["Parser<'a>", "first_word", "longest"],
        must_not_include=["garbage_lifetime_fn"],
        commit_message="Add lifetime annotations",
    ),
    DiffTestCase(
        name="rust_036_static_lifetime",
        initial_files={
            "src/constants.rs": """pub const APP_NAME: &str = "MyApp";
pub const VERSION: &str = "1.0.0";
""",
        },
        changed_files={
            "src/constants.rs": """pub const APP_NAME: &'static str = "MyApp";
pub const VERSION: &'static str = "1.0.0";

pub static GLOBAL_CONFIG: &'static str = "default";

lazy_static::lazy_static! {
    pub static ref RUNTIME_CONFIG: String = {
        std::env::var("CONFIG").unwrap_or_else(|_| "production".to_string())
    };
}
""",
            "src/messages.rs": """use crate::constants::{APP_NAME, VERSION};

pub fn get_greeting() -> &'static str {
    "Welcome to the application"
}

pub fn format_version() -> String {
    format!("{} v{}", APP_NAME, VERSION)
}
""",
        },
        must_include=["GLOBAL_CONFIG", "lazy_static", "get_greeting"],
        must_not_include=["garbage_static_const"],
        commit_message="Add static lifetime annotations",
    ),
]


SMART_POINTER_RUST_CASES = [
    DiffTestCase(
        name="rust_037_arc_rc_shared_ownership",
        initial_files={
            "src/cache.rs": """use std::collections::HashMap;

pub struct Cache {
    data: HashMap<String, String>,
}

impl Cache {
    pub fn new() -> Self {
        Self { data: HashMap::new() }
    }

    pub fn get(&self, key: &str) -> Option<&String> {
        self.data.get(key)
    }
}
""",
        },
        changed_files={
            "src/cache.rs": """use std::collections::HashMap;
use std::sync::{Arc, RwLock};

pub struct Cache {
    data: Arc<RwLock<HashMap<String, String>>>,
}

impl Cache {
    pub fn new() -> Self {
        Self {
            data: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub fn get(&self, key: &str) -> Option<String> {
        self.data.read().unwrap().get(key).cloned()
    }

    pub fn set(&self, key: String, value: String) {
        self.data.write().unwrap().insert(key, value);
    }

    pub fn clone_handle(&self) -> Arc<RwLock<HashMap<String, String>>> {
        Arc::clone(&self.data)
    }
}

impl Clone for Cache {
    fn clone(&self) -> Self {
        Self {
            data: Arc::clone(&self.data),
        }
    }
}
""",
        },
        must_include=["Arc", "RwLock", "clone_handle", "set"],
        must_not_include=["garbage_cache_method"],
        commit_message="Add Arc and RwLock for thread-safe shared ownership",
    ),
    DiffTestCase(
        name="rust_038_refcell_interior_mutability",
        initial_files={
            "src/counter.rs": """pub struct Counter {
    count: u64,
}

impl Counter {
    pub fn new() -> Self {
        Self { count: 0 }
    }

    pub fn increment(&mut self) {
        self.count += 1;
    }

    pub fn get(&self) -> u64 {
        self.count
    }
}
""",
        },
        changed_files={
            "src/counter.rs": """use std::cell::RefCell;

pub struct Counter {
    count: RefCell<u64>,
}

impl Counter {
    pub fn new() -> Self {
        Self { count: RefCell::new(0) }
    }

    pub fn increment(&self) {
        *self.count.borrow_mut() += 1;
    }

    pub fn get(&self) -> u64 {
        *self.count.borrow()
    }

    pub fn reset(&self) {
        *self.count.borrow_mut() = 0;
    }
}
""",
            "src/tracker.rs": """use crate::counter::Counter;
use std::rc::Rc;

pub struct Tracker {
    counters: Vec<Rc<Counter>>,
}

impl Tracker {
    pub fn new() -> Self {
        Self { counters: Vec::new() }
    }

    pub fn add_counter(&mut self) -> Rc<Counter> {
        let counter = Rc::new(Counter::new());
        self.counters.push(Rc::clone(&counter));
        counter
    }

    pub fn total(&self) -> u64 {
        self.counters.iter().map(|c| c.get()).sum()
    }
}
""",
        },
        must_include=["RefCell", "borrow_mut", "Tracker", "Rc"],
        must_not_include=["garbage_refcell_fn"],
        commit_message="Add RefCell for interior mutability",
    ),
    DiffTestCase(
        name="rust_039_deref_trait",
        initial_files={
            "src/wrapper.rs": """pub struct Wrapper<T> {
    value: T,
}

impl<T> Wrapper<T> {
    pub fn new(value: T) -> Self {
        Self { value }
    }

    pub fn into_inner(self) -> T {
        self.value
    }
}
""",
        },
        changed_files={
            "src/wrapper.rs": """use std::ops::{Deref, DerefMut};

pub struct Wrapper<T> {
    value: T,
}

impl<T> Wrapper<T> {
    pub fn new(value: T) -> Self {
        Self { value }
    }

    pub fn into_inner(self) -> T {
        self.value
    }
}

impl<T> Deref for Wrapper<T> {
    type Target = T;

    fn deref(&self) -> &Self::Target {
        &self.value
    }
}

impl<T> DerefMut for Wrapper<T> {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.value
    }
}
""",
            "src/usage.rs": """use crate::wrapper::Wrapper;

pub fn use_wrapper() {
    let wrapped = Wrapper::new(String::from("hello"));
    println!("Length: {}", wrapped.len());
    println!("Upper: {}", wrapped.to_uppercase());
}

pub fn modify_wrapper() {
    let mut wrapped = Wrapper::new(vec![1, 2, 3]);
    wrapped.push(4);
    println!("Items: {:?}", *wrapped);
}
""",
        },
        must_include=["Deref", "DerefMut", "use_wrapper", "modify_wrapper"],
        must_not_include=["garbage_deref_fn"],
        commit_message="Implement Deref and DerefMut traits",
    ),
    DiffTestCase(
        name="rust_040_drop_trait",
        initial_files={
            "src/connection.rs": """pub struct Connection {
    host: String,
    connected: bool,
}

impl Connection {
    pub fn new(host: String) -> Self {
        println!("Connecting to {}", host);
        Self { host, connected: true }
    }

    pub fn disconnect(&mut self) {
        self.connected = false;
    }
}
""",
        },
        changed_files={
            "src/connection.rs": """pub struct Connection {
    host: String,
    connected: bool,
}

impl Connection {
    pub fn new(host: String) -> Self {
        println!("Connecting to {}", host);
        Self { host, connected: true }
    }

    pub fn is_connected(&self) -> bool {
        self.connected
    }
}

impl Drop for Connection {
    fn drop(&mut self) {
        if self.connected {
            println!("Disconnecting from {}", self.host);
            self.connected = false;
        }
    }
}
""",
            "src/pool.rs": """use crate::connection::Connection;

pub struct ConnectionPool {
    connections: Vec<Connection>,
    max_size: usize,
}

impl ConnectionPool {
    pub fn new(max_size: usize) -> Self {
        Self {
            connections: Vec::new(),
            max_size,
        }
    }

    pub fn acquire(&mut self, host: &str) -> Option<&Connection> {
        if self.connections.len() < self.max_size {
            self.connections.push(Connection::new(host.to_string()));
            self.connections.last()
        } else {
            None
        }
    }
}

impl Drop for ConnectionPool {
    fn drop(&mut self) {
        println!("Dropping pool with {} connections", self.connections.len());
    }
}
""",
        },
        must_include=["Drop", "is_connected", "ConnectionPool", "acquire"],
        must_not_include=["garbage_drop_fn"],
        commit_message="Implement Drop trait for cleanup",
    ),
]


ALL_RUST_CASES = BASIC_RUST_CASES + ADVANCED_RUST_CASES + OWNERSHIP_RUST_CASES + LIFETIME_RUST_CASES + SMART_POINTER_RUST_CASES


@pytest.mark.parametrize("case", ALL_RUST_CASES, ids=lambda c: c.name)
def test_rust_cases(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
